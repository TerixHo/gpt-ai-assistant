"""第 4 關「滾到冬山火車站」的重點模型：冬山車站、通勤電聯車車廂、廟、透天厝。

座標慣例同 generate_props.py：1 單位 = 1 公分，Z 朝上，底面中心在原點。
匯出到 Godot 時 Blender 的 +Y 會變成 Godot 的 -Z，所以 Godot 物件定義裡「正面朝 +Z」的建築，
在這裡正面要朝 -Y。模型會被等比縮放到 items 定義的尺寸（以最長邊對齊），比例要與 dims 一致。
"""
import math

import bmesh
import bpy
from generate_props import box, cylinder, finish, join, limb

GREEN = "#4f9a6a"
MEMBRANE = "#f3efe2"
WHITE = "#f8f9fa"
GLASS = "#9cc9d9"
INK = "#2b2d42"


def _half_tube(radius, length, z_scale, loc, color, verts=24):
    """沿 Y 軸的半圓管（上半部），高度依 z_scale 壓扁：車站的白色膜材屋頂。"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts * 2, radius=radius, depth=length, location=(0, 0, 0),
                                        rotation=(math.radians(90), 0, 0))
    obj = bpy.context.active_object
    bpy.ops.object.transform_apply(rotation=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01], context="VERTS")
    for v in bm.verts:
        v.co.z *= z_scale
    bm.to_mesh(obj.data)
    bm.free()
    obj.location = loc
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True)
    return finish(obj, color)


def _arch_rib(radius, z_scale, y, base_z, color, thick=40, seg=10):
    """一道拱形鋼骨（半圓，壓扁），由多段圓柱接成。"""
    pts = []
    for i in range(seg + 1):
        a = math.pi * i / seg
        pts.append((radius * math.cos(a), y, base_z + radius * math.sin(a) * z_scale))
    for p1, p2 in zip(pts, pts[1:]):
        limb(p1, p2, thick, thick, color, verts=5)
    return pts


def build_sn_station():
    """冬山車站：高架月台上一道道綠色拱形鋼骨與白色膜材屋頂，遠看像一座大瓜棚。
    下層是白色站體（玻璃大門），兩側是月台。尺寸 寬 3600 × 長 11000 × 高 2200（公分）。"""
    L, W = 11000, 3600
    # 下層站體（長度只有中間 5000，兩側是高架橋本身）
    box((W, 5000, 1150), (0, 0, 575), WHITE)
    box((W + 20, 5020, 80), (0, 0, 1190), GREEN)
    for sy in (-1, 1):
        box((2400, 20, 700), (0, sy * 2505, 450), GLASS)
        box((600, 30, 900), (0, sy * 2515, 450), "#6c757d")
    for sx in (-1, 1):
        for k in range(5):
            box((20, 600, 500), (sx * 1805, -2000 + k * 1000, 650), GLASS)
    # 月台與月台邊的黃色警戒線
    for sx in (-1, 1):
        box((1000, L, 150), (sx * 1200, 0, 1425), "#ced4da")
        box((60, L, 4), (sx * 740, 0, 1502), "#ffd166")
    # 屋頂：白色膜材半圓管（底部在月台高度 1500，頂端 2200）
    radius = W / 2
    z_scale = 700 / radius
    _half_tube(radius - 10, L - 200, z_scale, (0, 0, 1500), MEMBRANE)
    # 綠色拱形鋼骨，每 500 公分一道；相鄰兩道之間有交叉的斜撐（瓜棚的格子）
    ribs = []
    y = -L / 2 + 250
    while y <= L / 2 - 249:
        ribs.append(_arch_rib(radius + 20, z_scale, y, 1500, GREEN))
        y += 500
    for r1, r2 in zip(ribs, ribs[1:]):
        for i in (2, 6):
            limb(r1[i], r2[i + 2], 18, 18, GREEN, verts=4)
            limb(r1[i + 2], r2[i], 18, 18, GREEN, verts=4)
    # 支撐屋頂的柱子
    for y in range(-5000, 5001, 1000):
        for sx in (-1, 1):
            cylinder(45, 700, (sx * (radius - 60), y, 1850), GREEN, verts=8)


def build_sn_train_car():
    """通勤電聯車車廂（沒有標誌）：白色車身、深藍窗帶、藍色腰帶，車頂有冷氣機與集電弓，兩端是駕駛室。
    尺寸 寬 300 × 長 2000 × 高 420。"""
    L = 2000
    box((300, L - 40, 330), (0, 0, 230), "#eef1f4", bevel=30, segments=2)
    box((304, L - 200, 85), (0, 0, 295), "#33415c")
    box((304, L - 60, 26), (0, 0, 200), "#3a86ff")
    box((304, L - 60, 10), (0, 0, 180), "#ffd166")
    for y in (-600, -200, 200, 600):
        for sx in (-1, 1):
            box((6, 130, 250), (sx * 151, y, 205), "#adb5bd")
    for sy in (-1, 1):
        box((260, 20, 110), (0, sy * (L / 2 - 20), 300), "#1b263b")
        box((200, 24, 30), (0, sy * (L / 2 - 18), 150), "#e63946")
    box((240, L - 300, 25), (0, 0, 405), "#adb5bd")
    for y in (-500, 0, 500):
        box((180, 260, 40), (0, y, 430), "#ced4da")
    # 集電弓
    limb((0, -700, 415), (0, -560, 470), 4, 4, INK, verts=4)
    limb((0, -560, 470), (0, -700, 500), 4, 4, INK, verts=4)
    box((160, 10, 6), (0, -700, 502), INK)
    # 轉向架與車輪
    for y in (-700, 700):
        box((240, 300, 60), (0, y, 50), INK)
        for dy in (-90, 90):
            for sx in (-1, 1):
                cylinder(40, 12, (sx * 115, y + dy, 40), "#495057", verts=10, rot=(0, 90, 0))


def build_sn_temple():
    """廟：灰色石台、紅色殿身與柱子、橘黃色屋瓦，屋脊兩端是往上翹的綠色燕尾，屋脊中央有彩色裝飾。
    尺寸 寬 2500 × 深 3500 × 高 1800。正面朝 -Y（Godot 的 +Z）。"""
    box((2500, 3500, 150), (0, 0, 75), "#adb5bd")
    box((1200, 300, 75), (0, -1800, 40), "#ced4da")
    box((2200, 3000, 850), (0, 0, 575), "#c1121f")
    box((1400, 20, 500), (0, -1505, 450), "#7a1c1c")
    for x in (-900, -450, 450, 900):
        cylinder(70, 850, (x, -1560, 575), "#d62828", verts=10)
    # 屋頂：兩坡（前後）屋瓦
    roof = "#e09f3e"
    from generate_props import prism
    prism([(-1750, 0), (1750, 0), (0, 380)], 2600, roof, loc=(0, 0, 1000), axis="x")
    box((2700, 3600, 50), (0, 0, 1000), "#9d0208")
    # 屋脊與燕尾
    ridge_z = 1380
    box((2200, 160, 110), (0, 0, ridge_z + 40), "#2a9d8f")
    for sx in (-1, 1):
        limb((sx * 1000, 0, ridge_z + 40), (sx * 1250, 0, ridge_z + 300), 70, 25, "#2a9d8f", verts=6)
        limb((sx * 1250, 0, ridge_z + 300), (sx * 1320, 0, ridge_z + 420), 25, 8, "#2a9d8f", verts=6)
    # 屋脊中央的寶塔與兩側的彩色裝飾
    cylinder(90, 200, (0, 0, ridge_z + 180), "#ffd166", verts=8, radius2=30)
    for sx in (-1, 1):
        box((140, 120, 120), (sx * 450, 0, ridge_z + 140), "#ff6b6b", bevel=20)
        box((140, 120, 120), (sx * 750, 0, ridge_z + 140), "#4cc9f0", bevel=20)


def build_sn_townhouse():
    """台灣常見的透天厝：磁磚外牆、一樓鐵捲門、二到四樓窗戶與小陽台，頂樓加蓋藍色鐵皮與水塔。
    尺寸 寬 500 × 深 1500 × 高 1300。正面朝 -Y（Godot 的 +Z）。"""
    D = 1400
    front = -D / 2
    box((500, D, 1150), (0, 0, 575), "#eceae4")
    box((504, 6, 1150), (0, front - 2, 575), "#f4d6c6")
    # 一樓鐵捲門與門框
    box((420, 10, 290), (0, front - 6, 150), "#9aa0a6")
    for k in range(8):
        box((420, 12, 4), (0, front - 9, 25 + k * 35), "#80868b")
    box((500, 120, 25), (0, front - 50, 315), "#6c757d")
    # 二到四樓：窗戶與陽台
    for i, z in enumerate((480, 760, 1020)):
        box((380, 10, 140), (0, front - 6, z), GLASS)
        box((390, 12, 10), (0, front - 8, z), "#ffffff")
        if i < 2:
            box((480, 100, 15), (0, front - 50, z - 100), "#adb5bd")
            box((480, 6, 80), (0, front - 98, z - 55), "#e9ecef")
    # 頂樓加蓋鐵皮屋與水塔
    box((480, 700, 130), (0, 300, 1215), "#4895ef")
    box((500, 720, 14), (0, 300, 1287), "#3f78c4")
    cylinder(55, 110, (120, -300, 1205), "#e9ecef", verts=12)
    box((500, 10, 60), (0, front + 5, 1180), "#eceae4")


def _joined(fn, name):
    """建完後合併成單一網格：在 Godot 只會是一個 MeshInstance（每種材質一次繪製），iPad 才跑得動。"""
    def run():
        fn()
        join([o for o in bpy.context.scene.objects if o.type == "MESH"], name)
    return run


RECIPES = {
    "sn_station": _joined(build_sn_station, "sn_station"),
    "sn_train_car": _joined(build_sn_train_car, "sn_train_car"),
    "sn_temple": _joined(build_sn_temple, "sn_temple"),
    "sn_townhouse": _joined(build_sn_townhouse, "sn_townhouse"),
}
