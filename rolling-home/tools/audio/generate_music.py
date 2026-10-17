#!/usr/bin/env python3
"""合成配樂（電子慢速爵士）與拾取、跳躍、轉身音效。全部原創，以 numpy 合成。

用法：
    python3 tools/audio/generate_music.py [輸出資料夾]
預設輸出到 godot/assets/audio：
    music_home.wav   遊戲中：88 BPM、F 大調，lo-fi 爵士嘻哈節奏，16 小節無縫循環
    music_title.wav  標題畫面：76 BPM、Eb 大調，刷鼓與電鋼琴，8 小節無縫循環
    pop.wav、ding.wav、chirp.wav  黏到東西：啵、叮、啾啾
    jump.wav、turn.wav            跳躍的彈簧聲、轉身的咻聲
    charge_loop.wav、charge_level.wav、flame.wav、launch.wav  集氣旋轉、升段、藍色火焰、衝出去
加上 --sfx-only 只重新產生音效（配樂不變）。

編曲：電鋼琴（FM 合成，左右輕擺）、鐵琴主旋律（含延遲回音）、圓潤低音、柔和襯底、
軟鼓組（搖擺十六分音符）、泡泡音點綴、淡淡的黑膠沙沙聲，最後加殘響。
循環點會把超出長度的殘響尾巴接回開頭，所以循環時不會斷。
"""
import sys
import wave
from pathlib import Path

import numpy as np

MUSIC_SR = 32000
SFX_SR = 44100
TAU = 2 * np.pi


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def write_wav(path: Path, data: np.ndarray, sr: int, peak=0.89):
    data = np.asarray(data, dtype=np.float64)
    m = np.max(np.abs(data)) or 1.0
    data = data * (peak / m)
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1 if data.ndim == 1 else data.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def fft_filter(x, sr, lo=None, hi=None, tilt=None):
    """用頻譜遮罩做濾波（噪音塑形用，不需要逐點迴圈）。"""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    mask = np.ones_like(f)
    if lo:
        mask *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        mask *= 1 / (1 + (f / hi) ** 4)
    if tilt:
        mask *= 1 / (1 + (f / tilt) ** 2)
    return np.fft.irfft(spec * mask, len(x))


# ---------- 樂器 ----------

def rhodes(f, dur, vel, sr, rng):
    """FM 電鋼琴：調變指數隨時間衰減，起音帶一點鐘聲般的音叉泛音，左右聲道反相震音。"""
    n = int((dur + 0.6) * sr)
    t = np.arange(n) / sr
    index = 1.6 * np.exp(-t / 0.22) + 0.25
    tone = np.sin(TAU * f * t + index * np.sin(TAU * f * t))
    tine = 0.18 * np.sin(TAU * f * 7.0 * t) * np.exp(-t / 0.025)
    env = np.minimum(t / 0.003, 1) * np.exp(-t / 1.8)
    rel = np.clip((t - dur) / 0.15, 0, 1)
    env *= 1 - rel
    sig = (tone + tine) * env * vel
    trem = 0.13 * np.sin(TAU * 4.6 * t + rng.uniform(0, TAU))
    return np.stack([sig * (1 + trem), sig * (1 - trem)], axis=1)


def vibes(f, dur, vel, sr, rng):
    """鐵琴：三個泛音各自衰減，馬達震音，木槌敲擊的瞬間噪音。"""
    n = int((dur + 1.6) * sr)
    t = np.arange(n) / sr
    sig = (np.sin(TAU * f * t) * np.exp(-t / 1.6)
           + 0.25 * np.sin(TAU * f * 3.92 * t) * np.exp(-t / 0.5)
           + 0.06 * np.sin(TAU * f * 9.8 * t) * np.exp(-t / 0.12))
    sig *= 1 + 0.22 * np.sin(TAU * 5.2 * t)
    sig *= np.minimum(t / 0.002, 1)
    sig *= 1 - np.clip((t - dur - 0.25) / 0.5, 0, 1)
    click = rng.normal(0, 1, n) * np.exp(-t / 0.002) * 0.08
    return (sig + click) * vel


