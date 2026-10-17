"""場景配置檔產生工具：用 Python 寫場景，輸出 Godot 讀的 data/levels/*.json。

各關卡各自一個腳本（例如 tools/levels/build_dongshan_home.py），import 本模組：

    from levelkit import Level
    lv = Level("dongshan_home", "槿寶的家", "說明…")
    lv.floor("客廳", 0, 0, 500, 400, pattern="terrazzo", color="#e8e2d6")
    lv.wall((0, 0), (500, 0), gaps=[(200, 290)])
    lv.stairs_up("書桌樓梯", top=(120, 72, 300), facing=180, width=24)
    lv.place("desk_study", 120, 0, 280, rot=180)
    lv.spawn("desk_top", (80, 260, 90, 50), y=72, items={"crayon": 8})
    lv.save()

單位一律是公分；x 往東、z 往南、y 往上。欄位意義見 godot/scripts/world/level_builder.gd 開頭的說明。
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVEL_DIR = ROOT / "godot" / "data" / "levels"


class Level:
    def __init__(self, level_id, name, note=""):
        self.path = LEVEL_DIR / f"{level_id}.json"
        self.d = {
            "_note": note,
            "id": level_id,
            "name": name,
            "areas": [],
            "start": {"pos": [0, 1, 0], "yaw_deg": 0},
            "floors": [],
            "walls": [],
            "blocks": [],
            "ramps": [],
            "stairs": [],
            "decor": [],
            "petals": [],
            "placements": [],
            "spawns": [],
            "gates": [],
        }

    # ---------- 建物 ----------

    def floor(self, name, x, z, w, d, y=0.0, pattern="plain", color="#d9b98c", repeat=90, thickness=None):
        f = {"name": name, "rect": [x, z, w, d], "y": y, "pattern": pattern, "color": color, "repeat": repeat}
        if thickness is not None:
            f["thickness"] = thickness
        self.d["floors"].append(f)
        return f

    def wall(self, a, b, height=240, thickness=10, gaps=None, color=None, y=0.0):
        """a、b 為牆中線兩端 (x, z)。gaps：[(起點距離, 終點距離[, 門楣高度]), ...]，距離從 a 量起。"""
        w = {"from": list(a), "to": list(b), "height": height, "thickness": thickness}
        if gaps:
            w["gaps"] = [list(g) for g in gaps]
        if color:
            w["color"] = color
        if y:
            w["y"] = y
        self.d["walls"].append(w)
        return w

    def block(self, name, x, y, z, w, h, d, color="#cccccc", pattern=None, repeat=90, rot=0):
        """實心方塊，(x, y, z) 是底面中心。"""
        b = {"name": name, "pos": [x, y, z], "size": [w, h, d], "color": color}
        if pattern:
            b["pattern"] = pattern
            b["repeat"] = repeat
        if rot:
            b["rot"] = rot
        self.d["blocks"].append(b)
        return b

    def ramp(self, name, a, b, width=20, thickness=1.5, color="#d9b26f"):
        r = {"name": name, "from": list(a), "to": list(b), "width": width, "thickness": thickness, "color": color}
        self.d["ramps"].append(r)
        return r

    def stairs(self, name, a, b, width=24, step=3.0, style="lego", colors=None):
        """積木樓梯：a 為底部起點（地面）、b 為頂端（平台邊緣），都是 (x, y, z)。"""
        s = {"name": name, "from": list(a), "to": list(b), "width": width, "step": step, "style": style}
        if colors:
            s["colors"] = colors
        self.d["stairs"].append(s)
        return s

    def stairs_up(self, name, top, facing, width=24, slope_deg=30.0, base_y=0.0, step=3.0, style="lego", colors=None):
        """從平台邊緣 top=(x, y, z) 往 facing 方向（度，0 = 往北 -z、90 = 往東 +x、180 = 往南 +z）
        鋪一座下到 base_y 的樓梯，坡度 slope_deg。回傳樓梯底部的位置。"""
        rise = top[1] - base_y
        run = rise / math.tan(math.radians(slope_deg))
        dx, dz = direction(facing)
        bottom = (round(top[0] + dx * run, 1), base_y, round(top[2] + dz * run, 1))
        self.stairs(name, bottom, top, width=width, step=step, style=style, colors=colors)
        return bottom

    def decor(self, name, shape, pos, size, color, rot=0, pattern=None, no_shadow=False):
        d = {"name": name, "shape": shape, "pos": list(pos), "size": list(size), "color": color, "rot": rot}
        if pattern:
            d["pattern"] = pattern
        if no_shadow:
            d["no_shadow"] = True
        self.d["decor"].append(d)
        return d

    def decor_item(self, name, item, pos, rot=0, scale=1.0):
        d = {"name": name, "item": item, "pos": list(pos), "rot": rot, "scale": scale}
        self.d["decor"].append(d)
        return d

    def petals(self, name, pos, size, color="#ffc8dd", amount=40, petal=1.6, fall=18.0):
        p = {"name": name, "pos": list(pos), "size": list(size), "color": color, "amount": amount, "petal": petal, "fall": fall}
        self.d["petals"].append(p)
        return p

    # ---------- 物件 ----------

    def place(self, item, x, y, z, rot=0, color=None, roam=None, blocks_spawn=True):
        p = {"item": item, "pos": [x, y, z], "rot": rot}
        if color:
            p["color"] = color
        if roam:
            p["roam"] = list(roam)
        if not blocks_spawn:
            p["blocks_spawn"] = False
        self.d["placements"].append(p)
        return p

    def spawn(self, zone, rect, y, items, avoid_furniture=None, exclude=None):
        """在 rect=(x, z, 寬, 深) 範圍、高度 y 隨機散布 items={物件 id: 數量}。"""
        s = {"zone": zone, "rect": list(rect), "y": y, "items": dict(items)}
        if avoid_furniture is not None:
            s["avoid_furniture"] = avoid_furniture
        if exclude:
            s["exclude"] = [list(e) for e in exclude]
        self.d["spawns"].append(s)
        return s

    def gate(self, gate_id, name, pos, size, open_at_cm, message="", color="#f1faee", slide=None, style=None, rot=0):
        g = {"id": gate_id, "name": name, "pos": list(pos), "size": list(size), "color": color,
             "open_at_cm": open_at_cm, "message": message}
        if slide:
            g["slide"] = list(slide)
        if style:
            g["style"] = style
        if rot:
            g["rot"] = rot
        self.d["gates"].append(g)
        return g

    def area(self, name, x, z, w, d):
        self.d["areas"].append({"name": name, "rect": [x, z, w, d]})

    # ---------- 關卡設定 ----------

    def set_start(self, pos, yaw_deg):
        self.d["start"] = {"pos": list(pos), "yaw_deg": yaw_deg}

    def set_rescue(self, pos, yaw_deg=0):
        self.d["rescue"] = {"pos": list(pos), "yaw_deg": yaw_deg}

    def set_env(self, sky="#bfe6ff", fog_color="#dfefff", fog_per_d=0.0):
        self.d["env"] = {"sky": sky, "fog_color": fog_color, "fog_per_d": fog_per_d}

    def set_stage(self, **kw):
        """關卡設定（start_cm、goal_cm、time_sec、comet_sec、seed、music、intro、zones、gates、tuning、grades）。"""
        self.d["stage"] = kw

    def zones(self):
        return [s["zone"] for s in self.d["spawns"]]

    def save(self, path=None):
        out = Path(path) if path else self.path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.d, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")
        counts = sum(sum(s["items"].values()) for s in self.d["spawns"])
        print(f"[levelkit] {out.name}：地板 {len(self.d['floors'])}、牆 {len(self.d['walls'])}、"
              f"樓梯 {len(self.d['stairs'])}、擺放 {len(self.d['placements'])}、散布 {counts} 件")
        return out


def direction(facing_deg):
    """facing（度）轉成 (dx, dz)：0 = 北（-z）、90 = 東（+x）、180 = 南（+z）、270 = 西（-x）。"""
    a = math.radians(facing_deg)
    return (round(math.sin(a), 6), round(-math.cos(a), 6))
