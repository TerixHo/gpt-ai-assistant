#!/usr/bin/env python3
"""產生遊戲暫代音效與配樂（原創合成，僅使用 Python 標準函式庫）。

用法：
    python3 tools/audio/generate_audio.py [輸出資料夾]
預設輸出到 godot/assets/audio。正式版請以作曲家或授權音源替換同名檔案。
"""
import math
import random
import struct
import sys
import wave
from pathlib import Path

RATE = 22050


def write_wav(path: Path, samples):
    peak = max(1e-6, max(abs(s) for s in samples))
    gain = 0.9 / peak if peak > 0.9 else 1.0
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s * gain)) * 32767)) for s in samples))


def env(t, length, attack=0.005, release=None):
    release = release if release is not None else length * 0.6
    if t < attack:
        return t / attack
    if t > length - release:
        return max(0.0, (length - t) / release)
    return 1.0


def tone(freq_fn, length, wave_fn=math.sin, attack=0.005, release=None, amp=1.0):
    out, phase = [], 0.0
    for i in range(int(length * RATE)):
        t = i / RATE
        phase += 2 * math.pi * freq_fn(t) / RATE
        out.append(wave_fn(phase) * env(t, length, attack, release) * amp)
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def at(samples, start_sec, total_len):
    out = [0.0] * total_len
    s = int(start_sec * RATE)
    for i, v in enumerate(samples):
        if s + i < total_len:
            out[s + i] += v
    return out


def noise(length, amp=1.0, rng=random.Random(1)):
    return [rng.uniform(-1, 1) * env(i / RATE, length) * amp for i in range(int(length * RATE))]


def note_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def soft_square(p):
    return math.tanh(3 * math.sin(p)) * 0.6


def epiano(p):
    return math.sin(p) + 0.3 * math.sin(2 * p) + 0.1 * math.sin(3 * p)


def sfx(out: Path):
    write_wav(out / "pickup.wav", tone(lambda t: 880 + 2400 * t, 0.09, soft_square, release=0.06, amp=0.6))
    n = int(0.32 * RATE)
    write_wav(out / "pickup_big.wav", mix(
        at(tone(lambda t: 660, 0.18, epiano, release=0.15), 0.0, n),
        at(tone(lambda t: 990, 0.2, epiano, release=0.17), 0.09, n)))
    write_wav(out / "bump.wav", mix(tone(lambda t: 110 - 200 * t, 0.2, math.sin, release=0.18), noise(0.08, 0.4)))
    write_wav(out / "drop.wav", tone(lambda t: 700 - 1600 * t, 0.28, soft_square, release=0.2, amp=0.5))
    write_wav(out / "tick.wav", tone(lambda t: 2200, 0.035, math.sin, release=0.03, amp=0.5))
    write_wav(out / "ui.wav", tone(lambda t: 1046, 0.06, soft_square, release=0.05, amp=0.4))
    n = int(0.9 * RATE)
    write_wav(out / "goal.wav", mix(*[at(tone(lambda t, f=note_hz(m): f, 0.35, epiano, release=0.3), i * 0.11, n)
                                      for i, m in enumerate([72, 76, 79, 84])]))
    n = int(0.7 * RATE)
    write_wav(out / "gate.wav", mix(*[at(tone(lambda t, f=note_hz(m): f, 0.3, epiano, release=0.25), i * 0.13, n)
                                      for i, m in enumerate([79, 74, 83])]))
    write_wav(out / "timeup.wav", tone(lambda t: 1200 * (1 - 0.6 * t), 0.9, soft_square, release=0.5, amp=0.5))
    dash = [v * (i / (0.3 * RATE)) for i, v in enumerate(noise(0.3, 0.5, random.Random(5)))]
    # 簡單低通：移動平均
    smooth, acc = [], 0.0
    for v in dash:
        acc = acc * 0.85 + v * 0.15
        smooth.append(acc)
    write_wav(out / "dash.wav", smooth)


def music(out: Path, name: str, bpm: float, progression, seed: int, swing=0.0):
    """原創四和弦循環：低音 + 電鋼琴和弦 + 五聲音階旋律 + 簡易鼓組。"""
    rng = random.Random(seed)
    beat = 60.0 / bpm
    bars = len(progression) * 2
    total = int(bars * 4 * beat * RATE)
    tracks = []
    scale = [0, 2, 4, 7, 9]
    for bar in range(bars):
        root, quality = progression[bar % len(progression)]
        chord = [root, root + (3 if quality == "m" else 4), root + 7, root + (10 if quality in ("m", "7") else 11)]
        t0 = bar * 4 * beat
        for b in range(4):
            bass = root - 24 + ([0, 7, 12, 7][b] if b % 2 else 0)
            tracks.append(at(tone(lambda t, f=note_hz(bass): f, beat * 0.9, math.sin, release=beat * 0.4, amp=0.55), t0 + b * beat, total))
        for b in (0, 2):
            for m in chord:
                tracks.append(at(tone(lambda t, f=note_hz(m + 12): f, beat * 1.6, epiano, attack=0.01, release=beat, amp=0.12),
                                 t0 + (b + 0.5) * beat, total))
        pos = 0.0
        while pos < 4.0:
            dur = rng.choice([0.5, 0.5, 1.0, 1.5])
            if rng.random() < 0.8:
                deg = rng.choice(scale)
                m = 72 + ((root % 12) + deg) % 12 if rng.random() < 0.5 else 72 + deg
                start = t0 + (pos + (swing if (pos * 2) % 2 == 1 else 0)) * beat
                tracks.append(at(tone(lambda t, f=note_hz(m): f, dur * beat * 0.95, soft_square, release=dur * beat * 0.5, amp=0.18), start, total))
            pos += dur
        for b in range(4):
            tracks.append(at(tone(lambda t: 60 * (1 - t * 3), 0.15, math.sin, release=0.12, amp=0.6 if b % 2 == 0 else 0.0), t0 + b * beat, total))
            for h in (0, 0.5):
                tracks.append(at(noise(0.04, 0.12, rng), t0 + (b + h) * beat, total))
    data = [0.0] * total
    for tr in tracks:
        for i, v in enumerate(tr):
            if v:
                data[i] += v
    write_wav(out / f"{name}.wav", data)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "godot" / "assets" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    sfx(out)
    music(out, "music_title", 96, [(60, "M"), (57, "m"), (62, "m"), (55, "7")], seed=7, swing=0.08)
    music(out, "music_home", 132, [(65, "M"), (67, "7"), (64, "m"), (69, "m")], seed=11, swing=0.1)
    for f in sorted(out.glob("*.wav")):
        print(f"{f.name}\t{f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
