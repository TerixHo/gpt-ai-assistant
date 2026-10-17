"""紅白機（NES／Famicom）風格的音源模擬：兩個脈衝波、一個三角波、一個雜訊，全部用 numpy 合成。

給 generate_music.py（配樂）與 generate_sfx.py（音效）共用。模擬重點：
    1. 脈衝波四種工作週期（12.5%、25%、50%、75%），以 PolyBLEP 消除混疊，聲音乾淨但保留方波的亮度。
    2. 音量 4 位元（0 到 15 階），音量包絡、顫音、琶音以每秒 60 格的「影格」更新，
       這是當年音樂驅動程式的做法，也是紅白機聲音一格一格、有顆粒感的來源。
    3. 三角波是 32 階的階梯三角波，沒有音量控制（只有開或關），用來彈低音和做大鼓。
    4. 雜訊用 15 位元線性回饋移位暫存器（LFSR），16 種週期與「長、短」兩種模式（短模式是金屬聲）。
音高依 NTSC 主機的 CPU 時脈換算成週期暫存器再換回頻率，所以音準有當年那種些微的偏差。
"""
import wave
from pathlib import Path

import numpy as np

TAU = 2 * np.pi
CPU = 1789773.0
FRAME_HZ = 60.0
NOISE_PERIODS = [4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068]
DUTIES = {12: 0.125, 25: 0.25, 50: 0.5, 75: 0.75}


def hz(midi):
    return 440.0 * 2 ** ((np.asarray(midi, dtype=np.float64) - 69) / 12)


def nes_pulse_hz(f):
    """把頻率換成脈衝波週期暫存器（11 位元）再換回頻率。"""
    t = np.clip(np.round(CPU / (16 * np.asarray(f)) - 1), 8, 2047)
    return CPU / (16 * (t + 1))


def nes_tri_hz(f):
    t = np.clip(np.round(CPU / (32 * np.asarray(f)) - 1), 2, 2047)
    return CPU / (32 * (t + 1))


def frames_to_samples(values, n, sr):
    """每影格一個值的陣列展開成每個取樣一個值（保持階梯，不內插）。"""
    values = np.asarray(values, dtype=np.float64)
    idx = np.minimum((np.arange(n) * FRAME_HZ / sr).astype(np.int64), len(values) - 1)
    return values[idx]


def _polyblep(t, dt):
    out = np.zeros_like(t)
    a = t < dt
    x = t[a] / dt[a]
    out[a] = x + x - x * x - 1.0
    b = t > 1.0 - dt
    x = (t[b] - 1.0) / dt[b]
    out[b] = x * x + x + x + 1.0
    return out


def pulse_wave(freq, duty, sr, phase0=0.0):
    """頻寬限制的脈衝波（-1 到 1）。freq 與 duty 可以是每個取樣一個值的陣列。"""
    freq = np.asarray(freq, dtype=np.float64)
    dt = np.clip(freq / sr, 1e-6, 0.45)
    phase = (phase0 + np.cumsum(dt) - dt[0]) % 1.0
    duty = np.broadcast_to(np.asarray(duty, dtype=np.float64), phase.shape)
    y = np.where(phase < duty, 1.0, -1.0)
    y += _polyblep(phase, dt)
    y -= _polyblep((phase + 1.0 - duty) % 1.0, dt)
    # 工作週期不對稱時有直流成分，扣掉讓不同音色的音量感一致
    return y - (2 * duty - 1)


def triangle_wave(freq, sr, phase0=0.0):
    """32 階的階梯三角波（-1 到 1），跟紅白機一樣只有 16 種高度。"""
    freq = np.asarray(freq, dtype=np.float64)
    dt = freq / sr
    phase = (phase0 + np.cumsum(dt) - dt[0]) % 1.0
    step = np.floor(phase * 32)
    level = np.where(step < 16, 15 - step, step - 16)
    return level / 7.5 - 1.0


_LFSR = {}


def _lfsr(short):
    if short in _LFSR:
        return _LFSR[short]
    reg = 1
    tap = 6 if short else 1
    length = 93 if short else 32767
    out = np.empty(length, dtype=np.float64)
    for i in range(length):
        out[i] = 1.0 if (reg & 1) == 0 else -1.0
        fb = (reg & 1) ^ ((reg >> tap) & 1)
        reg = (reg >> 1) | (fb << 14)
    _LFSR[short] = out
    return out


def noise_wave(period_index, n, sr, short=False, offset=0):
    """雜訊：period_index 可以是每個取樣一個值的陣列（0 最尖、15 最低沉）。"""
    seq = _lfsr(short)
    idx = np.clip(np.asarray(period_index), 0, 15).astype(np.int64)
    rate = CPU / np.asarray(NOISE_PERIODS, dtype=np.float64)[idx]
    rate = np.broadcast_to(rate, (n,))
    pos = np.cumsum(rate / sr) + offset
    return seq[pos.astype(np.int64) % len(seq)]


def quant_vol(v):
    """音量量化成 0 到 15 階，再換成 0 到 1。"""
    return np.round(np.clip(np.asarray(v, dtype=np.float64), 0, 15)) / 15.0


def env_frames(n_frames, start, sustain, decay_frames, release_at=None, release_frames=2):
    """每影格音量：從 start 每 decay_frames 影格降 1 階到 sustain；release_at 之後幾影格內歸零。"""
    f = np.arange(n_frames)
    v = np.maximum(start - f / max(decay_frames, 0.01), sustain)
    if release_at is not None:
        r = np.clip((f - release_at) / max(release_frames, 1), 0, 1)
        v = v * (1 - r)
    return v


# ---------- 濾波與輸出 ----------

def circular_post(x, sr_in, sr_out, hp=40.0):
    """把整首曲子當成循環訊號處理：高通、低通、降取樣都用 FFT 做（環狀），所以循環點完全無縫。"""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / sr_in)
    mask = 1 / np.sqrt(1 + (hp / np.maximum(f, 0.01)) ** 2)
    cut = sr_out * 0.47
    mask *= 1 / np.sqrt(1 + (f / cut) ** 12)
    spec = spec * mask
    if sr_out == sr_in:
        return np.fft.irfft(spec, n)
    ratio = sr_in // sr_out
    m = n // ratio
    keep = m // 2 + 1
    return np.fft.irfft(spec[:keep], m) / ratio


def linear_post(x, sr, hp=30.0, lp=None):
    """音效用：一般（非環狀）的濾波，前後補零避免繞回。"""
    pad = int(0.05 * sr)
    y = np.concatenate([x, np.zeros(pad)])
    spec = np.fft.rfft(y)
    f = np.fft.rfftfreq(len(y), 1 / sr)
    mask = 1 / np.sqrt(1 + (hp / np.maximum(f, 0.01)) ** 2)
    if lp:
        mask *= 1 / np.sqrt(1 + (f / lp) ** 8)
    return np.fft.irfft(spec * mask, len(y))[:len(x)]


def fade_edges(x, sr, fade_in=0.002, fade_out=0.01):
    x = np.array(x, dtype=np.float64)
    a = int(fade_in * sr)
    b = int(fade_out * sr)
    if a > 0:
        x[:a] *= np.linspace(0, 1, a)
    if b > 0:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def write_wav(path: Path, data, sr: int, peak=0.88):
    """寫 16 位元單聲道 WAV；peak 0.88 約等於 -1.1 dBFS。"""
    data = np.asarray(data, dtype=np.float64)
    m = np.max(np.abs(data)) or 1.0
    data = data * (peak / m)
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
