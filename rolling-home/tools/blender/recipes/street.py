"""第 2 關「上學的路」的重點模型：機車、腳踏車（菜籃車）、土地公小廟、白鷺鷥、汽車（三種顏色）。

由 tools/blender/generate_props.py 自動載入（見 load_recipe_modules）。
建模慣例同主檔：1 Blender 單位 = 1 公分、底面中心在原點、Z 朝上、正面朝 +Y（遊戲裡是 -Z）。
遊戲端會把模型等比縮放到 data/items/street.json 的 dims，所以比例要跟 dims 一致。
"""
import math

from generate_props import box, cylinder, sphere, disc, torus, limb, prism, rounded, join, uv_sphere  # noqa: F401


def build_st_scooter():
    """台灣常見的速克達機車：白色車殼、深灰坐墊、前擋板、踏板、後箱與前後輪。約 65 x 185 x 110 公分。"""
    shell, accent, seat, ink, metal, glass = "#f1f3f5", "#4361ee", "#343a40", "#212529", "#adb5bd", "#caf0f8"
    # 輪子（前 +Y、後 -Y）
    for y in (62, -62):
        disc(23, 12, (0, y, 23), (1, 0, 0), ink, verts=16)
        disc(12, 13, (0, y, 23), (1, 0, 0), metal, verts=10)
    # 踏板與車身下緣
    box((40, 70, 10), (0, 2, 24), shell, bevel=3)
    # 後半車殼（坐墊下方）
    box((44, 76, 34), (0, -40, 48), shell, bevel=8, segments=2)
    box((45, 30, 6), (0, -42, 38), accent)
    # 坐墊
    box((36, 66, 10), (0, -38, 70), seat, bevel=4, segments=2)
    # 前擋板（直立，往後微傾）
    box((48, 16, 62), (0, 48, 58), shell, bevel=6, segments=2)
    box((49, 4, 20), (0, 56, 45), accent)
    # 龍頭、把手、儀表
    box((22, 18, 18), (0, 52, 96), shell, bevel=5)
    cylinder(2.5, 64, (0, 50, 102), metal, verts=8, rot=(0, 90, 0))
    for sx in (-1, 1):
        cylinder(3, 12, (31 * sx, 50, 102), ink, verts=8, rot=(0, 90, 0))
        box((10, 3, 6), (20 * sx, 60, 104), "#e9ecef")
    box((16, 4, 10), (0, 61, 92), "#ffd166")
    box((14, 2, 6), (0, 44, 106), glass)
    # 後箱與尾燈
    box((34, 30, 26), (0, -78, 88), "#495057", bevel=5)
    box((30, 4, 6), (0, -94, 60), "#d00000")
    # 前土除
    box((14, 26, 6), (0, 62, 46), shell, bevel=2)


def build_st_bike():
    """菜籃車：低跨點車架、前面有菜籃、後面有貨架，薄荷綠車架。約 55 x 170 x 100 公分。"""
    frame, ink, metal, seat = "#2ec4b6", "#212529", "#adb5bd", "#6c4f3d"
    for y in (58, -58):
        torus(31, 3.2, (0, y, 34), ink, rot=(0, 90, 0), seg=24, mseg=6)
        disc(4, 8, (0, y, 34), (1, 0, 0), metal, verts=8)
        for k in range(6):
            a = math.radians(k * 30)
            limb((0, y + 30 * math.cos(a), 34 + 30 * math.sin(a)), (0, y - 30 * math.cos(a), 34 - 30 * math.sin(a)),
                 0.5, 0.5, metal, verts=4)
    # 車架：從前叉往下彎到五通，再上到坐管（低跨點）
    limb((0, 50, 80), (0, 6, 30), 2.4, 2.4, frame)
    limb((0, 6, 30), (0, -58, 34), 2.0, 2.0, frame)
    limb((0, 6, 30), (0, -18, 78), 2.4, 2.4, frame)
    limb((0, -18, 78), (0, -58, 34), 1.6, 1.6, frame)
    limb((0, 58, 34), (0, 50, 82), 2.0, 2.0, metal)
    # 坐墊與龍頭
    box((14, 24, 6), (0, -20, 82), seat, bevel=2)
    limb((0, 50, 82), (0, 46, 98), 1.6, 1.6, metal)
    limb((-26, 44, 98), (26, 44, 98), 1.4, 1.4, metal)
    for sx in (-1, 1):
        cylinder(2.2, 9, (24 * sx, 44, 98), ink, verts=8, rot=(0, 90, 0))
    # 前菜籃與後貨架
    box((36, 26, 24), (0, 68, 82), "#e9ecef")
    box((32, 22, 20), (0, 68, 84), "#ced4da")
    box((22, 34, 2.5), (0, -56, 66), metal)
    # 鈴鐺
    sphere(2.6, (12, 46, 102), "#ffd166", subdiv=1)


