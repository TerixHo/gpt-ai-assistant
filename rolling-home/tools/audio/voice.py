"""共振峰（formant）語音合成：槿寶的歡呼「Yooo～ GIN Gin～」與貓、狗、鴨、雞、青蛙的叫聲。

做法（只用 numpy）：
    1. 聲源：以基頻 f0(t) 的各次諧波相加（加法合成），振幅隨諧波次數遞減（聲門脈衝加嘴唇輻射約 -6 dB／八度），
       基頻帶顫音與微小抖動，聽起來比較像真人。
    2. 聲道：每個諧波的振幅乘上串接式共振峰濾波器在該頻率的增益 |H(f)|，F1 到 F5 隨時間在母音目標之間滑移，
       所以「ㄧ→ㄛ」的滑音（Yooo）和「ㄐ／g→ㄧ→ㄣ」（Gin）都是共振峰軌跡自然做出來的。
       鼻音 /n/ 用鼻腔共振峰加一個反共振（零點）。
    3. 子音：/g/ 是短暫閉塞後的爆破雜訊（帶通 2.5 到 4.5 kHz，前接高母音 /i/ 時軟顎爆破的頻帶），
       接一小段送氣。整段再加一點經過共振峰的氣音。
    4. 修飾：兩個微微走音、延遲的副本做合唱，加上短殘響，聽起來像開心的小朋友在小房間裡叫。
兒童的共振峰比成人約高 15 到 20%，基頻設在 450 到 800 Hz。
"""
import numpy as np

SR = 32000
TAU = 2 * np.pi

# 兒童母音目標（F1、F2、F3、F4、F5，單位 Hz）
VOWELS = {
    "j": (310, 2800, 3500, 4600, 5600),
    "i": (360, 2900, 3550, 4600, 5600),
    "o": (560, 1100, 2900, 4300, 5400),
    "a": (980, 1600, 3000, 4300, 5400),
    "u": (420, 900, 2700, 4200, 5300),
    "e": (650, 2300, 3100, 4400, 5400),
    "n": (290, 1600, 2700, 3900, 5000),
}
BANDWIDTHS = (110, 140, 180, 260, 320)


def _interp(keys, n, sr):
    """keys：[(秒, 值), ...] 線性內插成每個取樣一個值。"""
    t = np.arange(n) / sr
    ks = np.array([k[0] for k in keys])
    vs = np.array([k[1] for k in keys], dtype=np.float64)
    return np.interp(t, ks, vs)


def _smooth(x, sr, ms=12.0):
    k = max(int(sr * ms / 1000), 1)
    w = np.hanning(2 * k + 1)
    w /= w.sum()
    return np.convolve(np.pad(x, k, mode="edge"), w, mode="valid")


def _resonance(f, F, B):
    return F * F / np.sqrt((F * F - f * f) ** 2 + (B * f) ** 2)


def _antiresonance(f, Z, B):
    return np.sqrt((Z * Z - f * f) ** 2 + (B * f) ** 2) / (Z * Z)


def bandpass_noise(n, lo, hi, sr, rng):
    x = rng.standard_normal(n)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / sr)
    mask = (1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 6)) * (1 / np.sqrt(1 + (f / hi) ** 6))
    return np.fft.irfft(spec * mask, n)


