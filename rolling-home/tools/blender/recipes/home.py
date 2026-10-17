"""第 1 關「槿寶的家」的重點模型配方（由 tools/blender/generate_props.py 自動載入）。

產生：在 rolling-home 執行
    /opt/build/bpyenv/bin/python tools/blender/generate_props.py godot/assets/models/props hm_curry_pot hm_car ...
建模慣例同 generate_props.py：1 單位 = 1 公分、Z 朝上、底面中心在原點、正面朝 +Y、平面著色純色材質。
"""
import math

from generate_props import (box, cylinder, sphere, limb, disc, torus, prism, rounded, paint, near, join,
                            flatten_bottom, spin, squash)


def build_curry_pot():
    """咖哩鍋：不鏽鋼湯鍋裝著滿滿的咖哩，浮著紅蘿蔔丁和馬鈴薯丁，斜插一支湯勺。"""
    steel, rim, curry = "#adb5bd", "#ced4da", "#c27c0e"
    cylinder(12.5, 15.0, (0, 0, 7.5), steel, verts=20)
    torus(12.6, 0.7, (0, 0, 15.0), rim, seg=20, mseg=6)
    # 咖哩面要高過鍋身的頂蓋（圓柱是實心的），從上面才看得到
    cylinder(12.2, 0.5, (0, 0, 15.2), curry, verts=20)
    for sx in (-1, 1):
        box((3.2, 5.0, 1.4), (14.0 * sx, 0, 13.0), "#495057", bevel=0.4)
    chunks = ((-5, 3, "#f77f00"), (4, -5, "#f77f00"), (6, 4, "#f0d9a0"), (-2, -6, "#f0d9a0"),
              (-7, -2, "#f77f00"), (1, 7, "#f0d9a0"), (8, -1, "#8c5a2b"))
    for x, y, col in chunks:
        box((2.6, 2.6, 1.6), (x, y, 15.6), col, rot=(0, 0, 25 * x), bevel=0.3)
    limb((2.0, 1.5, 15.2), (9.0, 7.5, 22.0), 0.65, 0.55, "#6c757d", verts=8)
    sphere(1, (1.5, 1.0, 15.4), "#6c757d", scale=(3.0, 3.0, 0.8), subdiv=1)


def build_electric_pot():
    """電鍋：淺綠色鍋身、白色圓頂鍋蓋、黑色蓋鈕與兩側提把，正面一個紅色開關。"""
    body, lid, ink = "#95d5b2", "#f8f9fa", "#343a40"
    cylinder(12.5, 19.0, (0, 0, 9.5), body, verts=20)
    cylinder(12.8, 1.6, (0, 0, 5.0), "#74c69d", verts=20)
    cylinder(12.9, 1.2, (0, 0, 19.2), lid, verts=20)
    sphere(1, (0, 0, 19.8), lid, scale=(12.2, 12.2, 4.6), subdiv=3)
    cylinder(2.2, 2.2, (0, 0, 25.4), ink, verts=12)
    for sx in (-1, 1):
        box((3.2, 6.0, 2.0), (14.0 * sx, 0, 17.0), ink, bevel=0.5)
    box((3.0, 1.2, 4.0), (0, 12.6, 6.0), "#e63946", bevel=0.3)
    cylinder(0.9, 0.6, (0, 12.4, 12.0), "#ffd166", verts=10, rot=(90, 0, 0))


def build_car():
    """家裡的車：圓潤的五門小車，柔和的紅色車身、淺藍車窗、黑色輪胎與銀色輪框。正面朝 +Y。"""
    paint_col, glass, tire, metal = "#e56b6f", "#a8dadc", "#2b2d42", "#ced4da"
    box((172, 430, 58), (0, 0, 55), paint_col, bevel=10, segments=3)
    box((150, 236, 56), (0, -18, 110), glass, bevel=10, segments=3)
    box((154, 214, 7), (0, -20, 140), paint_col, bevel=3)
    for y in (-110, -20, 72):
        box((154, 9, 52), (0, y, 110), paint_col)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cylinder(32, 24, (78 * sx, 138 * sy, 32), tire, verts=18, rot=(0, 90, 0))
            cylinder(19, 25, (78 * sx, 138 * sy, 32), metal, verts=12, rot=(0, 90, 0))
        box((10, 18, 10), (82 * sx, 80, 112), paint_col, bevel=2)
        box((38, 4, 14), (55 * sx, 215, 66), "#fff3b0", bevel=2)
        box((34, 4, 12), (58 * sx, -215, 72), "#d00000", bevel=2)
    for sy in (-1, 1):
        box((168, 10, 16), (0, 216 * sy, 34), "#adb5bd", bevel=3)
        box((44, 2, 14), (0, 221 * sy, 48), "#f8f9fa")
    box((150, 120, 1.0), (0, 140, 84.5), "#d9575c")