def bass(f, dur, vel, sr):
    n = int((dur + 0.12) * sr)
    t = np.arange(n) / sr
    sig = np.sin(TAU * f * t) + 0.35 * np.sin(TAU * 2 * f * t) + 0.1 * np.sin(TAU * 3 * f * t)
    env = np.minimum(t / 0.006, 1) * (0.7 + 0.3 * np.exp(-t / 0.18))
    env *= 1 - np.clip((t - dur) / 0.08, 0, 1)
    return np.tanh(sig * env * 1.3) * vel


def pad(freqs, dur, vel, sr):
    """柔和的襯底：限頻鋸齒波三聲部微微走音，慢起慢收。"""
    n = int((dur + 0.8) * sr)
    t = np.arange(n) / sr
    sig = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.0, 0.004):
            ff = f * (1 + det)
            k = 1
            while k * ff < 3000:
                sig += np.sin(TAU * k * ff * t) / k / (1 + (k * ff / 700) ** 2)
                k += 1
    env = np.minimum(t / 0.45, 1) * (1 - np.clip((t - dur) / 0.7, 0, 1))
    return sig * env * vel / max(len(freqs), 1)


def bubble(f, vel, sr):
    """泡泡音：音高一下往上滑，很短。"""
    n = int(0.18 * sr)
    t = np.arange(n) / sr
    ff = f * (0.6 + 0.4 * (1 - np.exp(-t / 0.012)))
    phase = TAU * np.cumsum(ff) / sr
    return np.sin(phase) * np.exp(-t / 0.05) * np.minimum(t / 0.002, 1) * vel


class Drums:
    def __init__(self, sr, rng):
        self.sr = sr
        noise = rng.normal(0, 1, int(0.6 * sr))
        self.snare_noise = fft_filter(noise, sr, lo=900, hi=6500)
        self.hat_noise = fft_filter(rng.normal(0, 1, int(0.4 * sr)), sr, lo=7000)
        self.brush_noise = fft_filter(rng.normal(0, 1, int(0.6 * sr)), sr, lo=1800, hi=9000)

    def kick(self, vel):
        n = int(0.4 * self.sr)
        t = np.arange(n) / self.sr
        f = 45 + 75 * np.exp(-t / 0.035)
        body = np.sin(TAU * np.cumsum(f) / self.sr) * np.exp(-t / 0.2)
        return np.tanh(body * 1.5) * vel

    def snare(self, vel):
        n = int(0.3 * self.sr)
        t = np.arange(n) / self.sr
        tone = 0.45 * np.sin(TAU * 185 * t) * np.exp(-t / 0.05)
        return (tone + self.snare_noise[:n] * 0.5 * np.exp(-t / 0.11)) * vel

    def hat(self, vel, open_=False):
        n = int((0.3 if open_ else 0.06) * self.sr)
        t = np.arange(n) / self.sr
        return self.hat_noise[:n] * np.exp(-t / (0.16 if open_ else 0.022)) * vel * 0.5

    def brush(self, vel):
        n = int(0.35 * self.sr)
        t = np.arange(n) / self.sr
        env = np.minimum(t / 0.04, 1) * np.exp(-np.maximum(t - 0.04, 0) / 0.1)
        return self.brush_noise[:n] * env * vel * 0.4


# ---------- 編曲工具 ----------

