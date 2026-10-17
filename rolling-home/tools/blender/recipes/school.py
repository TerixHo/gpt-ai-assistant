"""第 3 關「小學與街區」的重點模型：溜滑梯、校車。

由 tools/blender/generate_props.py 自動載入（見 load_recipe_modules）。
建模慣例同主檔：1 Blender 單位 = 1 公分、底面中心在原點、Z 朝上、正面朝 +Y（遊戲裡是 -Z）。
遊戲端會把模型等比縮放到 data/items/school.json 的 dims，所以比例要跟 dims 一致。
"""
import math

from generate_props import box, cylinder, disc, limb, prism, rounded, sphere  # noqa: F401


def build_sc_slide():
    """遊戲場的溜滑梯：黃色平台與屋頂、藍色滑道往 +Y 滑下來、後面一座紅色梯子。約 120 x 460 x 260 公分。"""
    yellow, blue, red, metal, roof = "#ffbe0b", "#3a86ff", "#e63946", "#adb5bd", "#ff006e"
    # 平台（後段，-Y）與四根柱子
    for sx in (-1, 1):
        for sy in (-1, 1):
            cylinder(5, 250, (52 * sx, -150 + 52 * sy, 125), yellow, verts=8)
    box((120, 120, 10), (0, -150, 150), yellow, bevel=2)
    # 屋頂（尖頂）
    cylinder(85, 50, (0, -150, 225), roof, verts=4, radius2=2, rot=(0, 0, 45))
    # 欄杆
    for sx in (-1, 1):
        box((4, 120, 40), (58 * sx, -150, 175), red)
    box((120, 4, 40), (0, -208, 175), red)
    # 滑道：從平台前緣往 +Y 斜下到地面，兩側有護欄
    length = math.hypot(300, 145)
    ang = math.degrees(math.atan2(145, 300))
    chute = box((70, length, 6), (0, 60, 78), blue, bevel=2)
    chute.rotation_euler = (math.radians(-ang), 0, 0)
    for sx in (-1, 1):
        rail = box((5, length, 18), (37 * sx, 60, 86), blue)
        rail.rotation_euler = (math.radians(-ang), 0, 0)
    box((70, 30, 6), (0, 215, 4), blue)
    # 後面的梯子
    for sx in (-1, 1):
        limb((30 * sx, -230, 0), (30 * sx, -205, 150), 3, 3, red)
    for k in range(6):
        t = (k + 1) / 7
        limb((-30, -230 + 25 * t, 150 * t), (30, -230 + 25 * t, 150 * t), 2, 2, metal)


def build_sc_school_bus():
    """黃色校車：圓角車身、整排窗戶、黑色保險桿、四輪、前面有大車燈。約 250 x 1000 x 320 公分。"""
    body, glass, ink, metal, light, trim = "#ffbe0b", "#3d5a80", "#212529", "#ced4da", "#fff3b0", "#212529"
    side = rounded([(-500, 30), (500, 30), (500, 300), (-500, 300)], [10, 30, 60, 30], seg=3)
    prism(side, 246, body, axis="x")
    # 窗戶帶與擋風玻璃
    box((250, 760, 80), (0, -40, 225), glass)
    box((236, 6, 110), (0, 502, 220), glass)
    box((250, 1000, 10), (0, 0, 175), trim)
    # 車輪
    for sx in (-1, 1):
        for sy in (-330, 330):
            disc(52, 30, (112 * sx, sy, 52), (1, 0, 0), ink, verts=16)
            disc(26, 31, (113 * sx, sy, 52), (1, 0, 0), metal, verts=10)
        box((40, 6, 26), (85 * sx, 503, 110), light)
        box((40, 6, 26), (85 * sx, -503, 110), "#d00000")
    box((240, 10, 30), (0, 505, 50), trim)
    box((240, 10, 30), (0, -505, 50), trim)
    # 車頂燈與門
    box((60, 20, 16), (0, 420, 306), "#fb8500")
    box((6, 110, 200), (124, 380, 130), "#e09f3e")


RECIPES = {
    "sc_slide": build_sc_slide,
    "sc_school_bus": build_sc_school_bus,
}