def build_cherry_tree():
    """山櫻花樹：深褐樹幹分出幾根枝枒，頂著一團團桃紅與粉紅的花，零星幾簇新綠葉。"""
    bark = "#6f4518"
    limb((0, 0, 0), (0, 0, 175), 15, 10, bark, verts=10)
    flatten_bottom(sphere(1, (0, 0, 4), bark, scale=(22, 22, 9), subdiv=2), 0.0)
    branches = ((90, 40, 255), (-85, 55, 250), (20, -95, 245), (-40, -60, 290), (55, 85, 300),
                (-100, -10, 300), (0, 10, 330))
    for x, y, z in branches:
        limb((0, 0, 150), (x, y, z), 7, 3.5, bark, verts=8)
    blossoms = ((0, 0, 330, 95, "#ff8fab"), (95, 45, 285, 72, "#f15bb5"), (-90, 55, 280, 75, "#ffafcc"),
                (25, -100, 275, 70, "#ff8fab"), (-45, -70, 320, 70, "#f15bb5"), (60, 90, 330, 62, "#ffafcc"),
                (-105, -15, 320, 60, "#ff8fab"), (100, -40, 330, 55, "#ffc8dd"), (-20, 60, 375, 55, "#ffafcc"),
                (30, -20, 385, 50, "#f15bb5"))
    for x, y, z, r, col in blossoms:
        sphere(r, (x, y, z), col, scale=(1.0, 1.0, 0.78), subdiv=2)
    for x, y, z in ((-60, 95, 255), (120, 10, 265), (-10, -120, 300)):
        sphere(22, (x, y, z), "#80b918", scale=(1.0, 1.0, 0.7), subdiv=1)


def build_scooter():
    """機車：淺藍色車殼的速克達，黑色坐墊、白色擋泥板、圓形大燈，前後輪是小輪框。正面朝 +Y。"""
    shell, seat, tire, metal = "#8ecae6", "#2b2d42", "#212529", "#ced4da"
    box((32, 72, 9), (0, 2, 26), "#e9ecef", bevel=2)
    box((44, 14, 64), (0, 56, 60), shell, rot=(-12, 0, 0), bevel=5)
    box((40, 78, 34), (0, -44, 50), shell, bevel=8, segments=3)
    box((32, 62, 11), (0, -40, 72), seat, bevel=4)
    limb((0, 62, 88), (0, 58, 104), 3.5, 3.0, metal, verts=8)
    box((66, 4, 4), (0, 58, 104), seat, bevel=1)
    for sx in (-1, 1):
        cylinder(2.6, 10, (31 * sx, 58, 104), "#495057", verts=8, rot=(0, 90, 0))
        limb((22 * sx, 58, 104), (28 * sx, 56, 116), 0.8, 0.8, metal, verts=6)
        sphere(1, (29 * sx, 56, 118), metal, scale=(4, 1.2, 3), subdiv=1)
    sphere(6.5, (0, 66, 92), "#fff3b0", scale=(1, 0.6, 1), subdiv=2)
    for y in (64, -62):
        cylinder(18, 9, (0, y, 18), tire, verts=16, rot=(0, 90, 0))
        cylinder(10, 9.5, (0, y, 18), metal, verts=10, rot=(0, 90, 0))
    box((14, 34, 4), (0, 66, 37), "#f8f9fa", bevel=1.5, rot=(18, 0, 0))
    box((26, 4, 8), (0, -84, 55), "#e63946", bevel=1.5)