class Song:
    def __init__(self, bpm, bars, sr, seed, swing=0.6):
        self.sr = sr
        self.beat = 60.0 / bpm
        self.loop_len = int(bars * 4 * self.beat * sr)
        self.tail = int(3.5 * sr)
        self.rng = np.random.default_rng(seed)
        self.swing = swing
        self.buses = {k: np.zeros((self.loop_len + self.tail, 2)) for k in ("keys", "lead", "bass", "drums", "fx")}

    def time(self, bar, beat_pos):
        """搖擺：每個八分音符裡的第二個十六分音符往後推。"""
        eighth, rem = divmod(beat_pos * 2, 1.0)
        if abs(rem - 0.5) < 1e-6:
            rem = self.swing
        pos = (eighth + rem) / 2
        jitter = self.rng.normal(0, 0.004)
        return (bar * 4 + pos) * self.beat + jitter

    def put(self, bus, sig, start_sec, pan=0.0):
        i = max(int(start_sec * self.sr), 0)
        if sig.ndim == 1:
            left = np.cos((pan + 1) * np.pi / 4)
            right = np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * left, sig * right], axis=1)
        buf = self.buses[bus]
        end = min(i + len(sig), len(buf))
        if end > i:
            buf[i:end] += sig[:end - i]

    def delay(self, x, time_sec, feedback=0.32, taps=4, mix=0.35):
        """乒乓延遲。"""
        out = x.copy()
        d = int(time_sec * self.sr)
        amp = mix
        for k in range(1, taps + 1):
            shifted = np.zeros_like(x)
            shifted[d * k:] = x[:-d * k]
            if k % 2:
                shifted = shifted[:, ::-1]
            out += shifted * amp
            amp *= feedback
        return out

    def reverb(self, x, decay=1.4, mix=0.25):
        n = int(decay * 1.6 * self.sr)
        t = np.arange(n) / self.sr
        ir = np.zeros((n, 2))
        for ch in range(2):
            noise = self.rng.normal(0, 1, n) * np.exp(-t * 6.9 / decay)
            ir[:, ch] = fft_filter(noise, self.sr, tilt=4500)
        pre = int(0.018 * self.sr)
        ir = np.vstack([np.zeros((pre, 2)), ir])
        ir /= np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True))
        size = 1 << int(np.ceil(np.log2(len(x) + len(ir))))
        wet = np.zeros_like(x)
        for ch in range(2):
            y = np.fft.irfft(np.fft.rfft(x[:, ch], size) * np.fft.rfft(ir[:, ch], size), size)
            wet[:, ch] = y[:len(x)]
        return x + wet * mix

    def crackle(self, level=0.012):
        n = self.loop_len + self.tail
        hiss = fft_filter(self.rng.normal(0, 1, n), self.sr, lo=2500, hi=9000) * level * 0.25
        clicks = np.zeros(n)
        idx = self.rng.integers(0, n, int(n / self.sr * 7))
        clicks[idx] = self.rng.uniform(-1, 1, len(idx)) * level * 6
        clicks = fft_filter(clicks, self.sr, hi=5000)
        self.buses["fx"] += np.stack([hiss + clicks, hiss * 0.9 + clicks], axis=1)

    def mix(self, gains, reverb_decay, reverb_mix, lead_delay):
        lead = self.delay(self.buses["lead"], lead_delay) if lead_delay else self.buses["lead"]
        dry = (self.buses["keys"] * gains["keys"] + lead * gains["lead"] + self.buses["bass"] * gains["bass"]
               + self.buses["drums"] * gains["drums"] + self.buses["fx"] * gains["fx"])
        wet_src = self.buses["keys"] * gains["keys"] + lead * gains["lead"] + self.buses["drums"] * gains["drums"] * 0.4
        out = dry + (self.reverb(wet_src, reverb_decay, 1.0) - wet_src) * reverb_mix
        # 無縫循環：超出長度的尾巴接回開頭
        looped = out[:self.loop_len].copy()
        looped[:self.tail] += out[self.loop_len:self.loop_len + self.tail]
        looped = np.tanh(looped * 1.4 / np.max(np.abs(looped))) / np.tanh(1.4)
        return looped


def bass_line(song, bar, root, next_root, vel=0.9, busy=False):
    r = root
    approach = next_root - 1 if (bar % 2) else next_root + 2
    notes = [(0.0, 1.25, r), (1.5, 0.5, r + 7), (2.5, 0.75, r + 12 if busy else r + 10), (3.5, 0.45, approach)]
    for pos, dur, m in notes:
        song.put("bass", bass(hz(m), dur * song.beat, vel * song.rng.uniform(0.85, 1.0), song.sr), song.time(bar, pos))


def comp(song, bar, voicing, pattern, vel=0.22):
    for pos, dur in pattern:
        for m in voicing:
            sig = rhodes(hz(m), dur * song.beat, vel * song.rng.uniform(0.85, 1.0), song.sr, song.rng)
            song.put("keys", sig, song.time(bar, pos) + song.rng.uniform(0, 0.012))