def synth(dur, f0_keys, vowel_keys, amp_keys, nasal_keys=None, breath=0.04, vib=(6.0, 0.025, 0.15),
          tilt=0.85, jitter=0.004, rough=0.0, formant_scale=1.0, seed=1, sr=SR):
    """vowel_keys：[(秒, 母音代號)]；母音之間的共振峰平滑滑移。回傳單聲道陣列。"""
    rng = np.random.default_rng(seed)
    n = int(dur * sr)
    t = np.arange(n) / sr
    f0 = _interp(f0_keys, n, sr)
    rate, depth, delay = vib
    vib_env = np.clip((t - delay) / 0.12, 0, 1)
    f0 = f0 * (1 + depth * vib_env * np.sin(TAU * rate * t))
    # 慢速隨機抖動（真人的音高不會完全穩定）
    wob = _smooth(rng.standard_normal(n), sr, 25.0)
    wob /= np.max(np.abs(wob)) or 1
    f0 = f0 * (1 + jitter * wob)
    if rough > 0:
        f0 = f0 * (1 + rough * np.sin(TAU * 70 * t) * rng.uniform(0.6, 1.0))

    forms = []
    for i in range(5):
        keys = [(k[0], VOWELS[k[1]][i] * formant_scale) for k in vowel_keys]
        forms.append(_smooth(_interp(keys, n, sr), sr, 18.0))
    nasal = _smooth(_interp(nasal_keys, n, sr), sr, 15.0) if nasal_keys else np.zeros(n)
    amp = _smooth(_interp(amp_keys, n, sr), sr, 6.0)

    phase = np.cumsum(f0 / sr)
    out = np.zeros(n)
    kmax = int(sr * 0.47 / max(f0.min(), 50))
    for k in range(1, kmax + 1):
        fk = k * f0
        valid = fk < sr * 0.45
        if not valid.any():
            break
        g = np.ones(n)
        for i in range(5):
            g *= _resonance(fk, forms[i], BANDWIDTHS[i])
        # 鼻音：低頻鼻腔共振、1.3 kHz 附近反共振，整體較悶
        gn = _resonance(fk, 280.0, 100.0) * _resonance(fk, 2500.0, 300.0) * _antiresonance(fk, 1300.0, 250.0) * 0.6
        g = g * (1 - nasal) + gn * nasal
        src = 1.0 / k ** tilt
        out += np.where(valid, np.sin(TAU * k * phase) * src * g, 0.0)
    out *= amp
    if breath > 0:
        nz = rng.standard_normal(n)
        spec = np.fft.rfft(nz)
        ff = np.fft.rfftfreq(n, 1 / sr)
        mean_forms = [np.mean(fm) for fm in forms]
        # 氣音只留中高頻（低於 600 Hz 的雜訊聽起來像風切，不像呼吸）
        g = (ff / 600.0) ** 2 / (1 + (ff / 600.0) ** 2)
        for i in range(4):
            g *= _resonance(ff, mean_forms[i], BANDWIDTHS[i] * 2)
        asp = np.fft.irfft(spec * g, n)
        asp /= np.max(np.abs(asp)) or 1
        out += asp * breath * amp * np.max(np.abs(out))
    return out


def burst(n_len, lo, hi, sr, rng, decay=0.004):
    t = np.arange(n_len) / sr
    return bandpass_noise(n_len, lo, hi, sr, rng) * np.exp(-t / decay)


def place(dst, src, at):
    end = min(at + len(src), len(dst))
    dst[at:end] += src[:end - at]


def chorus_reverb(x, sr, wet=0.16, chorus=0.3, seed=3, room=0.32):
    rng = np.random.default_rng(seed)
    n = len(x)
    out = x.copy()
    # 合唱：兩個副本，延遲 11 與 17 毫秒，用重新取樣做 ±8 音分的微走音
    for delay_ms, cents in ((11, 8), (17, -9)):
        ratio = 2 ** (cents / 1200)
        idx = np.arange(n) * ratio
        cp = np.interp(idx, np.arange(n), x, right=0)
        d = int(sr * delay_ms / 1000)
        out[d:] += cp[:n - d] * chorus * 0.5
    # 短殘響：指數衰減的濾波雜訊當脈衝響應
    ir_n = int(room * 1.6 * sr)
    tt = np.arange(ir_n) / sr
    ir = bandpass_noise(ir_n, 300, 7000, sr, rng) * np.exp(-tt / (room / 6.9 * 2.0))
    ir[: int(0.008 * sr)] = 0
    ir /= np.sqrt(np.sum(ir ** 2)) or 1
    m = n + ir_n
    wetsig = np.fft.irfft(np.fft.rfft(out, m) * np.fft.rfft(ir, m), m)
    full = np.concatenate([out, np.zeros(ir_n)])
    full = full + wetsig * wet * (np.max(np.abs(out)) / (np.max(np.abs(wetsig)) or 1))
    return full