def build_rubber_duck():
    """小黃鴨：圓圓的黃色身體、圓頭、橘色扁嘴、黑豆眼、翹起的小尾巴。正面朝 +Y。"""
    y, o, k = "#ffd60a", "#f77f00", "#1d1d1f"
    flatten_bottom(sphere(1, (0, 0, 2.7), y, scale=(3.4, 4.4, 2.7), subdiv=3), 0.0)
    sphere(2.4, (0, 2.3, 6.3), y, subdiv=2)
    sphere(1, (0, 4.7, 6.0), o, scale=(1.2, 1.1, 0.45), subdiv=2)
    for sx in (-1, 1):
        sphere(0.38, (1.0 * sx, 4.1, 7.0), k, subdiv=1)
    sphere(1, (0, -4.2, 3.9), y, scale=(1.0, 1.0, 1.1), subdiv=1)


def build_red_stool():
    """台灣家家戶戶都有的紅色塑膠凳：圓形凳面中間一個提手洞，下面是往外張開的裙邊與側邊開口。"""
    red, dark = "#d62828", "#8a1c1c"
    cylinder(15.0, 3.0, (0, 0, 26.5), red, verts=24)
    cylinder(15.2, 25.0, (0, 0, 12.5), red, verts=24, radius2=12.6)
    disc(4.0, 0.4, (0, 0, 28.05), (0, 0, 1), dark, verts=12)
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        x, y = 14.1 * math.cos(ang), 14.1 * math.sin(ang)
        spin(box((9.0, 1.0, 11.0), (x, y, 9.0), dark), (0, 0, math.degrees(ang) + 90), (x, y, 9.0))


def build_chicken():
    """母雞（土雞）：褐色圓胖身體、淺色胸口、紅色雞冠與肉垂、黃色小腳，尾羽往上翹。正面朝 +Y。
    可動部件 head、tail、leg_fl、leg_fr 由遊戲端做走路動畫。"""
    brown, chest, red, beak, k = "#b5651d", "#f1d7a8", "#d62828", "#f4a261", "#1d1d1f"
    body = sphere(1, (0, 0, 18), brown, scale=(9.5, 14.0, 10.5), subdiv=3)
    paint(body, chest, lambda c: c.y > 5.0 and c.z < 20.0)
    wings = [sphere(1, (8.3 * sx, -1.0, 19.0), "#8c4a16", scale=(2.2, 9.0, 6.0), subdiv=1) for sx in (-1, 1)]
    join([body] + wings, "body", pivot=(0, 0, 18))

    head = [sphere(5.0, (0, 12.5, 30.0), brown, subdiv=2)]
    paint(head[0], chest, lambda c: c.y > 14.0 and c.z < 30.0)
    for i, (y, z) in enumerate(((10.5, 35.0), (12.5, 35.8), (14.5, 35.0))):
        head.append(sphere(1.6 + 0.3 * (i == 1), (0, y, z), red, subdiv=1))
    head.append(sphere(1, (0, 16.5, 26.6), red, scale=(1.1, 0.9, 1.8), subdiv=1))
    head.append(limb((0, 16.5, 30.0), (0, 20.0, 29.4), 1.3, 0.2, beak, verts=6))
    for sx in (-1, 1):
        head.append(sphere(0.6, (2.6 * sx, 15.4, 31.4), k, subdiv=1))
    head.append(limb((0, 9.0, 24.0), (0, 11.5, 29.0), 3.6, 3.4, brown, verts=8))
    join(head, "head", pivot=(0, 9.0, 24.0))

    tail = []
    for i, (x, rot) in enumerate(((-2.5, -12), (0, 0), (2.5, 12))):
        feather = sphere(1, (x, -14.5, 27.0), "#5c3010" if i != 1 else "#7a4214", scale=(1.6, 3.2, 8.0), subdiv=1)
        tail.append(spin(feather, (-30, rot, 0), (x, -12.0, 22.0)))
    join(tail, "tail", pivot=(0, -12.0, 22.0))

    for name, x in (("leg_fl", -3.5), ("leg_fr", 3.5)):
        top = (x, 1.0, 10.0)
        parts = [limb(top, (x, 1.5, 1.2), 1.0, 0.8, "#f4c430", verts=6),
                 box((3.4, 4.6, 0.9), (x, 2.8, 0.45), "#f4c430")]
        join(parts, name, pivot=top)


RECIPES = {
    "hm_curry_pot": build_curry_pot,
    "hm_electric_pot": build_electric_pot,
    "hm_car": build_car,
    "hm_cherry_tree": build_cherry_tree,
    "hm_scooter": build_scooter,
    "hm_rubber_duck": build_rubber_duck,
    "hm_red_stool": build_red_stool,
    "hm_chicken": build_chicken,
}
