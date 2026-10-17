#!/usr/bin/env python3
"""合成全部音效（紅白機風格為主，少量柔和音色）與槿寶的歡呼語音。全部原創，只需要 numpy。

用法：
    python3 tools/audio/generate_sfx.py [輸出資料夾]
預設輸出到 godot/assets/audio（32 kHz 單聲道 16 位元 WAV）。

分類：
    1. 遊戲動作：pop、ding、chirp、pickup、pickup_big、bump、drop、tick、goal、timeup、dash、ui、gate、
       jump、double_jump、flip、turn、charge_loop（1 秒無縫循環）、charge_level、flame、launch、
       rescue、impact_big、burst_drop、milestone、petal、splash、cheer
    2. 動物：meow、woof、duck、chicken、frog、bug
    3. 物件專屬音（items.json 的 "sfx" 欄位）：orange、curry、snack、crayon、yarn、bike_bell、car_horn、
       train_horn、school_bell（西敏寺鐘聲，1793 年作品，屬公眾領域）、bubble、squeak、bell
    4. 歡呼語音：cheer_gin_1、cheer_gin_2、cheer_gin_3（「Yooo～ GIN Gin～」，共振峰合成，見 voice.py）
"""
import sys
from pathlib import Path

import numpy as np

import nes
import voice

SR = 32000
TAU = 2 * np.pi


# ---------- 小工具 ----------

def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def exp_sweep(f0, f1, n):
    return f0 * (f1 / f0) ** np.linspace(0, 1, n)


def frame_steps(x):
    """把連續變化改成每影格一階（紅白機的階梯感）。"""
    n = len(x)
    idx = (np.arange(n) * nes.FRAME_HZ / SR).astype(int)
    first = np.searchsorted(idx, np.arange(idx[-1] + 1))
    return x[first[idx]]


def decay_env(n, tau, attack=0.002):
    t = np.arange(n) / SR
    return np.minimum(t / max(attack, 1e-4), 1) * np.exp(-t / tau)


def vol4(env):
    """音量量化成 16 階並以影格為單位（紅白機的顆粒感）。"""
    return frame_steps(np.round(np.clip(env, 0, 1) * 15) / 15)


def pulse(freq, duty=0.25, env=None, steppy=True):
    freq = np.asarray(freq, dtype=float)
    if steppy:
        freq = frame_steps(freq)
    y = nes.pulse_wave(freq, duty, SR)
    if env is not None:
        y = y * (vol4(env) if steppy else env)
    return y


def tri(freq, env=None):
    y = nes.triangle_wave(np.asarray(freq, dtype=float), SR)
    return y if env is None else y * env


def noise(n, period, env, short=False, steppy=True):
    per = np.broadcast_to(np.asarray(period, dtype=float), (n,)).copy()
    if steppy:
        per = frame_steps(per)
    y = nes.noise_wave(per, n, SR, short=short)
    return y * (vol4(env) if steppy else env)


def note_seq(notes, duty=0.25, step=0.05, tau=0.08, vib=0.0, tail=0.0, vol=1.0):
    """依序的短音（琶音、旋律）：notes 是 MIDI 音高或 None（休止）。"""
    seg = int(step * SR)
    out = np.zeros(seg * len(notes) + int(tail * SR) + seg)
    for i, m in enumerate(notes):
        if m is None:
            continue
        n = seg + (int(tail * SR) if i == len(notes) - 1 else 0)
        t = np.arange(n) / SR
        f = nes.hz(m) * (1 + vib * np.sin(TAU * 6 * t) * np.clip((t - 0.08) / 0.1, 0, 1))
        out[i * seg:i * seg + n] += pulse(f, duty, decay_env(n, tau) * vol)
    return out


