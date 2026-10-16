"""Blender 資產管線：以程式批次產生低多邊形道具，匯出 glTF（.glb）給 Godot。

執行方式（擇一）：
    1. 已安裝 Blender：
       blender --background --python tools/blender/generate_props.py -- [輸出資料夾] [物件 id ...]
    2. 使用 Blender Python 模組（pip install bpy==5.2.2，需 Python 3.13）：
       python tools/blender/generate_props.py [輸出資料夾] [物件 id ...]

預設輸出到 godot/assets/models/props/。Godot 端 PropFactory 會依 items.json 的 model 欄位
自動載入同名 .glb，並等比縮放到資料定義的尺寸；沒有模型的物件會退回程式產生的幾何。

建模慣例：1 Blender 單位 = 1 公分；底面中心在原點；Y 軸朝上（匯出時自動轉換）；
一律使用平面著色（flat shading）與純色材質，維持「玩具箱」感的低面數風格。
"""
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "godot" / "assets" / "models" / "props"


# ---------- 基本工具 ----------

_materials = {}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _materials.clear()


def material(hex_color: str):
    if hex_color in _materials:
        return _materials[hex_color]
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    # sRGB 轉線性，讓 glTF 匯出的顏色與 Godot 端一致
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    mat = bpy.data.materials.new(name=f"mat_{h}")
    try:
        mat.use_nodes = True
    except AttributeError:
        pass
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
    mat.diffuse_color = (*lin, 1.0)
    _materials[hex_color] = mat
    return mat


def finish(obj, color, bevel=0.0, segments=1):
    obj.data.materials.append(material(color))
    if bevel > 0:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return obj


def box(size, loc, color, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=[math.radians(r) for r in rot])
    obj = bpy.context.active_object
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return finish(obj, color, bevel, 2)


def cylinder(radius, depth, loc, color, verts=12, rot=(0, 0, 0), radius2=None):
    if radius2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc,
                                            rotation=[math.radians(r) for r in rot])
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=radius2, depth=depth, location=loc,
                                        rotation=[math.radians(r) for r in rot])
    return finish(bpy.context.active_object, color)


def sphere(radius, loc, color, scale=(1, 1, 1), subdiv=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return finish(obj, color)


def export(out_dir: Path, name: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.glb"
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=True)
    print(f"[blender] 匯出 {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


# ---------- 道具配方（Blender 座標：Z 朝上，單位公分） ----------

def build_thumbtack():
    cylinder(0.5, 0.3, (0, 0, 0.95), "#e63946", verts=14)
    cylinder(0.32, 0.25, (0, 0, 0.7), "#c1121f", verts=10, radius2=0.18)
    cylinder(0.07, 0.8, (0, 0, 0.4), "#c0c0c0", verts=6, radius2=0.01)


def build_die():
    box((1.6, 1.6, 1.6), (0, 0, 0.8), "#fafafa", bevel=0.18)
    pip = "#222222"
    r = 0.13
    faces = {
        (0, 0, 1): [(0, 0)],
        (0, 0, -1): [(-0.4, -0.4), (-0.4, 0), (-0.4, 0.4), (0.4, -0.4), (0.4, 0), (0.4, 0.4)],
        (1, 0, 0): [(-0.4, -0.4), (0.4, 0.4)],
        (-1, 0, 0): [(-0.4, -0.4), (0, 0), (0.4, 0.4), (-0.4, 0.4), (0.4, -0.4)],
        (0, 1, 0): [(-0.4, -0.4), (0, 0), (0.4, 0.4)],
        (0, -1, 0): [(-0.4, -0.4), (0.4, 0.4), (-0.4, 0.4), (0.4, -0.4)],
    }
    for n, pts in faces.items():
        for a, b in pts:
            if n[2] != 0:
                loc = (a, b, 0.8 + 0.79 * n[2])
            elif n[0] != 0:
                loc = (0.79 * n[0], a, 0.8 + b)
            else:
                loc = (a, 0.79 * n[1], 0.8 + b)
            sphere(r, loc, pip, subdiv=1)
    color = "#e63946"
    sphere(0.22, (0, 0, 1.59), color, subdiv=1)


def build_mahjong():
    box((2.6, 3.5, 1.3), (0, 0, 0.65), "#fdfcf5", bevel=0.12)
    box((2.6, 3.5, 0.7), (0, 0, 1.65), "#2d6a4f", bevel=0.12)
    # 正面簡單圓點牌面（原創圖樣）
    for dx, dy in ((-0.6, -0.9), (0.6, -0.9), (0, 0), (-0.6, 0.9), (0.6, 0.9)):
        cylinder(0.32, 0.08, (dx, dy, 1.31), "#1d4ed8" if dy else "#e63946", verts=10)


def build_eraser():
    box((4.4, 2.2, 1.2), (0, 0, 0.6), "#f8f9fa", bevel=0.15)
    box((2.6, 2.3, 1.3), (0.6, 0, 0.6), "#1d4ed8")
    box((0.3, 2.32, 1.32), (-0.55, 0, 0.6), "#f8f9fa")


def build_tangerine():
    sphere(3.0, (0, 0, 2.7), "#fb8500", scale=(1, 1, 0.9), subdiv=2)
    sphere(0.6, (0.3, 0, 5.45), "#2d6a4f", scale=(1, 1.8, 0.35), subdiv=1)
    cylinder(0.12, 0.4, (0, 0, 5.4), "#6b4f3a", verts=6)


def build_pusher():
    """原創推球角色「小滾」：藍色連身衣、圓頭、頭頂一片嫩芽。身高約 4.5 公分，面向 +Y（匯出後即 Godot 的前方 -Z）。"""
    sphere(0.75, (0, 0, 3.35), "#ffd7b5", subdiv=2)
    cylinder(0.55, 1.7, (0, 0, 1.75), "#5bc0eb", verts=10, radius2=0.42)
    sphere(0.11, (-0.32, 0.66, 3.45), "#2b2d42", subdiv=1)
    sphere(0.11, (0.32, 0.66, 3.45), "#2b2d42", subdiv=1)
    sphere(0.5, (0.2, 0, 4.2), "#7bc950", scale=(1.2, 0.6, 0.35), subdiv=1)
    for side in (-1, 1):
        cylinder(0.18, 1.2, (0.55 * side, 0.55, 2.0), "#5bc0eb", verts=8, rot=(-70, 0, 0))
        cylinder(0.2, 0.9, (0.35 * side, 0, 0.45), "#2b2d42", verts=8)


RECIPES = {
    "thumbtack": build_thumbtack,
    "die": build_die,
    "mahjong": build_mahjong,
    "eraser": build_eraser,
    "tangerine": build_tangerine,
    "pusher": build_pusher,
}


def main(argv):
    out_dir = Path(argv[0]) if argv else DEFAULT_OUT
    names = argv[1:] or list(RECIPES)
    for name in names:
        if name not in RECIPES:
            print(f"[blender] 略過未定義的配方：{name}")
            continue
        reset_scene()
        RECIPES[name]()
        export(out_dir, name)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(args)