def melody(song, bar, notes, vel=0.5, pan=0.25):
    for pos, dur, m in notes:
        song.put("lead", vibes(hz(m), dur * song.beat, vel * song.rng.uniform(0.85, 1.0), song.sr, song.rng),
                 song.time(bar, pos), pan)


# ---------- 遊戲中：電子慢速爵士（F 大調，88 BPM） ----------

HOME_CHORDS = [  # (低音根音, 電鋼琴無根音配置)
    (46, [62, 65, 69, 72]),   # Bbmaj9
    (45, [60, 64, 67, 71]),   # Am9
    (43, [58, 62, 65, 69]),   # Gm9
    (36, [58, 62, 64, 69]),   # C13
    (41, [57, 60, 64, 67]),   # Fmaj9
    (38, [60, 64, 65, 69]),   # Dm9
    (43, [58, 62, 65, 69]),   # Gm9
    (36, [64, 67, 70, 73]),   # C7b9
]

HOME_MELODY_A = [
    [(0.0, 0.5, 72), (0.5, 0.5, 74), (1.0, 1.0, 77), (2.5, 0.5, 76), (3.0, 1.0, 74)],
    [(0.5, 0.5, 72), (1.0, 0.5, 76), (1.5, 1.5, 79), (3.5, 0.5, 77)],
    [(0.0, 1.5, 74), (1.5, 0.5, 77), (2.0, 0.5, 81), (2.5, 1.0, 79)],
    [(0.0, 0.5, 76), (0.5, 0.5, 74), (1.0, 2.0, 69), (3.5, 0.5, 72)],
    [(0.0, 1.0, 76), (1.0, 0.5, 79), (1.5, 1.0, 81), (3.0, 0.5, 79), (3.5, 0.5, 76)],
    [(0.0, 1.5, 77), (2.0, 0.5, 76), (2.5, 0.5, 74), (3.0, 1.0, 72)],
    [(0.5, 0.5, 70), (1.0, 0.5, 72), (1.5, 0.5, 74), (2.0, 1.5, 77)],
    [(0.0, 0.5, 76), (0.5, 0.5, 73), (1.0, 0.5, 70), (1.5, 0.5, 67), (2.0, 2.0, 64)],
]

HOME_MELODY_B = [
    [(0.0, 0.5, 77), (0.5, 0.5, 76), (1.0, 0.5, 74), (1.5, 1.0, 72)],
    [(0.0, 1.5, 76), (2.0, 0.5, 79), (2.5, 1.0, 81)],
    [(0.0, 0.5, 82), (0.5, 0.5, 81), (1.0, 0.5, 79), (1.5, 0.5, 77), (2.0, 1.5, 74)],
    [(0.0, 0.5, 76), (0.5, 0.5, 79), (1.0, 1.0, 82), (2.5, 1.5, 81)],
    [(0.0, 2.0, 81), (2.0, 0.5, 79), (2.5, 0.5, 76), (3.0, 1.0, 77)],
    [(0.0, 1.0, 77), (1.0, 0.5, 74), (1.5, 0.5, 72), (2.0, 2.0, 69)],
    [(0.0, 0.5, 74), (0.5, 0.5, 77), (1.0, 0.5, 81), (1.5, 0.5, 84), (2.0, 1.5, 82)],
    [(0.0, 0.5, 79), (0.5, 0.5, 76), (1.0, 0.5, 73), (1.5, 0.5, 70), (2.0, 1.0, 72), (3.0, 1.0, 72)],
]

HOME_BUBBLES = {  # 第二輪：泡泡音呼應旋律（小節: [(拍, 音)]）
    8: [(3.0, 84), (3.25, 86), (3.5, 89)],
    9: [(3.5, 84)],
    13: [(2.5, 84), (2.75, 81), (3.0, 77)],
    15: [(3.0, 89), (3.25, 86)],
}