def bell_tone(f, dur, ratios=(1.0, 2.0, 2.76, 3.0, 4.07), decays=(1.0, 0.6, 0.35, 0.3, 0.2), amps=(1, 0.5, 0.35, 0.25, 0.15), beat=0.0):
    t = t_axis(dur)
    out = np.zeros_like(t)
    for r, d, a in zip(ratios, decays, amps):
        out += a * np.sin(TAU * f * r * t) * np.exp(-t / (d * dur * 0.5))
        if beat:
            out += a * 0.5 * np.sin(TAU * (f * r + beat) * t) * np.exp(-t / (d * dur * 0.5))
    return out * np.minimum(t / 0.002, 1)


def fm_bell(f, dur, ratio=3.5, index=3.0, tau=0.35):
    t = t_axis(dur)
    idx = index * np.exp(-t / (tau * 0.4))
    return np.sin(TAU * f * t + idx * np.sin(TAU * f * ratio * t)) * np.exp(-t / tau) * np.minimum(t / 0.002, 1)


def mix(*parts, length=None):
    n = length or max(len(p[1]) + int(p[0] * SR) for p in parts)
    out = np.zeros(n)
    for at, sig in parts:
        a = int(at * SR)
        end = min(a + len(sig), n)
        out[a:end] += sig[:end - a]
    return out


def finish(x, hp=40.0, lp=None, fade=0.008):
    return nes.fade_edges(nes.linear_post(x, SR, hp=hp, lp=lp), SR, 0.0005, fade)


# ---------- 遊戲動作 ----------

def s_pop():
    n = int(0.11 * SR)
    f = exp_sweep(nes.hz(84), nes.hz(98), n)
    f[int(0.035 * SR):] = nes.hz(98)
    body = pulse(f, 0.125, decay_env(n, 0.035))
    click = noise(int(0.008 * SR), 0, np.linspace(1, 0, int(0.008 * SR)) * 0.6)
    return finish(mix((0, body), (0, click)))


def s_ding():
    a = note_seq([91], 0.25, 0.055, tau=0.05)
    b = note_seq([98], 0.25, 0.4, tau=0.14, vib=0.004)
    sub = tri(np.full(int(0.4 * SR), nes.hz(86)), decay_env(int(0.4 * SR), 0.1) * 0.35)
    return finish(mix((0, a), (0.055, b), (0.055, sub)))


def s_chirp():
    def one(f0, f1, d=0.07):
        n = int(d * SR)
        return pulse(exp_sweep(f0, f1, n), 0.125, decay_env(n, 0.03, 0.004), steppy=False)
    return finish(mix((0, one(2000, 3600)), (0.105, one(2300, 4100))), lp=9000)


def s_pickup():
    return finish(note_seq([88], 0.5, 0.06, tau=0.03))


def s_pickup_big():
    arp = note_seq([84, 88, 91, 96], 0.25, 0.04, tau=0.05)
    spark = note_seq([96, 103, 96, 103, 96], 0.125, 0.034, tau=0.06, vol=0.6)
    return finish(mix((0, arp), (0.16, spark)))


def s_bump():
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    thud = tri(nes.hz(55 - 22 * np.clip(t / 0.1, 0, 1)), np.exp(-t / 0.07))
    nz = noise(n, 13, np.exp(-t / 0.05) * 0.8)
    return finish(mix((0, thud), (0, nz * 0.5)))


def s_drop():
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    f = nes.hz(81 - 24 * (t / t[-1]) ** 0.8)
    a = pulse(f, 0.5, (1 - t / t[-1]) ** 1.5)
    b = pulse(f * 1.008, 0.125, (1 - t / t[-1]) ** 1.5 * 0.5)
    return finish(a + b)


def s_tick():
    click = noise(int(0.015 * SR), 0, np.linspace(1, 0, int(0.015 * SR)), short=True)
    blip = pulse(np.full(int(0.035 * SR), 1600.0), 0.5, decay_env(int(0.035 * SR), 0.012))
    return finish(mix((0, click * 0.6), (0, blip)))