def build_st_shrine():
    """田邊的土地公小廟：石台基、紅牆、正面開口與神桌、燕尾屋脊的紅瓦屋頂、門口香爐。約 260 x 260 x 300 公分。"""
    stone, wall, roof, ridge, gold, dark = "#adb5bd", "#c1121f", "#e85d04", "#2a9d8f", "#ffd166", "#3d2c2e"
    box((260, 240, 30), (0, -10, 15), stone, bevel=4)
    box((180, 26, 12), (0, 118, 6), stone)
    # 主體：兩側與背牆
    box((200, 150, 150), (0, -30, 105), wall, bevel=3)
    # 正面門洞與內部神桌（暗色）
    box((110, 6, 100), (0, 46, 95), dark)
    box((80, 30, 30), (0, 30, 60), "#9c6644")
    box((30, 12, 34), (0, 22, 92), gold)
    # 兩根前柱與門楣
    for sx in (-1, 1):
        cylinder(9, 150, (78 * sx, 70, 105), wall, verts=10)
    box((200, 30, 20), (0, 62, 186), "#7a1013")
    box((90, 4, 22), (0, 78, 186), gold)
    # 屋頂：人字形斷面，沿前後方向擠出
    prism([(-138, 0), (138, 0), (0, 60)], 270, roof, axis="y", loc=(0, -20, 194))
    # 屋脊與燕尾（兩端翹起）
    box((14, 250, 12), (0, -20, 254), ridge)
    for sy in (-1, 1):
        prism([(0, 0), (34, 0), (52, 30), (40, 34), (24, 10), (0, 10)], 12, ridge, axis="x",
              loc=(0, sy * 125 - 20, 250), rot=(0, 0, 0 if sy > 0 else 180))
    sphere(10, (0, -20, 266), gold, subdiv=1)
    # 香爐
    cylinder(18, 24, (0, 104, 42), "#6c757d", verts=12)
    cylinder(20, 4, (0, 104, 55), "#495057", verts=12)


def build_st_egret():
    """白鷺鷥：白色身體、S 形長頸、黃色嘴、黑色長腳。頭與兩腳是可動部件（head、leg_fl、leg_fr）。約 30 x 50 x 80 公分。"""
    white, bill, leg = "#f8f9fa", "#ffb703", "#212529"
    body = sphere(1.0, (0, -2, 48), white, scale=(9, 19, 11), subdiv=2)
    tail = prism([(0, 0), (-16, 3), (-14, -2)], 8, white, axis="x", loc=(0, -19, 46))
    neck1 = limb((0, 12, 54), (0, 16, 64), 3.2, 2.6, white)
    neck2 = limb((0, 16, 64), (0, 12, 72), 2.6, 2.4, white)
    join([body, tail, neck1, neck2], "body")
    head = sphere(1.0, (0, 14, 76), white, scale=(4.2, 6, 4.2), subdiv=2)
    beak = cylinder(1.4, 13, (0, 24, 75), bill, verts=6, rot=(-90, 0, 0), radius2=0.2)
    eye_l = sphere(0.8, (2.8, 16, 77.5), leg, subdiv=1)
    eye_r = sphere(0.8, (-2.8, 16, 77.5), leg, subdiv=1)
    join([head, beak, eye_l, eye_r], "head", pivot=(0, 13, 72))
    for name, sx in (("leg_fl", 1), ("leg_fr", -1)):
        thigh = limb((3.5 * sx, -2, 40), (3.5 * sx, -1, 20), 1.3, 1.0, leg)
        shin = limb((3.5 * sx, -1, 20), (3.5 * sx, 0, 0.8), 1.0, 0.9, leg)
        foot = box((2, 9, 1.2), (3.5 * sx, 3, 0.6), leg)
        join([thigh, shin, foot], name, pivot=(3.5 * sx, -2, 40))


def _car(body):
    """一般小汽車：圓角車身、深色車窗、四輪、車燈。約 180 x 450 x 150 公分。"""
    glass, ink, metal, light, tail = "#3d5a80", "#212529", "#ced4da", "#fff3b0", "#d00000"
    side = rounded([(-225, 20), (225, 20), (225, 85), (-225, 85)], 18, seg=3)
    prism([(y, z) for y, z in side], 176, body, axis="x")
    # 車廂整個是深色玻璃，上面蓋車頂、兩側加車柱
    cabin = rounded([(-130, 80), (115, 80), (60, 142), (-110, 142)], [10, 10, 10, 10], seg=3)
    prism([(y, z) for y, z in cabin], 158, glass, axis="x")
    box((156, 168, 7), (0, -25, 145), body, bevel=3)
    for sx in (-1, 1):
        box((4, 10, 60), (79.5 * sx, -10, 112), body)
        box((4, 10, 60), (79.5 * sx, -118, 112), body)
    for sx in (-1, 1):
        for sy in (-1, 1):
            disc(33, 22, (78 * sx, 140 * sy, 33), (1, 0, 0), ink, verts=16)
            disc(18, 23, (79 * sx, 140 * sy, 33), (1, 0, 0), metal, verts=10)
        box((34, 4, 14), (55 * sx, 226, 64), light)
        box((30, 4, 12), (60 * sx, -226, 66), tail)
        box((4, 16, 6), (89 * sx, 60, 92), body)
    box((120, 6, 18), (0, 228, 40), "#495057")
    box((120, 6, 18), (0, -228, 40), "#495057")


def build_st_car_white():
    _car("#f1f3f5")


def build_st_car_red():
    _car("#e63946")


def build_st_car_blue():
    _car("#3a86ff")


RECIPES = {
    "st_scooter": build_st_scooter,
    "st_bike": build_st_bike,
    "st_shrine": build_st_shrine,
    "st_egret": build_st_egret,
    "st_car_white": build_st_car_white,
    "st_car_red": build_st_car_red,
    "st_car_blue": build_st_car_blue,
}