def music_home(out: Path):
    song = Song(88, 16, MUSIC_SR, seed=2026, swing=0.62)
    drums = Drums(MUSIC_SR, song.rng)
    comp_a = [(0.0, 1.4), (1.75, 0.35), (2.5, 1.2)]
    comp_b = [(0.0, 0.9), (1.25, 0.4), (2.0, 0.35), (2.75, 1.0)]
    for bar in range(16):
        root, voicing = HOME_CHORDS[bar % 8]
        next_root = HOME_CHORDS[(bar + 1) % 8][0]
        bass_line(song, bar, root, next_root, busy=bar >= 8)
        comp(song, bar, voicing, comp_a if bar < 8 else comp_b)
        song.put("keys", pad([hz(m - 12) for m in voicing[:3]], 4 * song.beat, 0.35, song.sr), song.time(bar, 0))
        mel = HOME_MELODY_A[bar] if bar < 8 else HOME_MELODY_B[bar - 8]
        melody(song, bar, mel)
        for pos, m in HOME_BUBBLES.get(bar, []):
            song.put("lead", bubble(hz(m), 0.35, song.sr), song.time(bar, pos), -0.4)
        # 鼓：大鼓 1、2a、3&；小鼓 2、4 加鬼音；腳踏鈸搖擺十六分音符
        for pos, v in ((0.0, 1.0), (1.75, 0.6), (2.5, 0.85)):
            song.put("drums", drums.kick(v), song.time(bar, pos))
        for pos, v in ((1.0, 0.8), (3.0, 0.85), (0.75, 0.18), (2.25, 0.15), (3.75, 0.2 if bar % 2 else 0.0)):
            if v:
                song.put("drums", drums.snare(v), song.time(bar, pos), 0.1)
        for k in range(8):
            pos = k * 0.5
            open_ = (pos == 3.5 and bar % 2 == 1)
            song.put("drums", drums.hat(0.55 if k % 2 == 0 else 0.35, open_), song.time(bar, pos), 0.3)
            if bar >= 8 and k % 2 == 1:
                song.put("drums", drums.hat(0.2), song.time(bar, pos + 0.25), 0.35)
    song.crackle()
    data = song.mix({"keys": 0.9, "lead": 0.55, "bass": 0.8, "drums": 0.55, "fx": 1.0},
                    reverb_decay=1.3, reverb_mix=0.28, lead_delay=song.beat * 0.75)
    write_wav(out / "music_home.wav", data, MUSIC_SR)


# ---------- 標題畫面：夢幻刷鼓（Eb 大調，76 BPM） ----------

TITLE_CHORDS = [
    (39, [55, 58, 62, 65]),   # Ebmaj9
    (36, [58, 62, 63, 67]),   # Cm9
    (41, [56, 60, 63, 67]),   # Fm9
    (34, [56, 60, 62, 67]),   # Bb13
]

TITLE_MELODY = [
    [(0.5, 0.5, 70), (1.0, 0.5, 72), (1.5, 1.5, 74), (3.5, 0.5, 75)],
    [(0.0, 1.5, 79), (2.0, 0.5, 77), (2.5, 1.5, 75)],
    [(0.0, 0.5, 72), (0.5, 0.5, 75), (1.0, 1.0, 79), (2.5, 0.5, 77), (3.0, 1.0, 75)],
    [(0.0, 2.0, 74), (2.5, 0.5, 72), (3.0, 1.0, 70)],
    [(0.5, 0.5, 70), (1.0, 0.5, 74), (1.5, 0.5, 77), (2.0, 2.0, 82)],
    [(0.0, 1.0, 79), (1.0, 0.5, 77), (1.5, 0.5, 75), (2.0, 2.0, 74)],
    [(0.0, 0.5, 72), (0.5, 0.5, 75), (1.0, 0.5, 79), (1.5, 1.5, 84), (3.5, 0.5, 82)],
    [(0.0, 1.5, 79), (2.0, 2.0, 74)],
]