def cheer_gin(variant=1, sr=SR):
    """「Yooo～ GIN Gin～」：Yooo 拉長、第一個 GIN 用力、第二個 Gin 音調往上揚。"""
    p, sp, rise = {1: (1.0, 1.0, 1.0), 2: (1.08, 0.9, 1.08), 3: (0.95, 1.18, 1.15)}[variant]
    rng = np.random.default_rng(10 + variant)

    def T(x):
        return x * sp

    # 1. Yooo～
    y_d = T(0.62)
    yo = synth(y_d + 0.05,
               f0_keys=[(0, 470 * p), (T(0.10), 560 * p), (T(0.38), 590 * p), (y_d, 545 * p)],
               vowel_keys=[(0, "j"), (T(0.035), "j"), (T(0.14), "o"), (y_d, "o")],
               amp_keys=[(0, 0), (0.025, 0.85), (T(0.12), 1.0), (y_d - 0.09, 0.95), (y_d, 0), (y_d + 0.05, 0)],
               vib=(6.2, 0.028, 0.2), breath=0.05, seed=20 + variant, sr=sr)
    gap1 = T(0.07)
    # 2. GIN（重音）
    g1_d = T(0.25)
    gin1 = synth(g1_d,
                 f0_keys=[(0, 660 * p), (T(0.12), 640 * p), (g1_d, 600 * p)],
                 vowel_keys=[(0, "i"), (T(0.15), "i"), (T(0.19), "n"), (g1_d, "n")],
                 nasal_keys=[(0, 0), (T(0.15), 0), (T(0.19), 1), (g1_d, 1)],
                 amp_keys=[(0, 0), (0.012, 1.0), (T(0.15), 0.95), (T(0.19), 0.45), (g1_d - 0.03, 0.35), (g1_d, 0)],
                 vib=(6.0, 0.01, 0.2), breath=0.06, seed=30 + variant, sr=sr)
    gap2 = T(0.06)
    # 3. Gin～（往上揚）
    g2_d = T(0.55)
    gin2 = synth(g2_d + 0.05,
                 f0_keys=[(0, 560 * p), (T(0.32), 740 * p * rise), (g2_d, 800 * p * rise)],
                 vowel_keys=[(0, "i"), (T(0.38), "i"), (T(0.44), "n"), (g2_d, "n")],
                 nasal_keys=[(0, 0), (T(0.38), 0), (T(0.44), 1), (g2_d, 1)],
                 amp_keys=[(0, 0), (0.014, 0.9), (T(0.30), 1.0), (T(0.38), 0.9), (T(0.44), 0.4), (g2_d, 0), (g2_d + 0.05, 0)],
                 vib=(6.5, 0.03, 0.18), breath=0.05, seed=40 + variant, sr=sr)

    total = len(yo) + int((gap1 + gap2) * sr) + len(gin1) + len(gin2) + int(0.05 * sr)
    out = np.zeros(total)
    pos = 0
    place(out, yo, pos)
    pos += int((y_d + gap1) * sr)
    peak = np.max(np.abs(yo))
    # /g/：閉塞後的軟顎爆破與短送氣
    place(out, burst(int(0.012 * sr), 2400, 4600, sr, rng) * peak * 0.55, pos - int(0.012 * sr))
    place(out, gin1, pos)
    pos += len(gin1) + int(gap2 * sr)
    place(out, burst(int(0.012 * sr), 2400, 4600, sr, rng) * peak * 0.5, pos - int(0.012 * sr))
    place(out, gin2, pos)
    return chorus_reverb(presence(out, sr), sr, wet=0.18, chorus=0.32, seed=50 + variant)


def presence(x, sr, corner=2500.0, gain=2.0):
    """高頻提升（shelving 濾波，2.5 kHz 以上約 +6 dB），讓小朋友的聲音更亮、更清楚。"""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    r = (f / corner) ** 2
    return np.fft.irfft(spec * (1 + (gain - 1) * r / (1 + r)), len(x))


