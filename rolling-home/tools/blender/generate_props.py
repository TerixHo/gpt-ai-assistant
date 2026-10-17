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
import bmesh  # 需在 bpy 之後匯入（bpy 模組模式下才會註冊）
from mathutils import Euler, Matrix, Vector

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


def box(size, loc, color, bevel=0.0, rot=(0, 0, 0), segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=[math.radians(r) for r in rot])
    obj = bpy.context.active_object
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return finish(obj, color, bevel, segments)


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


def squash(obj, sx=1.0, sy=1.0, sz=1.0):
    """在物件本地座標直接縮放網格（旋轉之前套用），例如把圓盤壓成橢圓。"""
    obj.data.transform(Matrix.Diagonal((sx, sy, sz, 1.0)))
    return obj


def spin(obj, rot, center):
    """以 center 為中心旋轉網格（度）。box/sphere 建立後變換已套用、原點在世界原點，不能直接改 rotation_euler。"""
    c = Vector(center)
    r = Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    obj.data.transform(Matrix.Translation(c) @ r @ Matrix.Translation(-c))
    return obj


def flatten_bottom(obj, z=0.0):
    """把低於 z 的頂點壓平，讓蛋形底部平穩坐在地上。"""
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, z)
    obj.data.update()
    return obj


def limb(p1, p2, r1, r2, color, verts=8):
    """從 p1 到 p2 的圓柱／圓錐（四肢、尾巴、莖）。"""
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d.length, location=(p1 + p2) / 2)
    obj = bpy.context.active_object
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return finish(obj, color)


def disc(radius, depth, loc, normal, color, verts=12, radius2=None):
    """軸心沿 normal 擺放的圓柱（輪子、貼花、眼睛）。"""
    obj = cylinder(radius, depth, loc, color, verts=verts, radius2=radius2)
    obj.rotation_euler = Vector(normal).to_track_quat("Z", "Y").to_euler()
    return obj


def torus(major, minor, loc, color, rot=(0, 0, 0), seg=12, mseg=6):
    bpy.ops.mesh.primitive_torus_add(major_segments=seg, minor_segments=mseg, major_radius=major,
                                     minor_radius=minor, location=loc, rotation=[math.radians(r) for r in rot])
    return finish(bpy.context.active_object, color)


def uv_sphere(radius, loc, color, segments=16, rings=8, scale=(1, 1, 1)):
    """經緯球：赤道有整圈邊，適合上下兩色（扭蛋殼）。"""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return finish(obj, color)