def s_goal():
    run = note_seq([72, 76, 79, 84, 79, 84], 0.25, 0.07, tau=0.06)
    held = int(0.75 * SR)
    t = np.arange(held) / SR
    vib = 1 + 0.006 * np.sin(TAU * 6 * t) * np.clip((t - 0.1) / 0.1, 0, 1)
    top = pulse(nes.hz(88) * vib, 0.25, np.exp(-t / 0.5))
    harm = pulse(nes.hz(84) * vib, 0.5, np.exp(-t / 0.5) * 0.6)
    bass = tri(np.full(held, nes.hz(60)), np.exp(-t / 0.6))
    crash = noise(held, 3, np.exp(-t / 0.25) * 0.5)
    return finish(mix((0, run), (0.42, top), (0.42, harm), (0.42, bass), (0.42, crash * 0.6)))


def s_timeup():
    def whistle(d, trill=True):
        n = int(d * SR)
        t = np.arange(n) / SR
        f = np.where(np.sin(TAU * 22 * t) > 0, 2900.0, 3250.0) if trill else np.full(n, 2900.0)
        env = np.minimum(t / 0.01, 1) * np.minimum((t[-1] - t) / 0.03, 1)
        return pulse(f, 0.125, env * 0.9)
    return finish(mix((0, whistle(0.12, False)), (0.18, whistle(0.12, False)), (0.36, whistle(0.55))), lp=8000)


def s_dash():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    nz = noise(n, np.round(9 - 7 * t / t[-1]), np.exp(-t / 0.15))
    sw = pulse(exp_sweep(300, 1200, n), 0.125, np.exp(-t / 0.12) * 0.5)
    return finish(nz * 0.7 + sw)


def s_ui():
    return finish(note_seq([95], 0.25, 0.04, tau=0.02), fade=0.004)