def music_title(out: Path):
    song = Song(76, 8, MUSIC_SR, seed=76, swing=0.64)
    drums = Drums(MUSIC_SR, song.rng)
    for bar in range(8):
        root, voicing = TITLE_CHORDS[bar % 4]
        next_root = TITLE_CHORDS[(bar + 1) % 4][0]
        bass_line(song, bar, root, next_root, vel=0.75)
        comp(song, bar, voicing, [(0.0, 2.2), (2.5, 1.3)], vel=0.2)
        # 電鋼琴分解和弦點綴
        for k, m in enumerate(voicing + [voicing[1] + 12]):
            song.put("keys", rhodes(hz(m + 12), 0.4 * song.beat, 0.07, song.sr, song.rng), song.time(bar, 2.0 + k * 0.25))
        song.put("keys", pad([hz(m - 12) for m in voicing[:3]], 4 * song.beat, 0.4, song.sr), song.time(bar, 0))
        melody(song, bar, TITLE_MELODY[bar], vel=0.45, pan=-0.2)
        song.put("drums", drums.kick(0.7), song.time(bar, 0.0))
        song.put("drums", drums.kick(0.45), song.time(bar, 2.5))
        for pos in (1.0, 3.0):
            song.put("drums", drums.brush(0.9), song.time(bar, pos), 0.15)
        for k in range(8):
            song.put("drums", drums.brush(0.25 if k % 2 else 0.35), song.time(bar, k * 0.5), -0.2)
    song.crackle(0.01)
    data = song.mix({"keys": 0.95, "lead": 0.6, "bass": 0.7, "drums": 0.5, "fx": 1.0},
                    reverb_decay=1.8, reverb_mix=0.35, lead_delay=song.beat * 0.75)
    write_wav(out / "music_title.wav", data, MUSIC_SR)


# ---------- 音效 ----------

def sfx(out: Path):
    sr = SFX_SR
    rng = np.random.default_rng(5)

    # 啵：小泡泡破掉，音高快速往上滑
    t = np.arange(int(0.12 * sr)) / sr
    f = 320 + 900 * (1 - np.exp(-t / 0.011))
    pop = np.sin(TAU * np.cumsum(f) / sr) * np.exp(-t / 0.035) * np.minimum(t / 0.0015, 1)
    pop += fft_filter(rng.normal(0, 1, len(t)), sr, lo=2000) * np.exp(-t / 0.003) * 0.15
    write_wav(out / "pop.wav", pop, sr, 0.8)

    # 叮：小鈴鐺，幾個不諧和泛音各自衰減
    t = np.arange(int(0.9 * sr)) / sr
    base = 1318.5
    ding = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, 0.45), (2.0, 0.4, 0.25), (3.01, 0.25, 0.15), (4.2, 0.15, 0.08), (5.43, 0.1, 0.05)):
        ding += amp * np.sin(TAU * base * ratio * t) * np.exp(-t / dec)
    ding *= np.minimum(t / 0.001, 1)
    write_wav(out / "ding.wav", ding, sr, 0.7)

    # 啾啾：兩聲小鳥叫，音高往上揚帶一點顫音
    total = np.zeros(int(0.3 * sr))
    for start, f0, f1 in ((0.0, 2300, 3500), (0.12, 2500, 3900)):
        n = int(0.08 * sr)
        tt = np.arange(n) / sr
        ff = f0 + (f1 - f0) * (tt / 0.08) ** 0.7 + 120 * np.sin(TAU * 45 * tt)
        chirp = np.sin(TAU * np.cumsum(ff) / sr) * np.sin(np.pi * tt / 0.08) ** 1.5
        i = int(start * sr)
        total[i:i + n] += chirp
    write_wav(out / "chirp.wav", total, sr, 0.7)

    # 跳躍：彈簧「啵嚶」聲
    t = np.arange(int(0.32 * sr)) / sr
    f = 200 + 520 * (1 - np.exp(-t / 0.07)) + 40 * np.sin(TAU * 18 * t) * np.exp(-t / 0.15)
    jump = np.sin(TAU * np.cumsum(f) / sr)
    jump = np.tanh(jump * 1.8) * np.exp(-t / 0.12) * np.minimum(t / 0.004, 1)
    write_wav(out / "jump.wav", jump, sr, 0.65)

    # 轉身：一陣咻的風聲
    n = int(0.32 * sr)
    t = np.arange(n) / sr
    noise = rng.normal(0, 1, n)
    lo_band = fft_filter(noise, sr, lo=500, hi=2500)
    hi_band = fft_filter(noise, sr, lo=2500, hi=7000)
    mixk = np.clip(t / 0.32, 0, 1)
    whoosh = (lo_band * (1 - mixk) + hi_band * mixk) * np.sin(np.pi * t / 0.32) ** 2
    write_wav(out / "turn.wav", whoosh, sr, 0.5)