def tile(size, loc, normal, color):
    """單面方片（魔術方塊色塊）；匯出的材質為雙面，背面也看得到。"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    obj = bpy.context.active_object
    squash(obj, size[0], size[1], 1.0)
    obj.rotation_euler = Vector(normal).to_track_quat("Z", "Y").to_euler()
    return finish(obj, color)


def mesh(verts, faces, color, name="mesh", bevel=0.0, segments=2):
    """由頂點與面直接建立網格（紙鶴、葉片、擠出的輪廓）。"""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return finish(obj, color, bevel, segments)


def prism(outline, thickness, color, loc=(0, 0, 0), rot=(0, 0, 0), axis="y", offset=0.0, bevel=0.0, segments=2):
    """把 2D 輪廓擠出成板：axis='y' 輪廓在 XZ 平面（立著），'z' 在 XY 平面（平放），'x' 在 YZ 平面。"""
    n = len(outline)
    verts = []
    for s in (offset - thickness / 2, offset + thickness / 2):
        for a, b in outline:
            verts.append({"x": (s, a, b), "y": (a, s, b), "z": (a, b, s)}[axis])
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    obj = mesh(verts, faces, color, "prism", bevel, segments)
    obj.location = loc
    obj.rotation_euler = [math.radians(r) for r in rot]
    return obj


def rounded(corners, radius, seg=4):
    """圓角多邊形輪廓（凸多邊形）；radius 可為單一數值或每個角各自的半徑。"""
    radii = list(radius) if isinstance(radius, (list, tuple)) else [radius] * len(corners)
    n = len(corners)
    pts = []
    for i, r in enumerate(radii):
        p = Vector(corners[i])
        if r <= 0:
            pts.append((p.x, p.y))
            continue
        a = (Vector(corners[i - 1]) - p).normalized()
        b = (Vector(corners[(i + 1) % n]) - p).normalized()
        half = a.angle(b) / 2
        c = p + (a + b).normalized() * (r / math.sin(half))
        p1 = p + a * (r / math.tan(half))
        p2 = p + b * (r / math.tan(half))
        a1 = math.atan2(p1.y - c.y, p1.x - c.x)
        a2 = math.atan2(p2.y - c.y, p2.x - c.x)
        d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            t = a1 + d * k / seg
            pts.append((c.x + r * math.cos(t), c.y + r * math.sin(t)))
    return pts


def star(r_out, r_in, n=5):
    """星形／花瓣輪廓，第一個尖端朝上。"""
    return [((r_out if i % 2 == 0 else r_in) * math.cos(math.pi / 2 + i * math.pi / n),
             (r_out if i % 2 == 0 else r_in) * math.sin(math.pi / 2 + i * math.pi / n)) for i in range(2 * n)]


def paint(obj, color, pred):
    """依面中心的世界座標把部分面換色（三毛貓花斑、柴犬裏白），不增加面數。"""
    bpy.context.view_layer.update()
    mat = material(color)
    names = [m.name for m in obj.data.materials]
    if mat.name not in names:
        obj.data.materials.append(mat)
        names.append(mat.name)
    idx = names.index(mat.name)
    mw = obj.matrix_world
    for poly in obj.data.polygons:
        if pred(mw @ poly.center):
            poly.material_index = idx
    return obj


def near(*blobs):
    """paint 用：面中心落在任一 (中心, 半徑) 球內。"""
    return lambda c: any((c - Vector(p)).length < r for p, r in blobs)


def join(objs, name, pivot=(0, 0, 0)):
    """合併成單一物件並把原點設在 pivot（關節）。動物的 head/tail/leg_* 靠這個讓遊戲端旋轉。"""
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for mod in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    target = objs[0]
    bpy.context.view_layer.objects.active = target
    if len(objs) > 1:
        bpy.ops.object.join()
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.context.scene.cursor.location = pivot
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    target.name = name
    target.data.name = name
    return target


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


def build_eraser():
    box((4.4, 2.2, 1.2), (0, 0, 0.6), "#f8f9fa", bevel=0.15)
    box((2.6, 2.3, 1.3), (0.6, 0, 0.6), "#1d4ed8")
    box((0.3, 2.32, 1.32), (-0.55, 0, 0.6), "#f8f9fa")


def build_tangerine():
    sphere(3.0, (0, 0, 2.7), "#fb8500", scale=(1, 1, 0.9), subdiv=2)
    sphere(0.6, (0.3, 0, 5.45), "#2d6a4f", scale=(1, 1.8, 0.35), subdiv=1)
    cylinder(0.12, 0.4, (0, 0, 5.4), "#6b4f3a", verts=6)


def _srgb_to_linear(hex_color):
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]


def _hex_rgb(hex_color):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def _gradient(stops, z):
    """stops：[(z, "#rrggbb"), ...] 由低到高。
    回傳 sRGB 數值（不轉線性）：Godot 匯入 glTF 頂點顏色時會再做一次轉換，直接存 sRGB 顯示出來才是原本的顏色。"""
    if z <= stops[0][0]:
        return _hex_rgb(stops[0][1])
    for (z0, c0), (z1, c1) in zip(stops, stops[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0)
            t = t * t * (3 - 2 * t)
            a, b = _hex_rgb(c0), _hex_rgb(c1)
            return [a[i] + (b[i] - a[i]) * t for i in range(3)]
    return _hex_rgb(stops[-1][1])


def _vertex_material():
    """顏色來自頂點顏色的霧面材質（glTF 會匯出 COLOR_0，Godot 端再加上絨面光澤）。"""
    if "pusher_skin" in _materials:
        return _materials["pusher_skin"]
    mat = bpy.data.materials.new(name="pusher_skin")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    attr = nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    mat.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    _materials["pusher_skin"] = mat
    return mat


def _skin(obj, stops):
    """平滑著色＋依高度上漸層色。"""
    bpy.context.view_layer.update()
    obj.data.materials.clear()
    obj.data.materials.append(_vertex_material())
    for poly in obj.data.polygons:
        poly.use_smooth = True
    col = obj.data.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="CORNER")
    mw = obj.matrix_world
    for loop in obj.data.loops:
        z = (mw @ obj.data.vertices[loop.vertex_index].co).z
        c = _gradient(stops, z)
        col.data[loop.index].color = (c[0], c[1], c[2], 1.0)
    obj.data.color_attributes.active_color = col
    return obj


def _smooth_sphere(radius, loc, scale=(1, 1, 1), seg=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return obj


BODY_STOPS = [(0.6, "#95a8f0"), (2.2, "#b8a8f3"), (3.9, "#d6c2f8")]


def build_pusher():
    """主角：圓滾滾的紫色貓咪（依 Terix 提供的角色圖建模）。
    身高約 4.5 公分（含耳朵），面向 +Y（匯出後即 Godot 的前方 -Z）。
    可動部件拆成 body / ear_l / ear_r / arm_l / arm_r / foot_l / foot_r，原點在關節，遊戲端旋轉做動畫。
    左右以角色自身為準：面向 +Y 時左邊是 -X。"""
    cz, hw, hh, hd = 2.25, 1.75, 1.97, 1.55
    body = _smooth_sphere(1.0, (0, 0, cz), scale=(hw, hd, hh), seg=40, rings=24)
    # 蛋形：上半部稍微收窄，最寬處在中間偏下
    for v in body.data.vertices:
        t = (v.co.z - cz) / hh
        k = 1.0 - 0.10 * max(t, 0.0) + 0.03 * max(-t, 0.0) * (1.0 + t)
        v.co.x *= k
        v.co.y *= k
    flatten_bottom(body, 0.32)
    body.data.update()
    _skin(body, BODY_STOPS)

    def surface_y(x, z):
        t = (z - cz) / hh
        k = 1.0 - 0.10 * max(t, 0.0) + 0.03 * max(-t, 0.0) * (1.0 + t)
        inner = 1.0 - (x / (hw * k)) ** 2 - t * t
        return hd * k * math.sqrt(max(inner, 0.0))

    parts = [body]
    # 眼睛：亮面黑珠子＋小反光點
    for sx in (-1, 1):
        ex, ez = 0.76 * sx, 2.98
        ey = surface_y(ex, ez) - 0.05
        eye = _smooth_sphere(0.13, (ex, ey, ez), scale=(1.0, 0.7, 1.2), seg=16, rings=10)
        finish(eye, "#141414")
        for poly in eye.data.polygons:
            poly.use_smooth = True
        eye.data.materials[0].name = "pusher_eye"
        parts.append(eye)
        glint = _smooth_sphere(0.035, (ex + 0.04, ey + 0.08, ez + 0.06), seg=8, rings=6)
        finish(glint, "#ffffff")
        parts.append(glint)
    # 嘴巴：小小的微笑弧線
    pts = []
    for i in range(9):
        a = math.radians(205 + 130 * i / 8)
        x, z = 0.2 * math.cos(a), 2.78 + 0.13 * math.sin(a)
        pts.append((x, surface_y(x, z) + 0.005, z))
    for p1, p2 in zip(pts, pts[1:]):
        seg = limb(p1, p2, 0.028, 0.028, "#2a2030", verts=6)
        for poly in seg.data.polygons:
            poly.use_smooth = True
        parts.append(seg)
    join(parts, "body", pivot=(0, 0, 0))

    # 耳朵：圓錐，尖端略圓，向外微傾
    for sx, name in ((-1, "ear_l"), (1, "ear_r")):
        base = (1.05 * sx, -0.05, 3.55)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.66, radius2=0.17, depth=0.95, location=(0, 0, 0.475))
        ear = bpy.context.active_object
        tip = _smooth_sphere(0.17, (0, 0, 0.95), seg=12, rings=8)
        bpy.ops.object.select_all(action="DESELECT")
        ear.select_set(True)
        tip.select_set(True)
        bpy.context.view_layer.objects.active = ear
        bpy.ops.object.join()
        ear.data.transform(Matrix.Diagonal((1.0, 0.8, 1.0, 1.0)))
        ear.data.transform(Euler((math.radians(-8), math.radians(20 * sx), 0)).to_matrix().to_4x4())
        ear.data.transform(Matrix.Translation(Vector(base)))
        _skin(ear, [(3.6, "#b19cf2"), (4.5, "#c9aaf5")])
        join([ear], name, pivot=base)

    # 短短的手：在身體兩側，原點在肩膀
    for sx, name in ((-1, "arm_l"), (1, "arm_r")):
        shoulder = (1.55 * sx, 0.05, 2.45)
        arm = _smooth_sphere(1.0, (1.82 * sx, 0.05, 1.78), scale=(0.3, 0.34, 0.74), seg=20, rings=12)
        spin(arm, (0, 14 * sx, 0), shoulder)
        _skin(arm, BODY_STOPS)
        join([arm], name, pivot=shoulder)

    # 兩隻小腳：原點在髖部
    for sx, name in ((-1, "foot_l"), (1, "foot_r")):
        hip = (0.82 * sx, 0.1, 0.55)
        foot = _smooth_sphere(1.0, (0.86 * sx, 0.18, 0.2), scale=(0.36, 0.42, 0.3), seg=20, rings=12)
        flatten_bottom(foot, 0.0)
        _skin(foot, [(0.0, "#8a9be6"), (0.6, "#95a8f0")])
        join([foot], name, pivot=hip)


# ---------- 動物（可動部件） ----------
# 動物一律拆成 body / head / tail / leg_fl / leg_fr / leg_bl / leg_br 七個頂層物件，
# head 原點在脖子、tail 在尾根、leg_* 在肩／髖頂端，遊戲端直接旋轉這些節點做動畫。
# 左右以動物自身為準：面向 +Y 時左邊是 -X。

def build_cat():
    """三毛貓：白底配橘、黑花斑，三角耳、長尾巴。約 20 x 30 x 46 公分，面向 +Y。"""
    w, o, k, p = "#fafafa", "#f4a259", "#2b2d42", "#ff8fab"
    body = sphere(1, (0, -0.5, 15.2), w, scale=(6.8, 12.5, 6.2), subdiv=3)
    paint(body, o, near(((-5.5, -2.5, 19.2), 6.5), ((4.0, -10.5, 17.7), 4.5)))
    paint(body, k, near(((5.5, 4.0, 19.7), 5.0), ((-3.5, -10.5, 20.2), 3.5)))
    chest = sphere(1, (0, 8.5, 17.2), w, scale=(5.2, 5.2, 5.4), subdiv=2)
    paint(chest, k, near(((5.0, 8.0, 21.2), 3.5)))
    join([body, chest], "body", pivot=(0, 0, 15.2))

    head = [sphere(1, (0, 15.4, 22.0), w, scale=(6.0, 5.2, 5.1), subdiv=2)]
    paint(head[0], o, lambda c: c.x < -1.0 and c.z > 21.8 and c.y < 19.2)
    paint(head[0], k, lambda c: c.x > 1.2 and c.z > 23.2 and c.y < 18.7)
    for sx, col in ((-1, o), (1, k)):
        rot = (-6, 18 * sx, 0)
        ear = (3.2 * sx, 15.2, 24.7)
        head.append(prism([(-2.3, 0), (2.3, 0), (0.25 * sx, 4.4)], 1.2, col, loc=ear, rot=rot))
        head.append(prism([(-1.3, 0.5), (1.3, 0.5), (0.2 * sx, 3.3)], 0.3, p, loc=ear, rot=rot, offset=0.65))
        head.append(sphere(1, (2.1 * sx, 19.85, 22.8), k, scale=(0.85, 0.45, 1.0), subdiv=1))
        head.append(sphere(0.27, (2.3 * sx, 20.25, 23.15), w, subdiv=1))
        head.append(sphere(1, (1.0 * sx, 20.3, 20.8), w, scale=(1.3, 0.9, 1.0), subdiv=1))
        for dz, drop in ((0.25, 0.6), (-0.35, -0.8)):
            head.append(limb((1.7 * sx, 20.8, 20.9 + dz), (9.8 * sx, 19.6, 20.9 + dz + drop), 0.09, 0.06,
                             "#6c757d", verts=4))
    head.append(sphere(1, (0, 21.15, 21.7), p, scale=(0.62, 0.38, 0.42), subdiv=1))
    join(head, "head", pivot=(0, 11.5, 19.8))

    tail_pts = [(0, -11.8, 17.7), (0, -16.5, 18.9), (0, -20.5, 21.4), (0, -23.0, 25.0), (0, -23.2, 29.0)]
    radii = (1.5, 1.4, 1.25, 1.1, 0.95)
    cols = (w, o, k, o, k)
    tail = []
    for i in range(4):
        tail.append(limb(tail_pts[i], tail_pts[i + 1], radii[i], radii[i + 1], cols[i], verts=8))
        tail.append(sphere(radii[i + 1], tail_pts[i + 1], cols[i + 1] if i == 3 else cols[i], subdiv=1))
    join(tail, "tail", pivot=tail_pts[0])

    for name, x, y in (("leg_fl", -3.4, 8.0), ("leg_fr", 3.4, 8.0), ("leg_bl", -3.6, -8.5), ("leg_br", 3.6, -8.5)):
        top = (x, y, 13.7)
        parts = [limb(top, (x, y + 0.4, 1.4), 2.05, 1.7, w, verts=8),
                 sphere(1, (x, y + 0.9, 1.0), w, scale=(1.95, 2.5, 1.0), subdiv=1)]
        if y < 0:
            thigh = sphere(1, (x * 1.05, y, 10.8), w, scale=(2.8, 4.3, 4.5), subdiv=1)
            paint(thigh, o if x < 0 else k, lambda c: c.z > 10.3)
            parts.append(thigh)
        join(parts, name, pivot=top)


def build_dog():
    """柴犬：背部赤褐、腹部與臉頰奶油色（裏白），立耳、捲尾巴蓋在背上。約 24 x 42 x 58 公分，面向 +Y。"""
    t, c, k, w = "#d9822b", "#fbe8cc", "#2b2d42", "#fafafa"
    body = sphere(1, (0, 0, 27), t, scale=(10.5, 18.5, 8.8), subdiv=3)
    paint(body, c, lambda p: p.z < 24.0 or (p.y > 11 and p.z < 28.5))
    chest = sphere(1, (0, 14, 31.5), t, scale=(7.3, 7.0, 7.4), subdiv=2)
    paint(chest, c, lambda p: p.y > 16.5 and p.z < 33.0)
    join([body, chest], "body", pivot=(0, 0, 27))

    head = [sphere(1, (0, 23.5, 32.6), t, scale=(7.3, 6.7, 6.3), subdiv=2)]
    paint(head[0], c, lambda p: p.z < 30.8 and p.y > 21.5)
    head.append(sphere(1, (0, 29.5, 30.6), c, scale=(3.5, 3.9, 2.9), subdiv=2))
    head.append(sphere(1, (0, 33.0, 31.7), k, scale=(1.3, 0.8, 0.85), subdiv=1))
    for sx in (-1, 1):
        rot = (-10, 14 * sx, 0)
        ear = (3.6 * sx, 22.7, 36.6)
        head.append(prism([(-2.6, 0), (2.6, 0), (0.3 * sx, 5.0)], 1.6, t, loc=ear, rot=rot))
        head.append(prism([(-1.5, 0.6), (1.5, 0.6), (0.2 * sx, 3.6)], 0.3, c, loc=ear, rot=rot, offset=0.85))
        head.append(sphere(1, (2.6 * sx, 29.3, 34.2), k, scale=(0.9, 0.47, 0.95), subdiv=1))
        head.append(sphere(0.27, (2.8 * sx, 29.75, 34.55), w, subdiv=1))
        head.append(sphere(1, (2.4 * sx, 28.55, 36.1), c, scale=(0.8, 0.3, 0.48), subdiv=1))
    join(head, "head", pivot=(0, 18.5, 30.5))

    ring_c, ring_r = Vector((0, -16.5, 36.3)), 3.8
    pts = [Vector((0, -17.5, 29.8))]
    for i, ang in enumerate((225, 180, 135, 90, 45, 0, -35)):
        a = math.radians(ang)
        pts.append(ring_c + Vector((0.3 * i, ring_r * math.cos(a), ring_r * math.sin(a))))

    def inner(p):
        return (Vector((0, p.y, p.z)) - Vector((0, ring_c.y, ring_c.z))).length < ring_r - 0.3

    tail = []
    for i in range(len(pts) - 1):
        r1, r2 = 2.1 - 0.12 * i, 2.1 - 0.12 * (i + 1)
        tail.append(paint(limb(pts[i], pts[i + 1], r1, r2, t, verts=6), c, inner))
        tail.append(paint(sphere(r2, pts[i + 1], t, subdiv=1), c, inner))
    join(tail, "tail", pivot=tuple(pts[0]))

    for name, x, y in (("leg_fl", -5.5, 12.0), ("leg_fr", 5.5, 12.0)):
        top = (x, y, 25.0)
        parts = [limb(top, (x, y + 0.3, 9.0), 2.5, 2.25, t, verts=8),
                 limb((x, y + 0.3, 9.0), (x, y + 0.6, 2.0), 2.25, 2.1, c, verts=8),
                 sphere(1, (x, y + 1.3, 1.5), c, scale=(2.3, 3.0, 1.5), subdiv=1)]
        join(parts, name, pivot=top)
    for name, x in (("leg_bl", -5.5), ("leg_br", 5.5)):
        top, hock = (x, -12.5, 26.0), (x, -14.6, 9.0)
        parts = [sphere(1, (x * 1.08, -12.8, 21.5), t, scale=(3.4, 5.2, 6.2), subdiv=1),
                 limb(top, hock, 2.6, 2.1, t, verts=8),
                 sphere(2.1, hock, t, subdiv=1),
                 limb(hock, (x, -13.4, 2.0), 2.1, 2.0, c, verts=8),
                 sphere(1, (x, -12.3, 1.5), c, scale=(2.3, 3.0, 1.5), subdiv=1)]
        join(parts, name, pivot=top)


# ---------- 玩具、文具與擺飾 ----------

def build_minicar():
    """紅色合金小汽車：車身、淺藍車窗、四個黑輪。面向 +Y。"""
    red, glass, ink, metal = "#e63946", "#a8dadc", "#2b2d42", "#c0c0c0"
    box((2.6, 7.2, 1.15), (0, 0, 1.05), red, bevel=0.25)
    box((2.2, 3.4, 1.1), (0, -0.4, 2.15), glass, bevel=0.15)
    box((2.3, 3.0, 0.3), (0, -0.45, 2.85), red)
    box((2.26, 0.35, 1.0), (0, -0.4, 2.15), red)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cylinder(0.62, 0.5, (1.25 * sx, 2.3 * sy, 0.62), ink, verts=12, rot=(0, 90, 0))
            cylinder(0.3, 0.06, (1.51 * sx, 2.3 * sy, 0.62), metal, verts=6, rot=(0, 90, 0))
        box((0.55, 0.1, 0.3), (0.8 * sx, 3.6, 1.2), "#ffd166")
        box((0.5, 0.1, 0.25), (0.85 * sx, -3.6, 1.25), "#9d0208")
    for sy in (-1, 1):
        box((2.5, 0.3, 0.3), (0, 3.6 * sy, 0.65), metal)


def build_dinosaur():
    """綠色暴龍玩具公仔：大頭、小手、粗腿、尾巴往後伸，背上一排深綠色背棘。面向 +Y。"""
    g, light, dark, w, k = "#57cc99", "#c7f9cc", "#2d6a4f", "#fafafa", "#2b2d42"
    body = spin(sphere(1, (0, 0.1, 2.5), g, scale=(0.95, 1.6, 1.05), subdiv=2), (25, 0, 0), (0, 0.1, 2.5))
    paint(body, light, lambda c: c.z < 2.35 and c.y > -0.4)
    limb((0, -1.1, 2.3), (0, -3.0, 1.2), 0.6, 0.12, g, verts=8)
    limb((0, 0.9, 2.9), (0, 1.5, 3.6), 0.55, 0.5, g, verts=8)
    box((1.2, 1.9, 1.0), (0, 2.1, 4.0), g, bevel=0.25)
    box((1.0, 1.5, 0.4), (0, 2.15, 3.35), light)
    for sx in (-1, 1):
        sphere(1, (0.85 * sx, -0.3, 1.75), g, scale=(0.6, 0.85, 0.8), subdiv=1)
        limb((0.85 * sx, -0.3, 1.4), (0.85 * sx, -0.1, 0.25), 0.32, 0.26, g, verts=6)
        box((0.7, 1.1, 0.3), (0.85 * sx, 0.2, 0.15), g)
        limb((0.55 * sx, 1.05, 2.55), (0.65 * sx, 1.5, 2.15), 0.14, 0.11, g, verts=6)
        sphere(0.2, (0.5 * sx, 2.55, 4.2), w, subdiv=1)
        sphere(0.11, (0.66 * sx, 2.62, 4.22), k, subdiv=1)
    for y, z, s in ((0.95, 3.5, 0.8), (0.35, 3.52, 1.0), (-0.35, 3.33, 1.0), (-1.0, 2.88, 0.9), (-1.6, 2.2, 0.75),
                    (-2.25, 1.75, 0.6)):
        prism([(-0.28 * s, 0), (0.28 * s, 0), (0, 0.45 * s)], 0.14, dark, loc=(0, y, z - 0.12), axis="x")


def build_daruma():
    """紅色達摩不倒翁：蛋形身體、白色臉部、黑色眉毛鬍子與雙眼、金色腹紋。面向 +Y。"""
    red, face, k, gold = "#d62828", "#fdfcf5", "#2b2d42", "#ffd166"
    flatten_bottom(sphere(1, (0, 0, 3.2), red, scale=(3.0, 3.0, 3.7), subdiv=3))
    sphere(1, (0, 1.75, 4.35), face, scale=(2.2, 1.3, 1.85), subdiv=2)
    for sx in (-1, 1):
        sphere(1, (0.8 * sx, 2.92, 4.6), k, scale=(0.5, 0.22, 0.5), subdiv=1)
        box((1.1, 0.25, 0.24), (0.85 * sx, 2.7, 5.45), k, rot=(0, -15 * sx, 0))
        box((1.0, 0.25, 0.22), (0.55 * sx, 2.9, 3.55), k, rot=(0, 20 * sx, 0))
    sphere(1, (0, 2.25, 1.7), gold, scale=(1.6, 0.62, 0.9), subdiv=2)


def build_kendama():
    """木製劍玉：劍柄、左右大小皿、頂端劍尖插著有白色條紋的紅球。"""
    wood, dark, red, w = "#deb887", "#b08155", "#e63946", "#fafafa"
    cylinder(1.5, 1.2, (0, 0, 0.6), wood, verts=12, radius2=1.0)
    cylinder(0.8, 7.6, (0, 0, 4.9), wood, verts=10)
    cylinder(1.25, 4.4, (0, 0, 9.3), wood, verts=10, rot=(0, 90, 0))
    for sx, r1, r2 in ((1, 1.0, 2.0), (-1, 0.9, 1.7)):
        disc(r1, 1.3, (2.85 * sx, 0, 9.3), (sx, 0, 0), wood, verts=12, radius2=r2)
        disc(r2 - 0.3, 0.05, (3.51 * sx, 0, 9.3), (sx, 0, 0), dark, verts=12)
    cylinder(0.7, 1.6, (0, 0, 11.3), wood, verts=10)
    cylinder(0.55, 1.2, (0, 0, 12.7), wood, verts=10, radius2=0.12)
    sphere(3.0, (0, 0, 15.0), red, subdiv=2)
    disc(3.03, 0.5, (0, 0, 15.0), (1, 0, 0), w, verts=16)


def build_gacha_capsule():
    """扭蛋殼：上半淺藍、下半粉紅，中間一圈白色接縫。"""
    cap = uv_sphere(2.5, (0, 0, 2.5), "#ff8fab", segments=16, rings=10)
    paint(cap, "#a2d2ff", lambda c: c.z > 2.5)
    cylinder(2.53, 0.35, (0, 0, 2.5), "#fafafa", verts=16)


def build_plush_bear():
    """坐姿咖啡色泰迪熊：淺色肚子與口鼻、圓耳、雙腳往前伸，脖子繫紅色領結。面向 +Y。"""
    fur, light, k, red = "#a0673f", "#e6c39a", "#3d2b1f", "#e63946"
    sphere(1, (0, -1, 8.5), fur, scale=(7, 6.2, 8.5), subdiv=2)
    sphere(1, (0, 1.5, 8.5), light, scale=(4.6, 3.9, 5.5), subdiv=2)
    sphere(1, (0, 0, 22.6), fur, scale=(6.8, 6.0, 6.0), subdiv=2)
    for sx in (-1, 1):
        sphere(1, (4.3 * sx, -0.5, 27.0), fur, scale=(2.4, 1.4, 2.4), subdiv=1)
        sphere(1, (4.3 * sx, 0.4, 26.9), light, scale=(1.5, 0.7, 1.5), subdiv=1)
        sphere(0.65, (2.3 * sx, 5.4, 23.9), k, subdiv=1)
        limb((5.8 * sx, 0.5, 15.0), (7.3 * sx, 4.5, 8.5), 2.4, 2.2, fur, verts=8)
        sphere(2.3, (7.3 * sx, 4.5, 8.5), fur, subdiv=1)
        limb((3.6 * sx, 0, 3.0), (4.2 * sx, 6.5, 3.0), 3.0, 2.8, fur, verts=8)
        sphere(1, (4.2 * sx, 7.0, 3.3), fur, scale=(2.9, 2.0, 3.3), subdiv=2)
        sphere(1, (4.2 * sx, 8.6, 3.3), light, scale=(2.0, 0.6, 2.3), subdiv=1)
        sphere(1, (1.3 * sx, 2.0, 17.2), red, scale=(1.4, 0.6, 1.0), subdiv=1)
    sphere(1, (0, 5.3, 20.8), light, scale=(2.8, 2.0, 2.1), subdiv=2)
    sphere(1, (0, 7.2, 21.6), k, scale=(1.0, 0.6, 0.7), subdiv=1)
    sphere(0.6, (0, 2.4, 17.2), red, subdiv=1)


def _randoseru(main, trim, metal):
    """書包共用形狀：圓弧頂箱體、從頂部蓋到正面的書包蓋與金屬扣，背面有背墊與兩條肩帶。"""
    box((22, 10, 24.6), (0, 0, 12.3), main, bevel=0.8)
    cylinder(5.35, 22.4, (0, 0, 24.6), main, verts=16, rot=(0, 90, 0))
    for sx in (-1, 1):
        arc = [(11.1 * sx, 5.4 * math.cos(math.radians(t)), 24.6 + 5.4 * math.sin(math.radians(t)))
               for t in range(0, 181, 30)]
        for p1, p2 in zip(arc, arc[1:]):
            limb(p1, p2, 0.22, 0.22, trim, verts=4)
    prism(rounded([(-11.2, 7.0), (11.2, 7.0), (11.2, 24.6), (-11.2, 24.6)], [3, 3, 0, 0]), 0.7, main, offset=5.0)
    prism(rounded([(-11.5, 6.6), (11.5, 6.6), (11.5, 24.6), (-11.5, 24.6)], [3.3, 3.3, 0, 0]), 0.4, trim,
          offset=4.85)
    box((2.2, 0.5, 1.6), (0, 5.55, 8.4), metal)
    box((18, 1.2, 18), (0, -5.3, 13), trim, bevel=0.5)
    for sx in (-1, 1):
        box((3.2, 0.9, 21), (5.2 * sx, -6.0, 14.5), main, rot=(-4, 0, 0))
        box((1.6, 0.5, 1.2), (5.2 * sx, -7.15, 4.8), metal)
    box((0.5, 1.6, 1.6), (11.2, 1.5, 9.0), metal)


def build_randoseru_red():
    """紅色小學生書包（ランドセル）。正面（書包蓋）朝 +Y。"""
    _randoseru("#d62828", "#9d0208", "#c0c0c0")


def build_randoseru_black():
    """黑色小學生書包，灰色滾邊。正面（書包蓋）朝 +Y。"""
    _randoseru("#2b2b2b", "#8d99ae", "#c0c0c0")


def build_spinning_top():
    """對戰陀螺：白色尖底、深灰驅動、銀色金屬輪盤、藍色攻擊環與黃色中心。"""
    silver, blue, dblue = "#adb5bd", "#3a86ff", "#1d4ed8"
    cylinder(0.08, 0.6, (0, 0, 0.3), "#fafafa", verts=8, radius2=0.45)
    cylinder(0.45, 0.6, (0, 0, 0.9), "#3a3a4a", verts=10, radius2=1.3)
    cylinder(1.4, 0.35, (0, 0, 1.0), silver, verts=8, radius2=2.25)
    cylinder(2.25, 0.55, (0, 0, 1.45), silver, verts=8)
    cylinder(1.95, 0.6, (0, 0, 2.0), blue, verts=12)
    for i in range(3):
        a = math.radians(i * 120)
        box((0.8, 1.4, 0.5), (1.4 * math.cos(a), 1.4 * math.sin(a), 2.1), dblue, rot=(0, 0, i * 120 + 30))
        b = a + math.radians(60)
        box((0.35, 0.35, 0.1), (1.35 * math.cos(b), 1.35 * math.sin(b), 2.33), "#e63946", rot=(0, 0, i * 120))
    cylinder(0.9, 0.5, (0, 0, 2.5), "#fafafa", verts=8)
    cylinder(0.6, 0.25, (0, 0, 2.85), "#ffd166", verts=6)


def build_toy_robot():
    """方塊造型玩具機器人：灰色頭與四肢、藍色身體、紅色細節與天線。面向 +Y。"""
    grey, blue, red, dark, yellow = "#adb5bd", "#4361ee", "#e63946", "#2b2d42", "#ffd166"
    for sx in (-1, 1):
        box((2.0, 4.4, 0.9), (1.4 * sx, 0.5, 0.45), blue)
        box((1.6, 1.8, 3.0), (1.4 * sx, 0, 2.3), grey)
        cylinder(0.55, 0.6, (3.1 * sx, 0, 7.4), dark, verts=6, rot=(0, 90, 0))
        box((1.1, 1.3, 3.0), (3.4 * sx, 0.2, 5.7), grey)
        cylinder(0.55, 0.9, (3.4 * sx, 0.4, 3.85), red, verts=8)
        cylinder(0.45, 0.3, (2.35 * sx, 0, 10.0), red, verts=6, rot=(0, 90, 0))
        disc(0.55, 0.15, (0.95 * sx, 1.72, 10.2), (0, 1, 0), yellow, verts=8)
        disc(0.25, 0.1, (0.95 * sx, 1.82, 10.2), (0, 1, 0), dark, verts=6)
    box((5.4, 4.2, 4.4), (0, 0, 5.9), blue, bevel=0.3, segments=1)
    box((3.4, 0.2, 2.2), (0, 2.12, 6.2), grey)
    for x, col in ((-0.9, red), (0, yellow), (0.9, "#7bc950")):
        disc(0.3, 0.15, (x, 2.25, 6.6), (0, 1, 0), col, verts=6)
    box((2.4, 0.1, 0.2), (0, 2.25, 5.7), dark)
    box((3.0, 1.0, 3.0), (0, -2.55, 6.3), grey)
    cylinder(0.7, 0.5, (0, 0, 8.3), dark, verts=8)
    box((4.4, 3.4, 3.0), (0, 0, 10.0), grey, bevel=0.35, segments=1)
    box((1.6, 0.12, 0.3), (0, 1.73, 9.2), red)
    cylinder(0.08, 0.3, (0, 0, 11.65), dark, verts=6)
    sphere(0.25, (0, 0, 11.75), red, subdiv=1)


def build_glue_stick():
    """口紅膠：黃色筒身、藍色標籤帶、白色蓋子，底部是橘色旋轉鈕。"""
    yellow, white = "#ffd166", "#fafafa"
    cylinder(1.1, 0.6, (0, 0, 0.3), "#f4a261", verts=16)
    cylinder(1.2, 6.0, (0, 0, 3.6), yellow, verts=16)
    cylinder(1.22, 2.6, (0, 0, 3.6), "#4361ee", verts=16)
    cylinder(1.235, 0.35, (0, 0, 3.6), white, verts=16)
    cylinder(1.25, 2.3, (0, 0, 7.75), white, verts=16)
    cylinder(1.25, 0.1, (0, 0, 8.95), white, verts=16, radius2=1.0)
    cylinder(1.27, 0.15, (0, 0, 6.75), "#dee2e6", verts=16)


def build_kids_scissors():
    """兒童安全剪刀平放：粉紅色塑膠握把（一大一小兩個圈），圓頭刀片朝 +Y。"""
    pink, metal = "#ff8fab", "#ced4da"
    squash(torus(1.45, 0.45, (-1.7, -3.4, 0.45), pink, seg=14), 0.9, 1.1, 1.0)
    squash(torus(1.25, 0.45, (1.6, -3.0, 0.45), pink, seg=14), 0.9, 1.1, 1.0)
    limb((-1.25, -1.9, 0.45), (-0.2, 0.7, 0.45), 0.45, 0.4, pink, verts=6)
    limb((1.2, -1.7, 0.45), (0.2, 0.7, 0.45), 0.45, 0.4, pink, verts=6)
    blade = [(-0.35, 0.0), (0.35, 0.0), (0.3, 6.45), (0.12, 6.9), (-0.12, 6.9), (-0.3, 6.45)]
    prism(blade, 0.12, metal, loc=(0, 0.6, 0.56), rot=(0, 0, 3), axis="z")
    prism(blade, 0.12, metal, loc=(0, 0.6, 0.68), rot=(0, 0, -3), axis="z")
    cylinder(0.3, 0.35, (0, 0.6, 0.62), "#6c757d", verts=8)


def build_pencil_case():
    """平放的藍色筆盒：深藍盒身、淺藍盒蓋，蓋上有黃色星星與白色名牌。"""
    box((20.8, 6.8, 1.9), (0, 0, 0.95), "#1d4ed8", bevel=0.3)
    box((21.0, 7.0, 1.1), (0, 0, 2.45), "#4895ef", bevel=0.3)
    prism(star(1.1, 0.48), 0.12, "#ffd166", loc=(6.0, 0.3, 3.03), axis="z")
    prism(star(0.65, 0.28), 0.12, "#ffd166", loc=(8.2, -1.6, 3.03), rot=(0, 0, 20), axis="z")
    box((5.5, 2.6, 0.08), (-5.0, 0.2, 3.02), "#fafafa")
    box((1.6, 0.25, 0.6), (0, 3.55, 1.9), "#c0c0c0")


def _flower(head, color, center="#ffd166"):
    """盆花的一朵花：莖從土裡長到 head，花瓣是星形板，往外微微傾斜。"""
    hx, hy, hz = head
    d = math.hypot(hx, hy) or 1.0
    rot = (-18 * hy / d, 18 * hx / d, 0)
    limb((hx * 0.3, hy * 0.3, 19.0), head, 0.35, 0.3, "#2d6a4f", verts=6)
    prism(star(2.4, 1.15), 0.5, color, loc=head, rot=rot, axis="z")
    c = Vector(head) + Euler([math.radians(r) for r in rot]).to_matrix() @ Vector((0, 0, 0.35))
    spin(sphere(1, c, center, scale=(0.9, 0.9, 0.55), subdiv=1), rot, c)


def build_flower_pot():
    """陶土花盆：盆身加盆緣、深色土壤，綠葉一圈，幾朵紅黃粉色的花。"""
    cylinder(10.0, 15.0, (0, 0, 7.5), "#e07a5f", verts=12, radius2=12.2)
    cylinder(13.6, 4.0, (0, 0, 16.8), "#c8553d", verts=12, radius2=14.0)
    cylinder(12.8, 0.4, (0, 0, 18.9), "#6b4f3a", verts=12)
    for i in range(7):
        a = i * 2 * math.pi / 7 + 0.2
        c = (9 * math.cos(a), 9 * math.sin(a), 21)
        leaf = sphere(1, c, "#52b788" if i % 2 else "#40916c", scale=(2.6, 6.0, 0.9), subdiv=1)
        spin(leaf, (30, 0, math.degrees(a) - 90), c)
    for a in (0.9, 3.9):
        c = (4.5 * math.cos(a), 4.5 * math.sin(a), 24)
        spin(sphere(1, c, "#52b788", scale=(2.0, 4.5, 0.7), subdiv=1), (55, 0, math.degrees(a) - 90), c)
    _flower((-3.0, 2.5, 31.0), "#e63946")
    _flower((3.5, -1.0, 34.0), "#ffd166", "#fb8500")
    _flower((1.0, 4.5, 28.5), "#ff8fab")
    _flower((-1.8, -4.0, 30.0), "#e63946")


def _monstera_leaf(length, base, azimuth, tilt, color):
    """龜背芋葉：心形葉片兩側有裂口，沿中肋微微折起；葉基在 base，朝 azimuth 方向、仰角 tilt 伸出。"""
    def w(t):
        return 0.5 * math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.6

    edge = [(0.13, -0.05), (0.27, -0.01), (w(0.12), 0.12), (w(0.24), 0.24)]
    for s in (0.36, 0.52, 0.67, 0.8):
        edge += [(w(s - 0.025), s - 0.025), (0.17, s - 0.08), (w(s + 0.025), s + 0.025)]
    edge += [(w(0.9), 0.9), (w(0.96), 0.96)]
    fold = math.tan(math.radians(14))

    def v(x, y):
        return (x * length, y * length, abs(x) * fold * length)

    right = [v(0, 0.07)] + [v(x, y) for x, y in edge] + [v(0, 1.0)]
    left = [v(0, 1.0)] + [v(-x, y) for x, y in reversed(edge)] + [v(0, 0.07)]
    n = len(right)
    obj = mesh(right + left, [tuple(range(n)), tuple(range(n, 2 * n))], color, "leaf")
    obj.location = base
    obj.rotation_euler = (math.radians(tilt), 0, math.radians(azimuth) - math.pi / 2)
    return obj


def build_house_plant():
    """龜背芋盆栽：白色花盆，七片有裂口的大葉子由細莖撐起。"""
    cylinder(12.5, 30, (0, 0, 15), "#f8f9fa", verts=12, radius2=15.0)
    cylinder(15.6, 2.4, (0, 0, 29.8), "#e9ecef", verts=12)
    cylinder(14.6, 0.4, (0, 0, 31.05), "#6b4f3a", verts=12)
    leaves = ((20, 6, 60, 26, 20), (110, 6, 68, 28, 30), (200, 6, 56, 25, 15), (290, 6, 74, 28, 35),
              (65, 4, 86, 30, 50), (245, 4, 90, 28, 52), (160, 3, 98, 24, 62))
    for i, (az, r, z, length, tilt) in enumerate(leaves):
        a = math.radians(az)
        base = (r * math.cos(a), r * math.sin(a), z)
        limb((0.8 * math.cos(a), 0.8 * math.sin(a), 30.5), base, 0.9, 0.6, "#52b788", verts=6)
        _monstera_leaf(length, base, az, tilt, "#2d6a4f" if i % 2 else "#40916c")


def build_toy_train():
    """藍色玩具蒸汽火車頭：鍋爐、駕駛室、紅色車頂與排障器、黑色車輪。面向 +Y。"""
    blue, red, ink, yellow, glass = "#3a86ff", "#e63946", "#2b2d42", "#ffd166", "#a8dadc"
    box((2.6, 10.6, 0.7), (0, 0, 0.95), red)
    for y, r in ((-3.4, 0.8), (-1.3, 0.8), (2.9, 0.65)):
        for sx in (-1, 1):
            disc(r, 0.4, (1.3 * sx, y, r), (1, 0, 0), ink, verts=8)
            disc(r * 0.45, 0.06, (1.52 * sx, y, r), (1, 0, 0), yellow, verts=6)
    for sx in (-1, 1):
        box((0.08, 2.5, 0.18), (1.56 * sx, -2.35, 0.8), "#c0c0c0")
    disc(1.3, 6.0, (0, 2.0, 2.6), (0, 1, 0), blue, verts=10)
    disc(1.35, 0.4, (0, 5.1, 2.6), (0, 1, 0), ink, verts=10)
    disc(1.34, 0.25, (0, 2.9, 2.6), (0, 1, 0), yellow, verts=10)
    cylinder(0.4, 0.7, (0, 4.1, 4.05), ink, verts=8)
    cylinder(0.4, 0.2, (0, 4.1, 4.3), ink, verts=8, radius2=0.55)
    sphere(0.55, (0, 2.0, 3.85), yellow, scale=(1, 1, 0.8), subdiv=1)
    box((3.0, 3.2, 2.8), (0, -3.3, 2.7), blue, bevel=0.15, segments=1)
    box((3.2, 3.6, 0.35), (0, -3.3, 4.3), red)
    box((3.06, 1.4, 1.0), (0, -3.0, 3.25), glass)
    box((2.2, 0.1, 0.8), (0, -1.66, 3.4), glass)
    prism([(5.3, 0.25), (6.0, 0.25), (5.3, 1.3)], 2.4, red, axis="x")
    disc(0.3, 0.3, (0, 5.4, 3.55), (0, 1, 0), yellow, verts=6)
    box((0.6, 0.7, 0.4), (0, -5.65, 0.9), ink)


def build_onigiri():
    """飯糰：圓角三角形立著，正面朝 +Y，底部包一條海苔。"""
    tri = rounded([(-4.0, 0.0), (4.0, 0.0), (0.0, 7.0)], 1.1, seg=5)
    xs, zs = [p[0] for p in tri], [p[1] for p in tri]
    kx, kz, z0 = 8.0 / (max(xs) - min(xs)), 7.0 / (max(zs) - min(zs)), min(zs)
    prism([(x * kx, (z - z0) * kz) for x, z in tri], 2.9, "#fdfcf5", bevel=0.5)
    nori = "#1b2a1f"
    for sy in (-1, 1):
        box((3.2, 0.12, 2.8), (0, 1.47 * sy, 1.45), nori)
    box((3.2, 3.06, 0.12), (0, 0, 0.06), nori)


def build_kokeshi():
    """木芥子：紅色和服圓柱身體配花朵圖樣與黃色腰帶，圓頭、黑色妹妹頭與紅髮飾。面向 +Y。"""
    red, skin, k, yellow, pink = "#e63946", "#ffe8d6", "#2b2d42", "#ffd166", "#ff8fab"
    cylinder(2.05, 0.7, (0, 0, 0.35), k, verts=12)
    cylinder(2.0, 9.3, (0, 0, 5.35), red, verts=12, radius2=1.75)
    cylinder(1.9, 1.2, (0, 0, 6.0), yellow, verts=12)
    cylinder(1.8, 0.5, (0, 0, 9.75), k, verts=12)
    for z, angles in ((2.2, (30, 90, 150)), (4.0, (60, 120, 240))):
        r = 2.0 - 0.25 * (z - 0.7) / 9.3 + 0.02
        for i, deg in enumerate(angles):
            a = math.radians(deg)
            n = (math.cos(a), math.sin(a), 0)
            p = (r * n[0], r * n[1], z)
            disc(0.62, 0.12, p, n, pink if i % 2 == 0 else "#fafafa", verts=6)
            disc(0.22, 0.14, p, n, yellow, verts=4)
    sphere(2.45, (0, 0, 12.4), skin, subdiv=2)
    sphere(2.5, (0, -0.3, 12.55), k, subdiv=2)
    sphere(1, (0, 1.2, 13.8), k, scale=(1.7, 1.0, 0.95), subdiv=2)
    for sx in (-1, 1):
        sphere(0.5, (2.0 * sx, 0.6, 13.65), red, subdiv=1)
        box((0.6, 0.1, 0.12), (0.75 * sx, 2.33, 12.25), k)
        disc(0.32, 0.06, (1.3 * sx, 1.95, 11.65), (0.53 * sx, 0.79, -0.3), pink, verts=6)
    sphere(0.17, (0, 2.2, 11.35), red, subdiv=1)


def build_paper_crane():
    """粉紅色紙鶴：菱形身體、向上張開的雙翼、細長的頸與尾，頭部前端下折。面向 +Y。"""
    v = {"B": (0, 0, 0), "F": (0, 1.0, 0.75), "R": (0, -1.0, 0.75), "SL": (-0.55, 0, 0.85),
         "SR": (0.55, 0, 0.85), "T": (0, 0, 1.1), "HF": (0, 0.7, 1.0), "HR": (0, -0.65, 1.0),
         "WL": (-2.0, -0.45, 2.3), "ML": (-0.95, 0.35, 1.5), "WR": (2.0, -0.45, 2.3), "MR": (0.95, 0.35, 1.5),
         "NL": (-0.12, 0.45, 0.55), "NR": (0.12, 0.45, 0.55), "NF": (0, 1.05, 0.8), "N": (0, 2.55, 2.75),
         "H": (0, 3.0, 2.35), "HL": (-0.07, 2.35, 2.45), "HX": (0.07, 2.35, 2.45),
         "TL": (-0.12, -0.45, 0.55), "TR": (0.12, -0.45, 0.55), "TF": (0, -1.05, 0.8), "TT": (0, -3.0, 3.0)}
    faces = [("B", "F", "SR"), ("B", "SR", "R"), ("B", "R", "SL"), ("B", "SL", "F"),
             ("T", "SR", "F"), ("T", "R", "SR"), ("T", "SL", "R"), ("T", "F", "SL"),
             ("HF", "ML", "WL"), ("HF", "WL", "HR"), ("HF", "WR", "MR"), ("HF", "HR", "WR"),
             ("NL", "NF", "N"), ("NR", "N", "NF"), ("NL", "N", "NR"), ("HL", "N", "H"), ("HX", "H", "N"),
             ("TL", "TT", "TF"), ("TR", "TF", "TT"), ("TL", "TR", "TT")]
    keys = list(v)
    mesh([v[key] for key in keys], [tuple(keys.index(c) for c in f) for f in faces], "#ff8fab", "crane")


def build_yoyo():
    """溜溜球：兩片黃色圓盤、外側紅色蓋片，中間纏著白線。立在地上，軸心沿 Y。"""
    yellow, red, white = "#ffd166", "#e63946", "#fafafa"
    for sy in (-1, 1):
        disc(2.75, 0.95, (0, 0.8 * sy, 2.75), (0, sy, 0), yellow, verts=16)
        disc(2.75, 0.35, (0, 1.45 * sy, 2.75), (0, sy, 0), yellow, verts=16, radius2=2.25)
        disc(1.9, 0.08, (0, 1.66 * sy, 2.75), (0, sy, 0), red, verts=16)
        disc(0.6, 0.1, (0, 1.72 * sy, 2.75), (0, sy, 0), white, verts=10)
    disc(0.95, 0.7, (0, 0, 2.75), (0, 1, 0), white, verts=12)


def build_rubiks_cube():
    """3x3 魔術方塊：黑色本體加 54 片彩色方片（方片合併成一個物件）。"""
    h = 2.85
    box((5.64, 5.64, 5.64), (0, 0, h), "#1b1b1b", bevel=0.2)
    colors = {(0, 0, 1): "#fafafa", (0, 0, -1): "#ffd166", (0, 1, 0): "#e63946", (0, -1, 0): "#fb8500",
              (1, 0, 0): "#1d4ed8", (-1, 0, 0): "#38b000"}
    tiles = []
    for n, col in colors.items():
        n = Vector(n)
        u = Vector((1, 0, 0)) if abs(n.x) < 0.5 else Vector((0, 1, 0))
        v = n.cross(u)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                tiles.append(tile((1.62, 1.62), Vector((0, 0, h)) + n * h + u * (1.86 * i) + v * (1.86 * j), n, col))
    join(tiles, "tiles")


def build_maneki_neko():
    """招財貓擺飾：白色坐姿，舉起左手，右手抱金幣，紅項圈配金鈴，頭上有橘黑花斑。面向 +Y。"""
    w, red, gold, k, p, o = "#fafafa", "#e63946", "#ffd166", "#2b2d42", "#ff8fab", "#f4a259"
    body = flatten_bottom(sphere(1, (0, 0, 2.4), w, scale=(2.5, 2.2, 2.6), subdiv=2))
    paint(body, o, near(((1.8, -1.6, 3.2), 1.5)))
    head = sphere(1, (0, 0.25, 6.2), w, scale=(2.3, 2.0, 1.95), subdiv=2)
    paint(head, o, lambda c: c.x < -0.9 and c.z > 6.9)
    paint(head, k, lambda c: c.x > 1.0 and c.z > 7.0 and c.y < 1.5)
    for sx, col in ((-1, o), (1, k)):
        rot = (0, 15 * sx, 0)
        prism([(-0.75, 0), (0.75, 0), (0.1 * sx, 1.35)], 0.5, col, loc=(1.25 * sx, 0.2, 7.55), rot=rot)
        prism([(-0.42, 0.18), (0.42, 0.18), (0.08 * sx, 0.95)], 0.12, p, loc=(1.25 * sx, 0.2, 7.55), rot=rot,
              offset=0.28)
        sphere(1, (0.8 * sx, 2.05, 6.5), k, scale=(0.26, 0.14, 0.3), subdiv=1)
        for dz in (0.12, -0.18):
            limb((0.6 * sx, 2.15, 5.85 + dz), (2.6 * sx, 1.7, 5.8 + dz * 2), 0.035, 0.03, "#adb5bd", verts=4)
    sphere(1, (0, 2.25, 6.0), p, scale=(0.22, 0.12, 0.15), subdiv=1)
    limb((-1.7, 0.6, 4.4), (-2.3, 0.9, 6.9), 0.62, 0.55, w, verts=8)
    sphere(0.72, (-2.35, 0.95, 7.2), w, subdiv=1)
    disc(0.32, 0.08, (-2.35, 1.62, 7.2), (0, 1, 0), p, verts=8)
    limb((1.5, 0.9, 4.0), (1.0, 1.9, 2.5), 0.55, 0.5, w, verts=8)
    sphere(0.6, (0.95, 2.0, 2.4), w, subdiv=1)
    squash(disc(1.05, 0.15, (0.1, 2.25, 2.6), (0, 1, 0), gold, verts=12), 0.72, 1.0, 1.0)
    squash(torus(1.4, 0.22, (0, 0.2, 4.55), red, mseg=5), 1.0, 0.9, 1.0)
    sphere(0.42, (0, 1.55, 4.3), gold, subdiv=1)


def build_toy_piano():
    """兒童玩具鋼琴：粉紅琴身與淺粉上蓋，前方 15 個白鍵與 10 個黑鍵，正面三個彩色圓點。面向 +Y。"""
    pink, light = "#ff8fab", "#ffc2d1"
    box((40, 17, 18), (0, -4.0, 9), pink, bevel=0.6)
    box((40.4, 17.4, 2.0), (0, -4.0, 19.0), light)
    box((40, 8, 7.5), (0, 8.5, 3.75), pink)
    for sx in (-1, 1):
        box((2.0, 8.0, 3.5), (19.0 * sx, 8.5, 8.75), light)
    keys = [box((2.25, 7.4, 1.2), (-16.8 + i * 2.4, 8.4, 8.1), "#fafafa") for i in range(15)]
    for i in (0, 1, 3, 4, 5, 7, 8, 10, 11, 12):
        keys.append(box((1.3, 4.4, 1.2), (-16.8 + (i + 0.5) * 2.4, 6.6, 9.1), "#2b2d42"))
    join(keys, "keys")
    for x, col in ((-6, "#e63946"), (0, "#ffd166"), (6, "#5bc0eb")):
        disc(1.6, 0.2, (x, 4.6, 13.0), (0, 1, 0), col, verts=12)


def build_soccer_ball():
    """4 號兒童足球：截角二十面體（12 黑五邊形、20 白六邊形）細分後推成球面。"""
    r = 10.0
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    bmesh.ops.bevel(bm, geom=list(bm.verts), offset=100 / 3, offset_type="PERCENT", segments=1,
                    affect="VERTICES", profile=0.5)
    for f in bm.faces:
        f.material_index = 1 if len(f.verts) == 5 else 0
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1)
    bmesh.ops.poke(bm, faces=list(bm.faces))
    for v in bm.verts:
        v.co = v.co.normalized() * r
    low = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= low
    me = bpy.data.meshes.new("ball")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("ball", me)
    bpy.context.scene.collection.objects.link(obj)
    finish(obj, "#fafafa")
    obj.data.materials.append(material("#2b2d42"))


def build_teddy_small():
    """粉紅色鑰匙圈小熊：大頭、張開雙手，左耳綁紅色蝴蝶結，頭頂有銀色吊環。面向 +Y。"""
    pink, light, k, red = "#ffafcc", "#ffe5ec", "#2b2d42", "#e63946"
    sphere(1, (0, -0.2, 1.75), pink, scale=(2.0, 1.7, 1.75), subdiv=2)
    sphere(1, (0, 0.55, 1.6), light, scale=(1.3, 1.15, 1.2), subdiv=1)
    sphere(1, (0, 0.1, 5.0), pink, scale=(3.0, 2.2, 2.2), subdiv=2)
    for sx in (-1, 1):
        sphere(1, (1.15 * sx, 1.0, 0.65), pink, scale=(0.75, 1.0, 0.65), subdiv=1)
        sphere(1, (1.15 * sx, 1.85, 0.65), light, scale=(0.5, 0.25, 0.45), subdiv=1)
        limb((1.5 * sx, 0.2, 2.6), (3.2 * sx, 0.5, 3.1), 0.55, 0.5, pink, verts=8)
        sphere(0.6, (3.25 * sx, 0.5, 3.1), pink, subdiv=1)
        sphere(0.85, (2.1 * sx, -0.1, 6.5), pink, scale=(1, 0.6, 1), subdiv=1)
        sphere(0.5, (2.1 * sx, 0.35, 6.45), light, scale=(1, 0.5, 1), subdiv=1)
        sphere(0.27, (0.95 * sx, 2.12, 5.4), k, subdiv=1)
        sphere(1, (-1.5 + 0.4 * sx, 0.95, 6.75), red, scale=(0.4, 0.2, 0.3), subdiv=1)
    sphere(0.18, (-1.5, 1.05, 6.75), red, subdiv=1)
    sphere(1, (0, 2.05, 4.5), light, scale=(1.0, 0.65, 0.72), subdiv=1)
    sphere(1, (0, 2.62, 4.75), k, scale=(0.32, 0.2, 0.24), subdiv=1)
    torus(0.42, 0.1, (0, 0, 7.45), "#c0c0c0", rot=(0, 90, 0), seg=10, mseg=4)


def build_marble():
    """玻璃彈珠：藍色球體，斜斜纏著一圈白色漩紋帶與一圈淺藍細帶。"""
    sphere(0.85, (0, 0, 0.85), "#3a86ff", subdiv=2)
    disc(0.87, 0.16, (0, 0, 0.85), (0.5, 0.3, 0.81), "#fafafa", verts=16)
    disc(0.865, 0.08, (0, 0, 0.85), (-0.4, 0.6, 0.69), "#a2d2ff", verts=16)


RECIPES = {
    "thumbtack": build_thumbtack,
    "die": build_die,
    "eraser": build_eraser,
    "tangerine": build_tangerine,
    "pusher": build_pusher,
    "cat": build_cat,
    "dog": build_dog,
    "minicar": build_minicar,
    "dinosaur": build_dinosaur,
    "daruma": build_daruma,
    "kendama": build_kendama,
    "gacha_capsule": build_gacha_capsule,
    "plush_bear": build_plush_bear,
    "randoseru_red": build_randoseru_red,
    "randoseru_black": build_randoseru_black,
    "spinning_top": build_spinning_top,
    "toy_robot": build_toy_robot,
    "glue_stick": build_glue_stick,
    "kids_scissors": build_kids_scissors,
    "pencil_case": build_pencil_case,
    "flower_pot": build_flower_pot,
    "house_plant": build_house_plant,
    "toy_train": build_toy_train,
    "onigiri": build_onigiri,
    "kokeshi": build_kokeshi,
    "paper_crane": build_paper_crane,
    "yoyo": build_yoyo,
    "rubiks_cube": build_rubiks_cube,
    "maneki_neko": build_maneki_neko,
    "toy_piano": build_toy_piano,
    "soccer_ball": build_soccer_ball,
    "teddy_small": build_teddy_small,
    "marble": build_marble,
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