def meow(sr=SR):
    d = 0.6
    return chorus_reverb(synth(d, f0_keys=[(0, 560), (0.14, 820), (0.36, 760), (d, 560)],
                               vowel_keys=[(0, "n"), (0.07, "i"), (0.22, "a"), (0.45, "o"), (d, "u")],
                               nasal_keys=[(0, 1), (0.07, 0), (d, 0)],
                               amp_keys=[(0, 0), (0.03, 0.6), (0.12, 1), (0.42, 0.85), (d, 0)],
                               vib=(7.0, 0.03, 0.15), breath=0.08, seed=61, sr=sr), sr, wet=0.08, chorus=0.0)


def woof(sr=SR):
    rng = np.random.default_rng(62)
    d = 0.2
    x = synth(d, f0_keys=[(0, 340), (0.05, 360), (d, 240)],
              vowel_keys=[(0, "u"), (0.05, "a"), (d, "o")],
              amp_keys=[(0, 0), (0.006, 1), (0.1, 0.8), (d, 0)],
              vib=(0, 0, 1), breath=0.35, jitter=0.03, rough=0.05, tilt=0.9, formant_scale=0.85, seed=63, sr=sr)
    x[: int(0.02 * sr)] += burst(int(0.02 * sr), 300, 2500, sr, rng, 0.006) * np.max(np.abs(x)) * 0.5
    return chorus_reverb(x, sr, wet=0.08, chorus=0.0)


def duck(sr=SR):
    rng = np.random.default_rng(64)
    out = np.zeros(int(0.62 * sr))
    for i, (at, f) in enumerate(((0.0, 330), (0.3, 300))):
        d = 0.24 if i == 0 else 0.2
        q = synth(d, f0_keys=[(0, f), (0.06, f * 1.08), (d, f * 0.85)],
                  vowel_keys=[(0, "u"), (0.04, "a"), (d, "a")],
                  nasal_keys=[(0, 0.6), (d, 0.45)],
                  amp_keys=[(0, 0), (0.01, 1), (d - 0.05, 0.7), (d, 0)],
                  vib=(0, 0, 1), breath=0.12, jitter=0.02, rough=0.18, tilt=0.7, formant_scale=1.1, seed=65 + i, sr=sr)
        q[: int(0.012 * sr)] += burst(int(0.012 * sr), 1500, 4000, sr, rng) * np.max(np.abs(q)) * 0.4
        place(out, q, int(at * sr))
    return out


def chicken(sr=SR):
    out = np.zeros(int(0.6 * sr))
    for i, (at, f, d) in enumerate(((0.0, 470, 0.09), (0.15, 440, 0.09), (0.3, 520, 0.24))):
        c = synth(d, f0_keys=[(0, f), (d * 0.4, f * 1.15), (d, f * 0.9)],
                  vowel_keys=[(0, "u"), (d * 0.5, "o"), (d, "a" if i == 2 else "u")],
                  amp_keys=[(0, 0), (0.008, 1), (d * 0.6, 0.7), (d, 0)],
                  vib=(0, 0, 1), breath=0.1, jitter=0.02, rough=0.08, seed=70 + i, sr=sr)
        place(out, c, int(at * sr))
    return out


def frog(sr=SR):
    out = np.zeros(int(0.62 * sr))
    for i, at in enumerate((0.0, 0.3)):
        d = 0.22
        c = synth(d, f0_keys=[(0, 150), (0.1, 175), (d, 140)],
                  vowel_keys=[(0, "o"), (0.08, "a"), (d, "o")],
                  amp_keys=[(0, 0), (0.01, 1), (d - 0.04, 0.8), (d, 0)],
                  vib=(0, 0, 1), breath=0.15, jitter=0.03, tilt=0.6, formant_scale=0.9, seed=80 + i, sr=sr)
        t = np.arange(len(c)) / sr
        c *= 0.55 + 0.45 * np.tanh(4 * np.sin(TAU * 24 * t))  # 呱呱的顫動
        place(out, c, int(at * sr))
    return out
