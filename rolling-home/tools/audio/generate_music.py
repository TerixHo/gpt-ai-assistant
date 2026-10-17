#!/usr/bin/env python3
"""合成全部配樂（紅白機晶片音樂風格），預設也一併重新產生全部音效與歡呼語音。

用法：
    python3 tools/audio/generate_music.py [輸出資料夾] [--music-only | --sfx-only]
預設輸出到 godot/assets/audio。只需要 numpy。

曲目（全部 22050 Hz 單聲道、以小節為單位無縫循環）：
    music_title.wav    標題畫面      150 BPM  C 大調  32 小節
    music_home.wav     第 1 關冬山的家  140 BPM  F 大調  32 小節
    music_street.wav   第 2 關上學的路  150 BPM  G 大調  24 小節
    music_school.wav   第 3 關學校與街區 156 BPM  D 大調  24 小節
    music_station.wav  第 4 關往火車站  168 BPM  A 大調  32 小節

風格參考：任天堂紅白機時代的射擊與動作遊戲配樂（例如兵蜂、高橋名人冒險島）那種明亮、跳躍的晶片音樂：
兩個脈衝波彈主旋律與和聲（或琶音、回音），三角波彈八度跳躍的低音，雜訊做鼓組，音量與顫音以影格為單位變化。
聲明：所有旋律、和聲進行與編曲都是本專案原創，沒有引用或改寫上述遊戲或其他作品的任何旋律。
唯一的引用是第 3 關 B 段開頭的西敏寺鐘聲（Westminster Quarters，1793 年，屬公眾領域），代表學校鐘聲。

音源模擬見 nes.py。每首曲子在 44.1 kHz 合成後，整首當成循環訊號用 FFT 做濾波與降取樣，
所以循環點沒有接縫；超出最後一小節的音符尾巴會接回開頭。
"""
import sys
from pathlib import Path

import numpy as np

import nes

SR = 44100
OUT_SR = 22050
NOTE_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MAJOR = [0, 2, 4, 5, 7, 9, 11]


def note_midi(name):
    """"C#5"、"Bb4" 轉 MIDI 音高。"""
    pc = NOTE_NAMES[name[0]]
    rest = name[1:]
    while rest and rest[0] in "#b":
        pc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return pc + 12 * (int(rest) + 1)


def chord_tones(name):
    """和弦名稱轉 (根音音級, [音程...])：支援大三、小三、屬七、小七。"""
    pc = NOTE_NAMES[name[0]]
    q = name[1:]
    if q.startswith("#") or q.startswith("b"):
        pc += 1 if q[0] == "#" else -1
        q = q[1:]
    pc %= 12
    if q == "m":
        return pc, [0, 3, 7]
    if q == "m7":
        return pc, [0, 3, 7, 10]
    if q == "7":
        return pc, [0, 4, 7, 10]
    return pc, [0, 4, 7]


def parse_bar(text):
    """一小節的旋律："C5:2 E5:2 r:4 ..."，長度單位是十六分音符，總和必須是 16。"""
    out = []
    pos = 0
    for tok in text.split():
        n, l = tok.split(":")
        l = int(l)
        if n != "r":
            out.append((pos, l, note_midi(n)))
        pos += l
    assert pos == 16, f"小節長度不是 16：{text}（{pos}）"
    return out