def charge_sfx(out: Path):
    """集氣：旋轉聲（1 秒無縫循環，遊戲中依集氣時間升高音調）、升段晶亮音、藍色火焰點火聲、放開衝出去的爆發聲。"""
    sr = SFX_SR
    rng = np.random.default_rng(9)

    # 旋轉聲：整數週期的頻率在 1 秒內剛好轉完整圈，頭尾接得起來；噪音用頻譜濾波（循環式），也接得起來
    n = sr
    t = np.arange(n) / sr
    whir = np.zeros(n)
    for k, amp in ((1, 1.0), (2, 0.45), (3, 0.25), (5, 0.12)):
        whir += amp * np.sin(TAU * 180 * k * t)
    whir *= 0.55 + 0.45 * np.sin(TAU * 16 * t)
    air = fft_filter(rng.normal(0, 1, n), sr, lo=800, hi=4000) * (0.6 + 0.4 * np.sin(TAU * 16 * t + 1.0))
    loop = np.tanh((whir * 0.5 + air * 0.35) * 1.2)
    write_wav(out / "charge_loop.wav", loop, sr, 0.6)

    # 升段：三個音往上爬的晶亮音
    total = np.zeros(int(0.45 * sr))
    for i, f in enumerate((1318.5, 1661.2, 1975.5)):
        nn = int(0.3 * sr)
        tt = np.arange(nn) / sr
        tone = (np.sin(TAU * f * tt) + 0.3 * np.sin(TAU * f * 2.01 * tt)) * np.exp(-tt / 0.09)
        start = int(i * 0.05 * sr)
        total[start:start + nn] += tone * (0.7 + 0.15 * i)
    write_wav(out / "charge_level.wav", total, sr, 0.6)

    # 藍色火焰點火：一陣「呼」，低通濾波由暗變亮再收
    nn = int(0.7 * sr)
    tt = np.arange(nn) / sr
    noise = rng.normal(0, 1, nn)
    dark = fft_filter(noise, sr, lo=150, hi=900)
    bright = fft_filter(noise, sr, lo=900, hi=5000)
    mixk = np.clip(tt / 0.25, 0, 1)
    flame = (dark * (1 - mixk) + bright * mixk * 0.8) * np.minimum(tt / 0.04, 1) * np.exp(-tt / 0.3)
    flame += 0.4 * np.sin(TAU * np.cumsum(90 + 140 * tt) / sr) * np.exp(-tt / 0.2)
    write_wav(out / "flame.wav", flame, sr, 0.7)

    # 衝出去：強風由高往低掃過，加上低音重擊
    nn = int(0.9 * sr)
    tt = np.arange(nn) / sr
    noise = rng.normal(0, 1, nn)
    hi = fft_filter(noise, sr, lo=2500, hi=9000)
    lo_ = fft_filter(noise, sr, lo=300, hi=2500)
    sweep = np.clip(tt / 0.5, 0, 1)
    wind = (hi * (1 - sweep) + lo_ * sweep) * np.minimum(tt / 0.015, 1) * np.exp(-tt / 0.35)
    boom = np.sin(TAU * np.cumsum(40 + 90 * np.exp(-tt / 0.05)) / sr) * np.exp(-tt / 0.25)
    write_wav(out / "launch.wav", np.tanh(wind * 0.8 + boom * 1.2), sr, 0.8)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else Path(__file__).resolve().parents[2] / "godot" / "assets" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    sfx(out)
    charge_sfx(out)
    if "--sfx-only" in sys.argv:
        return
    music_home(out)
    music_title(out)
    for name in ("pop", "ding", "chirp", "jump", "turn", "music_home", "music_title"):
        p = out / f"{name}.wav"
        with wave.open(str(p)) as w:
            secs = w.getnframes() / w.getframerate()
        print(f"{p.name}\t{p.stat().st_size // 1024} KB\t{secs:.1f} 秒")


if __name__ == "__main__":
    main()