def s_gate():
    run = note_seq([72, 76, 79, 84, 88, 91, 96], 0.25, 0.035, tau=0.05)
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    alt = np.where((np.arange(n) // int(SR / 30)) % 2 == 0, nes.hz(96), nes.hz(91))
    shim = pulse(alt, 0.125, np.exp(-t / 0.15) * 0.7)
    return finish(mix((0, run), (0.245, shim)))


def s_cheer():
    arp = note_seq([79, 84, 88, 91], 0.25, 0.05, tau=0.05)
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    alt = np.where((np.arange(n) // int(SR / 20)) % 2 == 0, nes.hz(91), nes.hz(88))
    trill = pulse(alt, 0.25, np.exp(-t / 0.25))
    bass = tri(np.full(n, nes.hz(60)), np.exp(-t / 0.3))
    return finish(mix((0, arp), (0.2, trill), (0.2, bass)))


def s_jump():
    n = int(0.2 * SR)
    t = np.arange(n) / SR
    f = exp_sweep(330, 990, n)
    f[int(0.14 * SR):] = 990
    return finish(pulse(f, 0.25, np.exp(-t / 0.12)))


def s_double_jump():
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    sw = pulse(exp_sweep(500, 1500, n), 0.25, np.exp(-t / 0.1))
    spark = note_seq([88, 92, 95, 100], 0.125, 0.034, tau=0.05, vol=0.7)
    return finish(mix((0, sw), (0.1, spark)))


def s_flip():
    n = int(0.38 * SR)
    t = np.arange(n) / SR
    f = 650 * (1 + 0.55 * np.sin(TAU * 2.8 * t - np.pi / 2) + 0.55)
    env = np.sin(np.pi * t / t[-1]) ** 0.7
    tone = pulse(f, 0.125, env * 0.8)
    wh = noise(n, np.round(5 + 3 * np.cos(TAU * 2.8 * t)), env * 0.6)
    return finish(tone + wh * 0.6)


def s_turn():
    n = int(0.26 * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / t[-1])
    wh = noise(n, np.round(8 - 5 * np.sin(np.pi * t / t[-1])), env)
    tone = pulse(exp_sweep(900, 500, n), 0.125, env * 0.35)
    return finish(wh * 0.7 + tone)


def s_charge_loop():
    """1 秒無縫循環：所有調變都是整數圈，環狀濾波，頭尾完全接得上。"""
    n = SR
    t = np.arange(n) / SR
    duty = 0.125 + 0.2 * (0.5 + 0.5 * np.sin(TAU * 8 * t))
    f1 = 110.0 * (1 + 0.03 * np.sin(TAU * 8 * t))
    a = nes.pulse_wave(f1, duty, SR) * (0.6 + 0.25 * np.sin(TAU * 8 * t))
    b = nes.pulse_wave(np.full(n, 165.0), 0.25, SR) * 0.3
    nz = nes.noise_wave(np.full(n, 7), n, SR) * (0.25 + 0.2 * np.sin(TAU * 8 * t + 1.0))
    x = a + b + nz * 0.5
    return nes.circular_post(x, SR, SR, hp=50.0)


def s_charge_level():
    arp = note_seq([84, 88, 91], 0.25, 0.04, tau=0.05)
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    tail = pulse(nes.hz(96) * (1 + 0.01 * np.sin(TAU * 12 * t)), 0.125, np.exp(-t / 0.1) * 0.7)
    return finish(mix((0, arp), (0.12, tail)))


def s_flame():
    n = int(0.75 * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(5)
    crackle = 0.6 + 0.4 * rng.random(int(0.75 * nes.FRAME_HZ) + 2)
    env = np.minimum(t / 0.05, 1) * np.exp(-t / 0.35)
    nz = noise(n, np.round(10 - 6 * t / t[-1]), env * nes.frames_to_samples(crackle, n, SR))
    rise = pulse(exp_sweep(200, 800, n), 0.125, env * 0.4)
    return finish(nz + rise)


def s_launch():
    n = int(0.65 * SR)
    t = np.arange(n) / SR
    nz = noise(n, np.round(4 + 8 * t / t[-1]), np.exp(-t / 0.22))
    sw = pulse(exp_sweep(200, 2000, n), 0.25, np.exp(-t / 0.15) * 0.6)
    boom = tri(nes.hz(48 - 20 * np.clip(t / 0.2, 0, 1)), np.exp(-t / 0.18))
    return finish(np.tanh((nz + sw + boom * 1.2) * 1.2))


def s_rescue():
    parts = []
    base = [72, 76, 79, 84, 88, 91]
    for c in range(4):
        notes = [m + 2 * c for m in base]
        parts.append((c * 0.16, note_seq(notes, 0.125, 0.026, tau=0.03, vol=1 - 0.15 * c)))
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    shim = pulse(exp_sweep(3000, 900, n), 0.125, np.exp(-t / 0.2) * 0.4)
    parts.append((0.64, shim))
    return finish(mix(*parts), lp=10000)


def s_impact_big():
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    thud = tri(nes.hz(48 - 24 * np.clip(t / 0.25, 0, 1)), np.exp(-t / 0.2))
    nz = noise(n, np.where(t < 0.03, 3, 14), np.exp(-t / 0.18))
    grit = pulse(np.full(n, 80.0), 0.5, np.exp(-t / 0.06) * 0.7)
    return finish(np.tanh((thud * 1.3 + nz + grit) * 1.4))


def s_burst_drop():
    rng = np.random.default_rng(9)
    parts = []
    for i in range(10):
        at = 0.02 + i * 0.055 + rng.uniform(-0.015, 0.015)
        m0 = 94 - i * 1.6 + rng.uniform(-3, 3)
        n = int(0.07 * SR)
        f = exp_sweep(nes.hz(m0), nes.hz(m0 - 10), n)
        parts.append((at, pulse(f, [0.125, 0.25, 0.5][i % 3], decay_env(n, 0.03) * (1 - i * 0.05))))
        tk = noise(int(0.01 * SR), 1, np.linspace(1, 0, int(0.01 * SR)) * 0.5)
        parts.append((at, tk))
    return finish(mix(*parts))


def s_milestone():
    hits = [(0.0, 79, 76, 0.09), (0.11, 79, 76, 0.09), (0.22, 84, 79, 0.55)]
    parts = []
    for at, top, low, d in hits:
        n = int(d * SR)
        t = np.arange(n) / SR
        vib = 1 + 0.007 * np.sin(TAU * 6 * t) * np.clip((t - 0.12) / 0.1, 0, 1)
        env = np.minimum(t / 0.004, 1) * np.where(t > d - 0.03, np.clip((d - t) / 0.03, 0, 1), 1) * (np.exp(-t / 0.6))
        parts.append((at, pulse(nes.hz(top) * vib, 0.25, env)))
        parts.append((at, pulse(nes.hz(low) * vib, 0.5, env * 0.6)))
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    parts.append((0.22, tri(np.full(n, nes.hz(60)), np.exp(-t / 0.5))))
    return finish(mix(*parts))


def s_petal():
    a = fm_bell(nes.hz(96), 0.7, ratio=3.5, index=1.5, tau=0.25)
    b = fm_bell(nes.hz(103), 0.6, ratio=3.5, index=1.2, tau=0.2) * 0.6
    return finish(mix((0, a), (0.09, b)), hp=300)


def s_splash():
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    nz = noise(n, np.round(3 + 6 * t / t[-1]), np.exp(-t / 0.12), steppy=False)
    parts = [(0, nz)]
    for i, (at, f0) in enumerate(((0.12, 500), (0.2, 650), (0.27, 420), (0.33, 760))):
        m = int(0.04 * SR)
        tt = np.arange(m) / SR
        parts.append((at, np.sin(TAU * np.cumsum(exp_sweep(f0, f0 * 2.4, m)) / SR) * np.exp(-tt / 0.015) * 0.5))
    return finish(mix(*parts), lp=9000)


# ---------- 物件專屬音 ----------

def s_orange():
    n1 = int(0.035 * SR)
    pop = pulse(exp_sweep(700, 1500, n1), 0.125, decay_env(n1, 0.02))
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    depth = 0.28 * np.exp(-t / 0.15)
    f = 400 * (1 + 0.15 * t) * (1 + depth * np.sin(TAU * 13 * t))
    boing = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.2) * np.minimum(t / 0.004, 1)
    boing2 = tri(frame_steps(f * 2), np.exp(-t / 0.15) * 0.3)
    return finish(mix((0, pop), (0.03, boing + boing2)))


def s_curry():
    parts = []
    for at, f0 in ((0.0, 180), (0.09, 240), (0.2, 160), (0.27, 280), (0.4, 200)):
        m = int(0.06 * SR)
        tt = np.arange(m) / SR
        parts.append((at, np.sin(TAU * np.cumsum(exp_sweep(f0, f0 * 2.6, m)) / SR) * np.exp(-tt / 0.02)))
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    parts.append((0, tri(np.full(n, nes.hz(43)), np.exp(-t / 0.2) * 0.25)))
    return finish(mix(*parts), hp=60)


def s_snack():
    rng = np.random.default_rng(12)
    parts = []
    for burst0 in (0.0, 0.14):
        for k in range(7):
            at = burst0 + rng.uniform(0, 0.07)
            m = int(rng.uniform(0.003, 0.009) * SR)
            parts.append((at, noise(m, int(rng.integers(0, 4)), np.linspace(1, 0, m) * rng.uniform(0.5, 1.0), steppy=False)))
    return finish(mix(*parts), hp=600)


def s_crayon():
    n = int(0.24 * SR)
    t = np.arange(n) / SR
    f = 2300 * (1 + 0.05 * np.sin(TAU * 38 * t) + 0.08 * t)
    stick = 0.6 + 0.4 * np.maximum(np.sin(TAU * 38 * t), 0)
    env = np.minimum(t / 0.02, 1) * np.minimum((t[-1] - t) / 0.04, 1)
    return finish(pulse(f, 0.125, env * stick, steppy=False) * 0.8, lp=8000)


def s_yarn():
    rng = np.random.default_rng(13)
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    puff = voice.bandpass_noise(n, 200, 1200, SR, rng) * np.minimum(t / 0.015, 1) * np.exp(-t / 0.06)
    puff /= np.max(np.abs(puff)) or 1
    thump = np.sin(TAU * np.cumsum(exp_sweep(190, 120, n)) / SR) * np.minimum(t / 0.01, 1) * np.exp(-t / 0.05)
    return finish(puff * 0.6 + thump * 0.7, hp=60)


def s_bug():
    parts = []
    for at in (0.0, 0.18):
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        am = 0.5 + 0.5 * np.tanh(6 * np.sin(TAU * 45 * t))
        f = 4800 * (1 + 0.02 * np.sin(TAU * 45 * t))
        env = np.minimum(t / 0.01, 1) * np.minimum((t[-1] - t) / 0.02, 1)
        parts.append((at, np.sin(TAU * np.cumsum(f) / SR) * am * env))
    return finish(mix(*parts), hp=800)


def s_bike_bell():
    def ring():
        return bell_tone(2650, 0.7, ratios=(1.0, 1.42, 2.08, 2.66), decays=(1.0, 0.7, 0.45, 0.3), amps=(1, 0.6, 0.4, 0.25), beat=9.0)
    return finish(mix((0, ring()), (0.17, ring() * 0.85)), hp=500)


def s_car_horn():
    parts = []
    for at, d in ((0.0, 0.12), (0.18, 0.16)):
        n = int(d * SR)
        t = np.arange(n) / SR
        droop = 1 - 0.03 * np.clip((t - d + 0.05) / 0.05, 0, 1)
        env = np.minimum(t / 0.008, 1) * np.minimum((d - t) / 0.015, 1)
        parts.append((at, pulse(415 * droop, 0.5, env * 0.8) + pulse(523 * droop, 0.25, env * 0.6)))
    return finish(mix(*parts))


def s_train_horn():
    n = int(0.95 * SR)
    t = np.arange(n) / SR
    env = np.minimum(t / 0.06, 1) * np.minimum((t[-1] - t) / 0.25, 1)
    vib = 1 + 0.004 * np.sin(TAU * 5 * t)
    x = np.zeros(n)
    for m, det in ((69, 1.0), (73, 1.003), (76, 0.997)):
        f = nes.hz(m) * det * vib
        x += pulse(f, 0.25, env * 0.5, steppy=False) + pulse(f * 1.004, 0.5, env * 0.3, steppy=False)
    return finish(x, lp=5000)


def s_school_bell():
    """西敏寺鐘聲前兩句（E C D G｜G D E C），柔和的電子鐘音色。"""
    phrase = [76, 72, 74, 67, 67, 74, 76, 72]
    parts = []
    for i, m in enumerate(phrase):
        at = i * 0.34 + (0.12 if i >= 4 else 0)
        tone = fm_bell(nes.hz(m), 1.4, ratio=2.0, index=1.2, tau=0.55)
        parts.append((at, tone))
        parts.append((at, 0.25 * fm_bell(nes.hz(m + 12), 0.8, ratio=3.5, index=0.8, tau=0.25)))
    return finish(mix(*parts), hp=120)


def s_bubble():
    m = int(0.09 * SR)
    tt = np.arange(m) / SR
    a = np.sin(TAU * np.cumsum(exp_sweep(320, 1100, m)) / SR) * np.exp(-tt / 0.03) * np.minimum(tt / 0.003, 1)
    b = np.sin(TAU * np.cumsum(exp_sweep(500, 1500, m)) / SR) * np.exp(-tt / 0.02) * 0.5
    return finish(mix((0, a), (0.07, b)), hp=150)


def s_squeak():
    n = int(0.24 * SR)
    t = np.arange(n) / SR
    contour = np.interp(t, [0, 0.08, 0.24], [900, 1500, 1150])
    f = contour * (1 + 0.02 * np.sin(TAU * 30 * t))
    env = np.minimum(t / 0.015, 1) * np.minimum((t[-1] - t) / 0.03, 1)
    return finish(pulse(f, 0.25, env, steppy=False), lp=4000, hp=500)


def s_bell():
    parts = []
    for at, m in ((0.0, 96), (0.13, 100), (0.29, 103), (0.42, 98)):
        parts.append((at, bell_tone(nes.hz(m), 1.0, ratios=(1.0, 2.76, 5.4), decays=(1.0, 0.5, 0.3), amps=(1, 0.4, 0.2)) * 0.8))
    return finish(mix(*parts), hp=600)


# ---------- 清單 ----------

SOUNDS = {
    "pop": (s_pop, 0.8), "ding": (s_ding, 0.7), "chirp": (s_chirp, 0.7), "pickup": (s_pickup, 0.6),
    "pickup_big": (s_pickup_big, 0.7), "bump": (s_bump, 0.8), "drop": (s_drop, 0.65), "tick": (s_tick, 0.6),
    "goal": (s_goal, 0.85), "timeup": (s_timeup, 0.7), "dash": (s_dash, 0.7), "ui": (s_ui, 0.5),
    "gate": (s_gate, 0.7), "cheer": (s_cheer, 0.75), "jump": (s_jump, 0.65), "double_jump": (s_double_jump, 0.7),
    "flip": (s_flip, 0.6), "turn": (s_turn, 0.55), "charge_loop": (s_charge_loop, 0.6),
    "charge_level": (s_charge_level, 0.6), "flame": (s_flame, 0.7), "launch": (s_launch, 0.85),
    "rescue": (s_rescue, 0.7), "impact_big": (s_impact_big, 0.9), "burst_drop": (s_burst_drop, 0.7),
    "milestone": (s_milestone, 0.7), "petal": (s_petal, 0.3), "splash": (s_splash, 0.7),
    "orange": (s_orange, 0.75), "curry": (s_curry, 0.7), "snack": (s_snack, 0.65), "crayon": (s_crayon, 0.5),
    "yarn": (s_yarn, 0.55), "bug": (s_bug, 0.45), "bike_bell": (s_bike_bell, 0.6), "car_horn": (s_car_horn, 0.65),
    "train_horn": (s_train_horn, 0.7), "school_bell": (s_school_bell, 0.6), "bubble": (s_bubble, 0.6),
    "squeak": (s_squeak, 0.55), "bell": (s_bell, 0.4),
    "meow": (lambda: voice.meow(SR), 0.7), "woof": (lambda: voice.woof(SR), 0.75),
    "duck": (lambda: voice.duck(SR), 0.65), "chicken": (lambda: voice.chicken(SR), 0.65),
    "frog": (lambda: voice.frog(SR), 0.6),
    "cheer_gin_1": (lambda: voice.cheer_gin(1, SR), 0.85), "cheer_gin_2": (lambda: voice.cheer_gin(2, SR), 0.85),
    "cheer_gin_3": (lambda: voice.cheer_gin(3, SR), 0.85),
}


def trim_tail(x, floor_db=-60.0, keep=0.02):
    """去掉結尾低於 floor_db 的靜音（保留一點點淡出）。"""
    m = np.max(np.abs(x)) or 1.0
    above = np.nonzero(np.abs(x) > m * 10 ** (floor_db / 20))[0]
    if len(above) == 0:
        return x
    end = min(len(x), above[-1] + int(keep * SR))
    return nes.fade_edges(x[:end], SR, 0.0, min(0.01, keep))


def main_all(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for name, (fn, peak) in SOUNDS.items():
        data = fn()
        if name != "charge_loop":
            data = nes.fade_edges(trim_tail(data), SR, 0.0015, 0.0)
        nes.write_wav(out / f"{name}.wav", data, SR, peak)
        print(f"[sfx] {name}.wav  {len(data) / SR:.2f} 秒")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main_all(Path(args[0]) if args else Path(__file__).resolve().parents[2] / "godot" / "assets" / "audio")