class Song:
    def __init__(self, bpm, chords, key_pc):
        self.bpm = bpm
        self.step_s = 60.0 / bpm / 4
        self.chords = [c.split("|") for c in chords]
        self.bars = len(chords)
        self.steps = self.bars * 16
        n = int(round(self.steps * self.step_s * SR))
        self.n = n - (n % 2)
        self.key_pc = key_pc
        pad = int(3 * SR)
        self.buf = {k: np.zeros(self.n + pad) for k in ("p1", "p2", "tri", "noise")}
        self.lead = []      # (step, length, midi)
        self.p2 = []        # (step, length, midi or list, kind, params)
        self.tri = []       # (step, length, midi, kind)
        self.drums = []     # (step, kind)

    def at(self, step):
        return int(round(step * self.step_s * SR))

    def chord_at(self, step):
        bar = (step // 16) % self.bars
        parts = self.chords[bar]
        half = 0 if len(parts) == 1 else min((step % 16) // (16 // len(parts)), len(parts) - 1)
        return parts[half]

    # ---------- 寫入樂句 ----------

    def melody(self, bar0, bars):
        for i, text in enumerate(bars):
            for pos, l, m in parse_bar(text):
                self.lead.append(((bar0 + i) * 16 + pos, l, m))

    def drum_bars(self, bar0, patterns):
        for i, pat in enumerate(patterns):
            assert len(pat) == 16, pat
            for s, ch in enumerate(pat):
                if ch != ".":
                    self.drums.append(((bar0 + i) * 16 + s, ch))

    # ---------- 自動伴奏 ----------

    def bass(self, bar0, nbars, style):
        for b in range(bar0, bar0 + nbars):
            for s in range(16):
                step = b * 16 + s
                pc, iv = chord_tones(self.chord_at(step))
                root = 36 + pc
                if root > 43:
                    root -= 12
                fifth = root + 7
                if style == "octave":
                    if s % 2 == 0:
                        m = root if (s // 2) % 2 == 0 else root + 12
                        if s == 14:
                            m = fifth
                        self.tri.append((step, 2, m, "bass"))
                elif style == "walk":
                    if s % 4 == 0:
                        seq = [root, root + iv[1], root + 12, fifth]
                        self.tri.append((step, 3, seq[s // 4], "bass"))
                elif style == "bounce":
                    pat = {0: (root, 3), 3: (root + 12, 1), 4: (fifth, 2), 6: (root + 12, 2),
                           8: (root, 3), 11: (root + 12, 1), 12: (fifth, 2), 14: (root + iv[1] + 12, 2)}
                    if s in pat:
                        m, l = pat[s]
                        self.tri.append((step, l, m, "bass"))
                elif style == "drive":
                    if s % 2 == 0:
                        seq = [root, root, root + 12, root, root, root + 12, fifth, root + 12]
                        self.tri.append((step, 2, seq[s // 2], "bass"))
                    elif s == 15:
                        self.tri.append((step, 1, root + 12, "bass"))
                elif style == "half":
                    if s % 8 == 0:
                        self.tri.append((step, 7, root if s == 0 else fifth, "bass"))

    def arp(self, bar0, nbars, rhythm="8ths", vol=7):
        """紅白機招牌的影格琶音：每一影格換一個和弦音，聽起來像閃爍的和弦。"""
        hits = {"8ths": range(0, 16, 2), "off": (2, 6, 10, 14), "quarters": range(0, 16, 4),
                "push": (0, 3, 6, 8, 11, 14)}[rhythm]
        for b in range(bar0, bar0 + nbars):
            for s in hits:
                step = b * 16 + s
                pc, iv = chord_tones(self.chord_at(step))
                base = 60 + pc
                if base > 66:
                    base -= 12
                notes = [base + i for i in iv[:3]] + [base + 12]
                self.p2.append((step, 2 if rhythm != "quarters" else 3, notes, "arp", {"vol": vol}))

    def harmony(self, bar0, nbars, vol=8):
        """主旋律下方三度（依調內音階）。"""
        lo, hi = bar0 * 16, (bar0 + nbars) * 16
        scale = [(self.key_pc + d) % 12 for d in MAJOR]
        for step, l, m in self.lead:
            if not lo <= step < hi:
                continue
            pc = m % 12
            if pc in scale:
                deg = scale.index(pc)
                down = (scale[deg] - scale[(deg - 2) % 7]) % 12
                h = m - down
            else:
                h = m - 4
            self.p2.append((step, l, h, "harm", {"vol": vol}))

    def echo(self, bar0, nbars, delay=3, vol=6):
        """回音：主旋律延遲幾個十六分音符、音量變小，像當年用第二個聲道做的延遲效果。"""
        lo, hi = bar0 * 16, (bar0 + nbars) * 16
        for step, l, m in self.lead:
            if lo <= step < hi:
                self.p2.append((step + delay, l, m, "echo", {"vol": vol}))

    def pad(self, bar0, nbars, vol=6):
        """長音襯底：每半小節一個和弦內音（第三音），慢慢顫音。"""
        for b in range(bar0, bar0 + nbars):
            for s in (0, 8):
                step = b * 16 + s
                pc, iv = chord_tones(self.chord_at(step))
                m = 60 + (pc + iv[1]) % 12
                if m > 67:
                    m -= 12
                self.p2.append((step, 8, m, "pad", {"vol": vol}))

    # ---------- 合成 ----------

    def _place(self, ch, start_sample, sig):
        buf = self.buf[ch]
        end = min(start_sample + len(sig), len(buf))
        buf[start_sample:end] += sig[:end - start_sample]

    def _segments(self, events):
        """單音聲道：每個事件最多響到下一個事件開始。"""
        events = sorted(events, key=lambda e: e[0])
        out = []
        for i, e in enumerate(events):
            nxt = events[i + 1][0] if i + 1 < len(events) else e[0] + 64
            out.append((e, nxt))
        return out

    def render(self, lead_duty=25, lead_vib=0.16, lead_bend=False, p2_duty=12, swing=0.0):
        sp = self.step_s
        fs = SR / nes.FRAME_HZ

        def step_time(step):
            # 搖擺：偶數十六分音符後的那一拍稍微延後
            return step + (swing if step % 2 == 1 else 0.0)

        # 主旋律
        for (step, l, m), nxt in self._segments(self.lead):
            start = self.at(step_time(step))
            avail = self.at(step_time(nxt)) - start
            gate_s = l * sp - min(0.03, l * sp * 0.25)
            seg = min(avail, int((gate_s + 0.06) * SR))
            nf = int(seg / fs) + 2
            f = np.arange(nf)
            pitch = np.full(nf, float(m))
            if l >= 3:
                d = 9
                pitch += np.where(f > d, lead_vib * np.sin(nes.TAU * 6.0 * (f - d) / nes.FRAME_HZ), 0.0)
            if lead_bend and l >= 4:
                pitch -= np.clip(1 - f / 4.0, 0, 1) * 1.0
            gate_f = gate_s * nes.FRAME_HZ
            vol = nes.env_frames(nf, 13, 9 if l >= 3 else 8, 2.0, release_at=gate_f, release_frames=3)
            freq = nes.frames_to_samples(nes.nes_pulse_hz(nes.hz(pitch)), seg, SR)
            v = nes.frames_to_samples(nes.quant_vol(vol), seg, SR)
            duty = nes.DUTIES[lead_duty]
            sig = nes.pulse_wave(freq, duty, SR) * v
            self._place("p1", start, nes.fade_edges(sig, SR, 0.0005, 0.003))

        # 第二脈衝波：琶音、和聲、回音、襯底
        for (step, l, m, kind, prm), nxt in self._segments(self.p2):
            start = self.at(step_time(step))
            avail = self.at(step_time(nxt)) - start
            gate_s = l * sp - 0.02
            seg = min(avail, int((gate_s + 0.05) * SR))
            if seg <= 8:
                continue
            nf = int(seg / fs) + 2
            f = np.arange(nf)
            vmax = prm.get("vol", 7)
            if kind == "arp":
                notes = np.array(m, dtype=float)
                pitch = notes[f % len(notes)]
                vol = nes.env_frames(nf, vmax, 2, 1.5, release_at=gate_s * nes.FRAME_HZ)
                duty = 0.125
            elif kind == "pad":
                pitch = m + np.where(f > 12, 0.12 * np.sin(nes.TAU * 5.0 * (f - 12) / nes.FRAME_HZ), 0.0)
                vol = nes.env_frames(nf, vmax, vmax - 2, 6.0, release_at=gate_s * nes.FRAME_HZ, release_frames=4)
                duty = 0.5
            else:
                pitch = np.full(nf, float(m))
                if l >= 3:
                    pitch += np.where(f > 9, 0.12 * np.sin(nes.TAU * 6.0 * (f - 9) / nes.FRAME_HZ), 0.0)
                vol = nes.env_frames(nf, vmax, max(vmax - 3, 2), 2.0, release_at=gate_s * nes.FRAME_HZ)
                duty = nes.DUTIES[p2_duty] if kind == "echo" else 0.5 if kind == "harm" else 0.25
            freq = nes.frames_to_samples(nes.nes_pulse_hz(nes.hz(pitch)), seg, SR)
            v = nes.frames_to_samples(nes.quant_vol(vol), seg, SR)
            sig = nes.pulse_wave(freq, duty, SR) * v
            self._place("p2", start, nes.fade_edges(sig, SR, 0.0005, 0.003))

        # 三角波：低音與大鼓共用（大鼓會打斷低音，跟當年一樣）。
        # 大鼓約 0.06 秒，低音音符被大鼓蓋到的部分切掉，大鼓一結束就接著響。
        kick_len = 0.06 / sp
        kicks = sorted(step for step, ch in self.drums if ch in "kKC")
        resumed = [(k, kick_len, 0, "kick") for k in kicks]
        for step, l, m, kind in self.tri:
            pieces = [(float(step), float(step + l))]
            for k in kicks:
                nxt_pieces = []
                for a, b in pieces:
                    if k + kick_len <= a or k >= b:
                        nxt_pieces.append((a, b))
                        continue
                    if k > a:
                        nxt_pieces.append((a, k))
                    if k + kick_len < b:
                        nxt_pieces.append((k + kick_len, b))
                pieces = nxt_pieces
            for a, b in pieces:
                if b - a > 0.2:
                    resumed.append((a, b - a, m, kind))
        for (step, l, m, kind), nxt in self._segments(resumed):
            start = self.at(step_time(step))
            avail = self.at(step_time(nxt)) - start
            if kind == "kick":
                seg = min(avail, int(0.09 * SR))
                t = np.arange(seg) / SR
                pitch = 52 - 30 * np.clip(t / 0.06, 0, 1)
                freq = nes.nes_tri_hz(nes.hz(pitch))
                sig = nes.triangle_wave(freq, SR) * 1.1
            else:
                gate_s = l * sp - 0.025
                seg = min(avail, int(gate_s * SR))
                freq = np.full(seg, nes.nes_tri_hz(nes.hz(m)))
                sig = nes.triangle_wave(freq, SR)
            if seg <= 8:
                continue
            self._place("tri", start, nes.fade_edges(sig, SR, 0.0008, 0.003))

        # 雜訊：小鼓、鈸、碎音鈸，和大鼓的「咚」
        for (step, ch), nxt in self._segments(self.drums):
            start = self.at(step_time(step))
            avail = self.at(step_time(nxt)) - start
            spec = {
                "k": (12, 11, 0.05, False), "K": (12, 13, 0.06, False),
                "s": (6, 12, 0.13, False), "S": (5, 15, 0.16, False),
                "h": (1, 5, 0.035, False), "o": (1, 7, 0.16, False),
                "C": (3, 12, 0.6, False), "c": (2, 10, 0.5, False),
                "t": (0, 8, 0.05, True),
            }.get(ch)
            if spec is None:
                continue
            per, v0, dur, short = spec
            seg = min(avail, int(dur * SR))
            if seg <= 8:
                continue
            nf = int(seg / (SR / nes.FRAME_HZ)) + 2
            vol = np.maximum(v0 - np.arange(nf) * (v0 / max(dur * nes.FRAME_HZ, 1)), 0)
            per_f = np.full(nf, per, dtype=float)
            if ch in "sS":
                per_f[:2] = per - 3  # 小鼓開頭比較尖
            v = nes.frames_to_samples(nes.quant_vol(vol), seg, SR)
            p = nes.frames_to_samples(per_f, seg, SR)
            sig = nes.noise_wave(p, seg, SR, short=short, offset=start) * v
            self._place("noise", start, nes.fade_edges(sig, SR, 0.0003, 0.004))

    def mixdown(self, levels=None):
        lv = {"p1": 0.26, "p2": 0.2, "tri": 0.34, "noise": 0.2}
        lv.update(levels or {})
        mix = sum(self.buf[k] * lv[k] for k in self.buf)
        # 超過結尾的尾巴接回開頭（循環無縫）
        tail = mix[self.n:]
        mix = mix[:self.n].copy()
        k = min(len(tail), self.n)
        mix[:k] += tail[:k]
        mix = np.tanh(mix * 1.6) / 1.6
        return nes.circular_post(mix, SR, OUT_SR, hp=35.0)


def drums_for(section, nbars, fill=None):
    pats = [section[i % len(section)] for i in range(nbars)]
    if fill:
        pats[-1] = fill
    return pats


# ---------- 曲目（全部原創） ----------

def song_title():
    chords = ["C", "G", "Am", "F", "C", "G", "F|G", "C",
              "Am", "F", "Dm", "G", "Am", "F", "Dm|G", "G",
              "C", "G", "Am", "F", "C", "G", "F|G", "C",
              "F", "G", "Em", "Am", "F", "G", "Dm7|G", "G7"]
    s = Song(150, chords, 0)
    A = ["G4:2 C5:2 E5:2 G5:4 E5:2 C5:2 E5:2",
         "D5:2 G5:2 B5:4 A5:2 G5:2 D5:4",
         "C5:2 E5:2 A5:4 G5:2 E5:2 C5:2 E5:2",
         "F5:6 E5:2 D5:2 C5:2 A4:4",
         "G4:2 C5:2 E5:2 G5:4 A5:2 G5:2 E5:2",
         "F5:2 E5:2 D5:4 G5:4 B4:4",
         "A4:2 C5:2 F5:4 G5:2 B5:2 D6:4"]
    s.melody(0, A + ["C6:6 G5:2 C5:4 r:4"])
    s.melody(8, ["E5:3 E5:3 A5:2 G5:2 E5:2 D5:4",
                 "C5:3 C5:3 F5:2 E5:2 C5:2 A4:4",
                 "D5:2 F5:2 A5:2 F5:2 D6:4 C6:4",
                 "B5:2 A5:2 G5:2 F5:2 D5:4 B4:4",
                 "E5:3 E5:3 A5:2 B5:2 C6:2 A5:4",
                 "F5:2 A5:2 C6:2 A5:2 F5:4 E5:4",
                 "D5:2 F5:2 A5:4 G5:2 B5:2 D6:2 F6:2",
                 "G6:4 r:2 G5:2 G5:2 A5:2 B5:4"])
    s.melody(16, A + ["C6:4 E6:4 G6:4 C6:4"])
    s.melody(24, ["A5:1 r:1 A5:1 r:1 C6:2 A5:2 G5:2 F5:2 E5:4",
                  "B5:1 r:1 B5:1 r:1 D6:2 B5:2 A5:2 G5:2 D5:4",
                  "G5:2 E5:2 B4:2 E5:2 G5:2 B5:2 E6:4",
                  "C6:2 B5:2 A5:2 E5:2 C5:4 E5:4",
                  "F5:4 A5:4 C6:4 F6:4",
                  "E6:2 D6:2 C6:2 B5:2 A5:2 G5:2 F5:2 D5:2",
                  "D5:4 F5:4 G5:4 B5:4",
                  "D6:2 C6:2 B5:2 A5:2 G5:2 F5:2 E5:2 D5:2"])
    s.bass(0, 32, "octave")
    s.arp(0, 8, "off")
    s.echo(8, 8, delay=3)
    s.harmony(16, 8)
    s.arp(24, 8, "8ths", vol=6)
    beat = ["K.h.s.h.k.h.s.hh", "k.h.s.h.k.k.s.h."]
    s.drum_bars(0, ["C.h.s.h.k.h.s.hh"] + drums_for(beat, 8, "k.h.s.h.s.s.SSSS")[1:])
    s.drum_bars(8, ["C.hhs.hhk.hhs.hh"] + drums_for(["k.hhs.hhk.hhs.hh", "k.hhs.hkk.hhs.hh"], 8, "s.s.s.s.ssssSSSS")[1:])
    s.drum_bars(16, ["C.h.s.h.k.h.s.hh"] + drums_for(beat, 8, "k.h.s.h.s.s.SSSS")[1:])
    s.drum_bars(24, ["C...s...k...s..."] + drums_for(["k.h.s.h.k.h.s.h.", "k.hhs.hkk.hhs.hh"], 8, "SSs.SSs.ssssSSSS")[1:])
    s.render(lead_duty=25, lead_bend=True)
    return s.mixdown()


def song_home():
    chords = ["F", "C", "Dm", "Bb", "F", "C", "Bb|C", "F",
              "Bb", "F", "Gm", "C", "Am", "Dm", "Gm|C", "C7",
              "F", "C", "Dm", "Bb", "F", "C", "Bb|C", "F",
              "Dm", "Am", "Bb", "F", "Gm", "C", "Bb|C", "C7"]
    s = Song(140, chords, 5)
    A = ["C5:2 A4:2 C5:2 F5:4 E5:2 F5:2 A5:2",
         "G5:4 E5:2 C5:2 D5:2 E5:2 G5:4",
         "F5:2 D5:2 A4:2 D5:2 F5:2 A5:2 G5:4",
         "F5:3 D5:3 Bb4:2 C5:4 r:4",
         "C5:2 A4:2 C5:2 F5:4 G5:2 A5:2 C6:2",
         "Bb5:4 A5:2 G5:2 E5:4 C5:4",
         "D5:2 F5:2 Bb5:4 A5:2 G5:2 E5:4"]
    s.melody(0, A + ["F5:8 r:2 C5:2 D5:2 E5:2"])
    s.melody(8, ["D6:4 C6:2 Bb5:2 F5:4 D5:4",
                 "C6:4 A5:2 F5:2 C5:4 A4:4",
                 "Bb4:2 D5:2 G5:2 Bb5:2 A5:2 G5:2 D5:4",
                 "E5:2 G5:2 C6:2 Bb5:2 A5:2 G5:2 E5:4",
                 "A5:3 G5:3 E5:2 C5:4 E5:4",
                 "F5:3 E5:3 D5:2 A4:4 D5:4",
                 "Bb4:2 D5:2 G5:4 C5:2 E5:2 G5:4",
                 "Bb5:2 A5:2 G5:2 E5:2 C5:2 D5:2 E5:4"])
    s.melody(16, A + ["F5:4 A5:2 C6:2 F6:4 r:4"])
    s.melody(24, ["A5:2 F5:2 D5:2 F5:2 A5:4 D6:4",
                  "C6:2 A5:2 E5:2 A5:2 C6:4 E6:4",
                  "D6:3 C6:3 Bb5:2 F5:4 D5:4",
                  "C5:3 D5:3 F5:2 A5:8",
                  "Bb5:2 A5:2 G5:2 D5:2 G5:4 Bb5:4",
                  "C6:2 Bb5:2 G5:2 E5:2 G5:4 C6:4",
                  "D6:2 C6:2 Bb5:4 G5:2 A5:2 Bb5:4",
                  "C6:4 r:2 G5:2 E5:2 C5:2 E5:2 G5:2"])
    s.bass(0, 32, "bounce")
    s.arp(0, 8, "off", vol=7)
    s.harmony(8, 8, vol=7)
    s.echo(16, 8, delay=2, vol=5)
    s.pad(24, 8, vol=6)
    beat = ["k.hhs.h.k.hhs.hh", "k.hhs.hkk.hhs.h."]
    s.drum_bars(0, ["C.hhs.h.k.hhs.hh"] + drums_for(beat, 8, "k.hhs.h.s.s.ssSS")[1:])
    s.drum_bars(8, ["C.h.s.h.k.h.s.h."] + drums_for(["k.h.s.h.k.h.s.hh", "k.h.s.hkk.h.s.h."], 8, "s.s.s.s.ssssSSSS")[1:])
    s.drum_bars(16, ["C.hhs.h.k.hhs.hh"] + drums_for(beat, 8, "k.hhs.h.s.s.ssSS")[1:])
    s.drum_bars(24, ["C.h.o.h.k.h.o.h."] + drums_for(["k.h.o.h.k.h.o.h.", "k.h.o.hkk.h.o.h."], 8, "s.s.ssss.sSSsSSS")[1:])
    s.render(lead_duty=50, lead_vib=0.14, swing=0.18)
    return s.mixdown()


def song_street():
    chords = ["G", "Em", "C", "D", "G", "Em", "Am|D", "G",
              "C", "D", "Bm", "Em", "C", "D", "Am|D", "D7",
              "G", "Em", "C", "D", "G", "Em", "Am|D", "G"]
    s = Song(150, chords, 7)
    A = ["D5:2 G5:2 G5:2 A5:2 B5:4 G5:4",
         "E5:2 G5:2 B5:2 A5:2 G5:4 E5:4",
         "C5:2 E5:2 G5:2 C6:2 B5:2 A5:2 G5:4",
         "A5:6 F#5:2 D5:4 r:4",
         "D5:2 G5:2 G5:2 A5:2 B5:2 C6:2 D6:4",
         "B5:2 G5:2 E5:2 G5:2 B5:4 E6:4",
         "C6:2 B5:2 A5:4 F#5:2 G5:2 A5:4"]
    s.melody(0, A + ["G5:8 r:4 D5:2 D5:2"])
    s.melody(8, ["E5:2 E5:2 G5:2 E5:2 C6:4 B5:4",
                 "F#5:2 F#5:2 A5:2 F#5:2 D6:4 C6:4",
                 "B5:3 A5:3 F#5:2 D5:4 F#5:4",
                 "G5:3 F#5:3 E5:2 B4:4 E5:4",
                 "C6:2 B5:2 A5:2 G5:2 E5:2 G5:2 C6:4",
                 "D6:2 C6:2 B5:2 A5:2 F#5:2 A5:2 D6:4",
                 "E6:2 D6:2 C6:4 A5:2 B5:2 C6:4",
                 "D6:4 r:2 A5:2 F#5:2 D5:2 C5:4"])
    s.melody(16, A + ["G5:4 B5:4 D6:4 G6:4"])
    s.bass(0, 24, "walk")
    s.harmony(0, 8, vol=7)
    s.arp(8, 8, "push", vol=7)
    s.echo(16, 8, delay=3, vol=6)
    march = ["k.h.s.h.k.h.s.h.", "k.h.s.h.k.hks.h."]
    s.drum_bars(0, ["C.h.s.h.k.h.s.h."] + drums_for(march, 8, "k.h.s.h.sss.SSSS")[1:])
    s.drum_bars(8, ["C.hhs.hhk.hhs.hh"] + drums_for(["k.hhs.hhk.hhs.hh"], 8, "s.s.s.s.ssssSSSS")[1:])
    s.drum_bars(16, ["C.h.s.h.k.h.s.h."] + drums_for(march, 8, "k.h.s.h.s.s.SSSS")[1:])
    s.render(lead_duty=25, lead_vib=0.15)
    return s.mixdown()


def song_school():
    chords = ["D", "A", "Bm", "G", "D", "A", "G|A", "D",
              "D|A", "A|D", "G", "A", "Bm", "F#m", "G|A", "A7",
              "D", "A", "Bm", "G", "D", "A", "G|A", "D"]
    s = Song(156, chords, 2)
    A = ["A4:2 D5:2 F#5:2 A5:2 F#5:2 D5:2 A5:4",
         "E5:2 A5:2 C#6:2 B5:2 A5:2 E5:2 C#5:4",
         "D5:2 F#5:2 B5:4 A5:2 F#5:2 D5:4",
         "G5:3 F#5:3 E5:2 D5:2 B4:2 D5:4",
         "A4:2 D5:2 F#5:2 A5:2 B5:2 A5:2 D6:4",
         "C#6:2 B5:2 A5:2 E5:2 A5:4 C#6:4",
         "B5:2 A5:2 G5:4 E5:2 F#5:2 G5:4"]
    s.melody(0, A + ["F#5:4 D5:4 A4:4 r:4"])
    # B 段開頭：西敏寺鐘聲（1793 年，公眾領域）當作學校鐘聲
    s.melody(8, ["F#5:4 D5:4 E5:4 A4:4",
                 "A4:4 E5:4 F#5:4 D5:4",
                 "B5:2 G5:2 D5:2 G5:2 B5:2 D6:2 B5:4",
                 "C#6:2 A5:2 E5:2 A5:2 C#6:2 E6:2 C#6:4",
                 "D6:3 C#6:3 B5:2 F#5:4 B5:4",
                 "A5:3 F#5:3 E5:2 C#5:4 F#5:4",
                 "G5:2 B5:2 D6:4 E6:2 C#6:2 A5:4",
                 "A5:2 B5:2 C#6:2 D6:2 E6:4 G5:4"])
    s.melody(16, A + ["D6:4 A5:4 F#5:4 D5:4"])
    s.bass(0, 24, "octave")
    s.echo(0, 8, delay=3, vol=6)
    s.pad(8, 2, vol=7)
    s.arp(10, 6, "8ths", vol=6)
    s.harmony(16, 8, vol=7)
    beat = ["k.hhs.hhk.hhs.hh", "k.hhs.hkk.hhs.ho"]
    s.drum_bars(0, ["C.hhs.hhk.hhs.hh"] + drums_for(beat, 8, "k.hhs.hhs.s.SSSS")[1:])
    s.drum_bars(8, ["C...c...C...c...", "k...c...k...s.h.", "k.h.s.h.k.h.s.h.", "k.h.s.h.k.hks.h.",
                    "k.hhs.hhk.hhs.hh", "k.hhs.hkk.hhs.hh", "k.hhs.hhk.hhs.hh", "s.s.s.s.ssssSSSS"])
    s.drum_bars(16, ["C.hhs.hhk.hhs.hh"] + drums_for(beat, 8, "k.hhs.hhs.s.SSSS")[1:])
    s.render(lead_duty=12, lead_vib=0.18)
    return s.mixdown({"p1": 0.3})


def song_station():
    chords = ["A", "E", "F#m", "D", "A", "E", "D|E", "A",
              "D", "E", "C#m", "F#m", "D", "E", "Bm|E", "E7",
              "A", "E", "F#m", "D", "A", "E", "D|E", "A",
              "A", "D", "E", "A", "F#m", "D", "Bm|E", "E7"]
    s = Song(168, chords, 9)
    A = ["E5:1 r:1 E5:1 r:1 A5:2 C#6:2 B5:2 A5:2 E5:4",
         "B4:1 r:1 B4:1 r:1 E5:2 G#5:2 B5:2 A5:2 G#5:4",
         "A5:2 F#5:2 C#5:2 F#5:2 A5:2 C#6:2 B5:4",
         "A5:3 F#5:3 D5:2 E5:4 F#5:4",
         "E5:1 r:1 E5:1 r:1 A5:2 C#6:2 E6:2 D6:2 C#6:4",
         "B5:2 G#5:2 E5:2 G#5:2 B5:4 E6:4",
         "F#6:2 E6:2 D6:4 E6:2 D6:2 B5:4"]
    s.melody(0, A + ["A5:8 r:2 E5:2 F#5:2 G#5:2"])
    s.melody(8, ["A5:4 F#5:2 D5:2 A5:4 B5:4",
                 "G#5:4 E5:2 B4:2 G#5:4 A5:4",
                 "E5:2 G#5:2 C#6:2 G#5:2 E6:4 C#6:4",
                 "F#5:2 A5:2 C#6:2 A5:2 F#6:4 E6:4",
                 "D6:2 C#6:2 B5:2 A5:2 F#5:2 A5:2 D6:4",
                 "E6:2 D6:2 C#6:2 B5:2 G#5:2 B5:2 E6:4",
                 "D6:2 C#6:2 B5:4 G#5:2 A5:2 B5:4",
                 "E6:4 r:2 B5:2 G#5:2 E5:2 D5:4"])
    s.melody(16, A + ["A5:4 C#6:4 E6:4 A6:4"])
    # C 段：火車汽笛般的長音，鼓組變成「咻咚咻咚」的火車節奏
    s.melody(24, ["A5:6 r:2 A5:6 r:2",
                  "F#5:6 r:2 A5:6 r:2",
                  "G#5:6 r:2 B5:6 r:2",
                  "C#6:12 r:4",
                  "C#6:2 A5:2 F#5:2 A5:2 C#6:2 F#6:2 E6:4",
                  "D6:2 A5:2 F#5:2 A5:2 D6:2 F#6:2 E6:4",
                  "D6:2 C#6:2 B5:4 B5:2 C#6:2 D6:4",
                  "E6:2 D6:2 C#6:2 B5:2 G#5:2 E5:2 F#5:2 G#5:2"])
    s.bass(0, 32, "drive")
    s.arp(0, 8, "off", vol=7)
    s.harmony(8, 8, vol=8)
    s.echo(16, 8, delay=2, vol=6)
    s.harmony(24, 4, vol=8)
    s.arp(28, 4, "8ths", vol=6)
    beat = ["khhhshhhkhkhshhh", "khhhshhkkhhhshkh"]
    s.drum_bars(0, ["Chhhshhhkhkhshhh"] + drums_for(beat, 8, "khhhshhhs.s.SSSS")[1:])
    s.drum_bars(8, ["ChhhShhhkhkhShhh"] + drums_for(["khhhShhhkhkhShhh", "khhhShhkkhhhShkh"], 8, "SsSsSsSsssssSSSS")[1:])
    s.drum_bars(16, ["Chhhshhhkhkhshhh"] + drums_for(beat, 8, "khhhshhhs.s.SSSS")[1:])
    train = ["k.ttk.ttk.ttk.tt", "k.ttk.ttk.ttkstt"]
    s.drum_bars(24, ["C.ttk.ttk.ttk.tt"] + drums_for(train, 8, "SSs.SSs.ssssSSSS")[1:])
    s.render(lead_duty=25, lead_vib=0.17, lead_bend=True)
    return s.mixdown()


SONGS = {
    "title": song_title,
    "home": song_home,
    "street": song_street,
    "school": song_school,
    "station": song_station,
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    out = Path(args[0]) if args else Path(__file__).resolve().parents[2] / "godot" / "assets" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    if "--sfx-only" not in flags:
        for name, fn in SONGS.items():
            data = fn()
            nes.write_wav(out / f"music_{name}.wav", data, OUT_SR, peak=0.88)
            print(f"[music] music_{name}.wav  {len(data) / OUT_SR:.1f} 秒")
    if "--music-only" not in flags:
        import generate_sfx
        generate_sfx.main_all(out)


if __name__ == "__main__":
    main()
