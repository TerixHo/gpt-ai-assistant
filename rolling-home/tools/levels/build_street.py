"""第 2 關「上學的路」：產生物件定義 data/items/street.json 與場景配置 data/levels/street.json。

故事：槿寶在家裡長到 1 公尺，滾出家門，沿著宜蘭冬山鄉間的農路一路滾到學校大門，目標 3 公尺。
沿路是稻田、灌溉水圳、農舍、土地公小廟、雜貨店、文旦園、鴨寮，終點是小學大門。

執行（在 rolling-home 資料夾）：
    python3 tools/levels/build_street.py

單位公分；x 往東、z 往南、y 往上。主路沿著 x 軸從西（槿寶家）往東（學校）。
本檔也提供物件定義的小工具（part、item、budget），第 3 關的 build_school.py 會 import 使用。
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from levelkit import Level  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ITEMS_DIR = ROOT / "godot" / "data" / "items"


# ---------- 物件定義小工具 ----------

def part(shape, dims, pos, color, rot=None, collide=True, name=None, tint=False):
    """一個零件。pos 是零件中心（相對於物件底面中心）；rot 是 [x, y, z] 度。"""
    p = {"shape": shape, "dims": [round(float(v), 2) for v in dims], "pos": [round(float(v), 2) for v in pos], "color": color}
    if rot:
        p["rot"] = list(rot)
    if not collide:
        p["collide"] = False
    if name:
        p["name"] = name
    if tint:
        p["tint"] = True
    return p


def item(item_id, name, name_en, category, dims, parts=None, shape="parts", color="#cccccc", fill=0.5,
         flavor=None, sfx=None, model=None, critter=None, colors=None, pickable=True, size=None):
    d = {"id": item_id, "name": name, "name_en": name_en, "category": category}
    if parts:
        d["shape"] = "parts"
        d["parts"] = parts
    else:
        d["shape"] = shape
        d["color"] = color
    d["dims"] = [round(float(v), 2) for v in dims]
    d["fill"] = fill
    if colors:
        d["colors"] = colors
    if model:
        d["model"] = model
    if critter:
        d["critter"] = critter
    if sfx:
        d["sfx"] = sfx
    if size is not None:
        d["size"] = size
    if not pickable:
        d["pickable"] = False
    if flavor:
        d["flavor"] = flavor
    return d


def size_of(d):
    if "size" in d:
        return float(d["size"])
    a = sorted(d["dims"])
    return math.sqrt(a[2] * a[1])


def sphere_volume(dia):
    return math.pi / 6.0 * dia ** 3


def save_items(filename, note, items):
    ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    out = ITEMS_DIR / filename
    out.write_text(json.dumps({"_note": note, "items": items}, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")
    print(f"[items] {out.name}：{len(items)} 種物件")


def budget(level, all_items, start_cm, goal_cm, buckets):
    """依散布與擺放的數量，統計各尺寸區間的件數與可增加的體積（與 Katamari 的成長公式相同）。"""
    defs = {d["id"]: d for d in all_items}
    counts = {}
    for s in level.d["spawns"]:
        for k, n in s["items"].items():
            counts[k] = counts.get(k, 0) + n
    for p in level.d["placements"]:
        counts[p["item"]] = counts.get(p["item"], 0) + 1
    rows = {b: [0, 0.0] for b in buckets}
    total_n = 0
    usable = 0.0
    for k, n in counts.items():
        d = defs.get(k)
        if d is None or d.get("pickable", True) is False:
            continue
        s = size_of(d)
        total_n += n
        vol = sphere_volume(s) * d.get("fill", 0.5) * n
        if s <= goal_cm * 0.7:
            usable += vol
        for lo, hi in buckets:
            if lo <= s < hi:
                rows[(lo, hi)][0] += n
                rows[(lo, hi)][1] += vol
    need = sphere_volume(goal_cm) - sphere_volume(start_cm)
    print(f"[budget] 物件總數 {total_n}（不可黏的另計）；需要體積 {need / 1e6:.2f} m³，"
          f"目標內可黏總體積 {usable / 1e6:.2f} m³（{usable / need:.2f} 倍）")
    for (lo, hi), (n, v) in rows.items():
        print(f"[budget]   {lo:>5}–{hi:<5} cm：{n:4d} 件，{v / 1e6:8.2f} m³")
    return total_n


# ---------- 共用造型 ----------

def wheel(dia, width, pos, color="#212529", name=None):
    """沿 x 軸的輪子（車子往 -z 前進）。"""
    return part("cylinder", [dia, width, dia], pos, color, rot=[0, 0, 90], name=name)


# ---------- 第 2 關物件 ----------

def street_items():
    it = []
    A = it.append

    # 田裡與農家的小東西（20 到 70 公分）
    A(item("st_pomelo", "文旦", "Pomelo", "水果", [16, 15, 16], [
        part("sphere", [16, 15, 16], [0, 7.5, 0], "#d9e36a"),
        part("cone", [3, 3, 3], [0, 16, 0], "#6a994e", collide=False)],
        fill=0.7, sfx="orange", flavor="冬山的文旦，白露前後採收，中秋節最好吃。"))
    A(item("st_pomelo_box", "文旦禮盒", "Pomelo Gift Box", "水果", [42, 26, 32], [
        part("box", [42, 22, 32], [0, 11, 0], "#f4d35e"),
        part("box", [42, 4, 32], [0, 24, 0], "#2d6a4f"),
        part("sphere", [12, 10, 12], [-10, 27, 0], "#d9e36a", collide=False)],
        fill=0.6, flavor="一盒六顆，要寄給台北的阿姨。"))
    A(item("st_bucket", "水桶", "Bucket", "農具", [30, 34, 30], [
        part("cylinder", [30, 32, 30], [0, 16, 0], "#3a86ff", tint=True),
        part("box", [30, 2, 2], [0, 33, 0], "#6c757d", collide=False)],
        fill=0.4, colors=["#3a86ff", "#ff006e", "#ffbe0b", "#8ac926"]))
    A(item("st_cabbage", "高麗菜", "Cabbage", "蔬菜", [26, 20, 26], shape="sphere", color="#a7c957", fill=0.6,
         flavor="又大又圓的高麗菜，要拿去煮火鍋。"))
    A(item("st_green_onion", "一把青蔥", "Green Onions", "蔬菜", [10, 62, 10], [
        part("cylinder", [9, 26, 9], [0, 13, 0], "#f1faee"),
        part("cylinder", [10, 36, 10], [0, 44, 0], "#52b788")],
        fill=0.4))
    A(item("st_watermelon", "西瓜", "Watermelon", "水果", [34, 30, 34], shape="sphere", color="#2d6a4f", fill=0.7))
    A(item("st_rice_sack", "米袋", "Rice Sack", "農具", [45, 20, 70], [
        part("box", [45, 20, 70], [0, 10, 0], "#f1e3c6"),
        part("box", [46, 21, 8], [0, 10, -15], "#e63946", collide=False)],
        fill=0.6, flavor="蘭陽平原種出來的米，一袋好重。"))
    A(item("st_helmet", "安全帽", "Scooter Helmet", "交通", [28, 24, 32], [
        part("sphere", [28, 24, 32], [0, 12, 0], "#ffbe0b", tint=True),
        part("box", [20, 4, 3], [0, 9, -15], "#212529", collide=False)],
        fill=0.4, colors=["#ffbe0b", "#e63946", "#f8f9fa", "#3a86ff", "#ff8fab"]))
    A(item("st_rain_boots", "雨鞋", "Rain Boots", "農具", [26, 35, 28], [
        part("box", [11, 35, 14], [-6, 17.5, 0], "#ffd60a"),
        part("box", [11, 35, 14], [6, 17.5, 3], "#ffd60a"),
        part("box", [11, 8, 26], [-6, 4, -6], "#ffd60a")],
        fill=0.3))
    A(item("st_bamboo_hat", "斗笠", "Bamboo Hat", "農具", [50, 18, 50], shape="cone", color="#d4a373", fill=0.3,
         flavor="下田戴的斗笠，遮太陽也遮雨。"))
    A(item("st_hoe", "鋤頭", "Hoe", "農具", [22, 6, 130], [
        part("cylinder", [4, 120, 4], [0, 3, 6], "#b08968", rot=[90, 0, 0]),
        part("box", [22, 3, 12], [0, 2, -58], "#6c757d")],
        fill=0.2))
    A(item("st_stool", "塑膠凳", "Plastic Stool", "生活", [34, 45, 34], shape="cylinder", color="#e63946", fill=0.3,
         colors=["#e63946", "#3a86ff", "#8ac926", "#ffbe0b"], flavor="廟口和攤子都看得到的塑膠凳。"))
    A(item("st_plastic_chair", "紅色塑膠椅", "Red Plastic Chair", "生活", [45, 85, 45], [
        part("box", [40, 41, 38], [0, 20.5, 0], "#d62828"),
        part("box", [45, 4, 42], [0, 43, 0], "#d62828"),
        part("box", [45, 40, 4], [0, 65, 20], "#d62828")],
        fill=0.3, flavor="辦桌、廟會都少不了的紅色塑膠椅。"))
    A(item("st_potted_plant", "大盆栽", "Big Potted Plant", "植物", [60, 80, 60], [
        part("cylinder", [40, 35, 40], [0, 17.5, 0], "#bc6c25"),
        part("sphere", [60, 50, 60], [0, 58, 0], "#52b788")],
        fill=0.4))
    A(item("st_brick_stack", "一疊紅磚", "Stack of Bricks", "建材", [40, 30, 25], shape="box", color="#b5523b", fill=0.8))
    A(item("st_traffic_cone", "交通錐", "Traffic Cone", "交通", [36, 68, 36], [
        part("box", [36, 3, 36], [0, 1.5, 0], "#fb8500"),
        part("cone", [30, 65, 30], [0, 35.5, 0], "#fb8500"),
        part("cylinder", [17, 10, 17], [0, 42, 0], "#f8f9fa", collide=False)],
        fill=0.3))
    A(item("st_trash_bin", "路邊垃圾桶", "Street Trash Bin", "生活", [50, 92, 50], [
        part("cylinder", [50, 85, 50], [0, 42.5, 0], "#2a9d8f"),
        part("cylinder", [54, 7, 54], [0, 88.5, 0], "#264653")],
        fill=0.4))
    A(item("st_gas_tank", "瓦斯桶", "Gas Cylinder", "生活", [32, 72, 32], [
        part("cylinder", [32, 62, 32], [0, 31, 0], "#adb5bd"),
        part("cylinder", [20, 10, 20], [0, 67, 0], "#6c757d")],
        fill=0.5))
    A(item("st_frog", "青蛙", "Frog", "動物", [12, 8, 14], [
        part("sphere", [12, 8, 14], [0, 4, 0], "#70e000"),
        part("sphere", [4, 4, 4], [-3, 8, -5], "#f8f9fa", collide=False),
        part("sphere", [4, 4, 4], [3, 8, -5], "#f8f9fa", collide=False)],
        fill=0.6, sfx="frog", flavor="稻田裡呱呱叫的青蛙。"))
    A(item("st_duck", "鴨子", "Duck", "動物", [22, 34, 38], [
        part("sphere", [22, 18, 30], [0, 14, 2], "#f8f9fa"),
        part("sphere", [12, 12, 12], [0, 27, -11], "#f8f9fa", name="head"),
        part("box", [6, 3, 8], [0, 26, -19], "#fb8500", collide=False),
        part("box", [3, 6, 3], [-5, 3, 2], "#fb8500", name="leg_fl"),
        part("box", [3, 6, 3], [5, 3, 2], "#fb8500", name="leg_fr")],
        fill=0.5, critter={"kind": "dog", "walk": 26, "run": 85, "sight": 260, "paw_cooldown": 99, "sound": "duck"},
        flavor="鴨寮跑出來的鴨子，排成一列散步。"))
    A(item("st_chicken", "雞", "Chicken", "動物", [22, 38, 34], [
        part("sphere", [22, 20, 28], [0, 17, 2], "#bc6c25"),
        part("sphere", [12, 12, 12], [0, 31, -9], "#bc6c25", name="head"),
        part("box", [3, 6, 8], [0, 39, -9], "#d62828", collide=False),
        part("box", [3, 7, 3], [-5, 3.5, 2], "#ffbe0b", name="leg_fl"),
        part("box", [3, 7, 3], [5, 3.5, 2], "#ffbe0b", name="leg_fr")],
        fill=0.5, critter={"kind": "dog", "walk": 30, "run": 110, "sight": 240, "paw_cooldown": 99, "sound": "chicken"},
        flavor="農家養的土雞，跑起來超快。"))
    A(item("st_egret", "白鷺鷥", "Egret", "動物", [30, 80, 50], [
        part("sphere", [18, 22, 36], [0, 46, 4], "#f8f9fa"),
        part("cylinder", [5, 26, 5], [0, 62, -12], "#f8f9fa", rot=[-25, 0, 0]),
        part("sphere", [9, 8, 12], [0, 76, -18], "#f8f9fa", name="head"),
        part("box", [2, 2, 12], [0, 76, -28], "#ffbe0b", collide=False),
        part("cylinder", [3, 38, 3], [-4, 19, 4], "#212529", name="leg_fl"),
        part("cylinder", [3, 38, 3], [4, 19, 4], "#212529", name="leg_fr")],
        fill=0.3, model="st_egret",
        critter={"kind": "dog", "walk": 18, "run": 140, "sight": 320, "paw_cooldown": 99, "sound": "chirp"},
        flavor="稻田裡找小蟲吃的白鷺鷥，冬山的濕地很常見。"))
    A(item("st_dog_local", "黃色土狗", "Village Dog", "動物", [30, 55, 75], shape="box", color="#d08c60", fill=0.4,
         model="dog", size=60.0,
         critter={"kind": "dog", "walk": 40, "run": 160, "sight": 300, "paw_cooldown": 99, "sound": "woof"},
         flavor="巷口的黃狗，大家都叫牠「阿黃」。"))
    A(item("st_cat_local", "三花貓", "Village Cat", "動物", [22, 32, 48], shape="box", color="#fefae0", fill=0.4,
         model="cat", size=32.0,
         critter={"kind": "cat", "walk": 30, "run": 130, "sight": 260, "paw_cooldown": 99, "sound": "meow"},
         flavor="雜貨店的貓，常在冰櫃上睡午覺。"))
    A(item("st_mailbox_pair", "郵筒（紅綠兩個）", "Mailboxes", "街道", [100, 130, 45], [
        part("box", [45, 105, 40], [-26, 52.5, 0], "#2b9348"),
        part("cylinder", [45, 14, 40], [-26, 111, 0], "#2b9348", rot=[90, 0, 0]),
        part("box", [45, 105, 40], [26, 52.5, 0], "#d62828"),
        part("cylinder", [45, 14, 40], [26, 111, 0], "#d62828", rot=[90, 0, 0])],
        fill=0.4, flavor="綠色寄平信，紅色寄限時。"))
    A(item("st_water_jar", "大水缸", "Water Jar", "生活", [80, 82, 80], [
        part("sphere", [80, 72, 80], [0, 38, 0], "#8d6e4f"),
        part("cylinder", [56, 10, 56], [0, 77, 0], "#7f5539")],
        fill=0.5, flavor="以前用來接雨水的大水缸。"))
    A(item("st_wheelbarrow", "手推車", "Wheelbarrow", "農具", [60, 70, 150], [
        part("box", [60, 30, 90], [0, 50, -5], "#3a86ff", tint=True),
        wheel(35, 10, [0, 17.5, -55]),
        part("box", [50, 4, 60], [0, 45, 50], "#6c757d")],
        fill=0.3, colors=["#3a86ff", "#e63946", "#2b9348"]))
    A(item("st_bike", "腳踏車", "Bicycle", "交通", [55, 100, 170], [
        part("box", [8, 70, 160], [0, 35, 0], "#e63946"),
        part("box", [55, 8, 8], [0, 96, -60], "#adb5bd")],
        fill=0.2, model="st_bike", sfx="bike_bell", flavor="上學騎的腳踏車，鈴鐺叮叮響。"))
    A(item("st_scooter", "機車", "Scooter", "交通", [65, 110, 185], [
        part("box", [55, 60, 170], [0, 40, 0], "#f8f9fa"),
        part("box", [60, 50, 40], [0, 85, -60], "#f8f9fa")],
        fill=0.35, model="st_scooter", sfx="car_horn", flavor="鄉下每家都有的機車，載菜載小孩都靠它。"))
    A(item("st_scarecrow", "稻草人", "Scarecrow", "農具", [100, 176, 30], [
        part("cylinder", [6, 170, 6], [0, 85, 0], "#7f5539"),
        part("box", [100, 6, 6], [0, 120, 0], "#7f5539"),
        part("box", [50, 50, 20], [0, 105, 0], "#e63946"),
        part("sphere", [26, 26, 26], [0, 148, 0], "#e9c46a"),
        part("cone", [44, 16, 44], [0, 166, 0], "#d4a373", collide=False)],
        fill=0.2, flavor="站在田中央，幫忙把麻雀趕走。"))
    A(item("st_fruit_stall", "文旦攤車", "Pomelo Stall", "街道", [180, 210, 200], [
        part("box", [120, 80, 200], [0, 60, 0], "#8d6e4f"),
        wheel(40, 10, [-65, 20, 0], "#495057"),
        wheel(40, 10, [65, 20, 0], "#495057"),
        part("cylinder", [6, 110, 6], [0, 150, 0], "#adb5bd", collide=False),
        part("cone", [180, 40, 180], [0, 195, 0], "#ffbe0b", collide=False),
        part("sphere", [100, 30, 170], [0, 112, 0], "#d9e36a", collide=False)],
        fill=0.3, sfx="orange", flavor="路邊的文旦攤，阿伯說今年的特別甜。"))
    A(item("st_bus_stop", "公車站牌", "Bus Stop Sign", "街道", [40, 250, 40], [
        part("cylinder", [40, 10, 40], [0, 5, 0], "#6c757d"),
        part("cylinder", [8, 240, 8], [0, 125, 0], "#adb5bd"),
        part("box", [40, 60, 6], [0, 215, 0], "#1d4e89", collide=False),
        part("box", [30, 10, 7], [0, 228, 0], "#f8f9fa", collide=False)],
        fill=0.15))
    A(item("st_electric_pole", "電線桿", "Utility Pole", "街道", [40, 900, 40], [
        part("cylinder", [32, 900, 32], [0, 450, 0], "#bfb8a8"),
        part("box", [180, 12, 12], [0, 850, 0], "#6c757d", collide=False),
        part("cylinder", [40, 60, 40], [30, 700, 0], "#adb5bd", collide=False)],
        fill=0.15, flavor="鄉間小路旁一根接一根的電線桿。"))
    A(item("st_small_tree", "小樹", "Small Tree", "植物", [140, 220, 140], [
        part("cylinder", [16, 90, 16], [0, 45, 0], "#7f5539"),
        part("sphere", [140, 130, 140], [0, 150, 0], "#40916c")],
        fill=0.25))
    A(item("st_pomelo_sapling", "文旦樹苗", "Pomelo Sapling", "植物", [80, 150, 80], [
        part("cylinder", [40, 30, 40], [0, 15, 0], "#212529"),
        part("cylinder", [8, 60, 8], [0, 60, 0], "#7f5539"),
        part("sphere", [80, 70, 80], [0, 112, 0], "#2d6a4f")],
        fill=0.25))
    A(item("st_stone_bench", "石椅", "Stone Bench", "街道", [150, 45, 45], shape="box", color="#b0aca4", fill=0.6))
    A(item("st_chess_table", "象棋桌", "Chess Table", "街道", [80, 75, 80], [
        part("cylinder", [80, 6, 80], [0, 72, 0], "#c8b6a6"),
        part("cylinder", [30, 69, 30], [0, 34.5, 0], "#a8a29e"),
        part("box", [40, 2, 40], [0, 76, 0], "#e9c46a", collide=False)],
        fill=0.3, flavor="大榕樹下的象棋桌，阿公們每天都來下棋。"))
    A(item("st_bamboo_basket", "竹簍", "Bamboo Basket", "農具", [45, 40, 45], shape="cylinder", color="#c9a46b", fill=0.3))
    A(item("st_hose", "一捲水管", "Garden Hose", "農具", [42, 14, 42], shape="cylinder", color="#2b9348", fill=0.4))
    A(item("st_crate", "塑膠菜籃", "Plastic Crate", "生活", [55, 32, 40], [
        part("box", [55, 30, 40], [0, 15, 0], "#ffbe0b", tint=True),
        part("sphere", [20, 14, 20], [-12, 30, 0], "#a7c957", collide=False),
        part("sphere", [20, 14, 20], [12, 30, 4], "#e63946", collide=False)],
        fill=0.3, colors=["#ffbe0b", "#3a86ff", "#8ac926", "#ff006e"]))
    A(item("st_water_buffalo", "水牛", "Water Buffalo", "動物", [90, 165, 260], [
        part("box", [90, 90, 200], [0, 110, 10], "#4a4e54"),
        part("box", [50, 50, 60], [0, 130, -115], "#4a4e54", name="head"),
        part("box", [100, 8, 12], [0, 160, -110], "#d9d2c5", collide=False),
        part("cylinder", [20, 65, 20], [-30, 32.5, -60], "#343a40"),
        part("cylinder", [20, 65, 20], [30, 32.5, -60], "#343a40"),
        part("cylinder", [20, 65, 20], [0, 32.5, 80], "#343a40")],
        fill=0.4, flavor="在田邊泡水休息的水牛，慢吞吞的。"))
    A(item("st_kick_scooter", "滑板車", "Kick Scooter", "玩具", [35, 80, 60], [
        part("box", [14, 6, 60], [0, 5, 0], "#ff006e", tint=True),
        part("cylinder", [4, 72, 4], [0, 42, -26], "#adb5bd"),
        part("box", [35, 3, 3], [0, 78, -26], "#212529")],
        fill=0.2, colors=["#ff006e", "#3a86ff", "#8ac926"], sfx="squeak"))
    A(item("st_signboard", "店門口立牌", "A-frame Sign", "街道", [60, 110, 50], [
        part("box", [60, 110, 4], [0, 54, -10], "#264653", rot=[12, 0, 0]),
        part("box", [60, 110, 4], [0, 54, 10], "#264653", rot=[-12, 0, 0]),
        part("box", [50, 30, 5], [0, 75, -16], "#ffbe0b", rot=[12, 0, 0], collide=False)],
        fill=0.2))
    A(item("st_ice_box", "冰棒冰櫃", "Ice Pop Freezer", "街道", [90, 85, 60], [
        part("box", [90, 75, 60], [0, 37.5, 0], "#f8f9fa"),
        part("box", [86, 10, 56], [0, 80, 0], "#3a86ff")],
        fill=0.6, flavor="雜貨店門口的冰櫃，裡面有清冰和紅豆冰棒。"))
    A(item("st_tire", "舊輪胎", "Old Tire", "生活", [62, 20, 62], shape="cylinder", color="#212529", fill=0.4))
    A(item("st_oil_drum", "鐵桶", "Steel Drum", "生活", [58, 88, 58], shape="cylinder", color="#1d4e89", fill=0.5,
         colors=["#1d4e89", "#d62828", "#2b9348"]))
    A(item("st_ladder", "鋁梯", "Step Ladder", "農具", [50, 190, 60], [
        part("box", [45, 190, 5], [0, 93, -15], "#ced4da", rot=[-9, 0, 0]),
        part("box", [45, 190, 5], [0, 93, 15], "#ced4da", rot=[9, 0, 0])],
        fill=0.15))
    A(item("st_seedling_tray", "秧苗盤", "Rice Seedling Tray", "農具", [60, 10, 30], [
        part("box", [60, 4, 30], [0, 2, 0], "#212529"),
        part("box", [58, 6, 28], [0, 7, 0], "#80b918", collide=False)],
        fill=0.4, flavor="插秧前的秧苗，綠油油一盤。"))
    A(item("st_feed_sack", "飼料袋", "Feed Sack", "農具", [40, 25, 60], shape="box", color="#d4a373", fill=0.6))
    A(item("st_coop", "雞籠", "Chicken Coop", "農具", [80, 60, 60], [
        part("box", [80, 4, 60], [0, 2, 0], "#7f5539"),
        part("box", [80, 56, 60], [0, 32, 0], "#ced4da")],
        fill=0.2))
    A(item("st_vending", "飲料販賣機", "Vending Machine", "街道", [100, 180, 75], [
        part("box", [100, 180, 75], [0, 90, 0], "#e63946", tint=True),
        part("box", [80, 70, 4], [0, 120, -38], "#caf0f8", collide=False),
        part("box", [30, 20, 4], [0, 40, -38], "#212529", collide=False)],
        fill=0.6, colors=["#e63946", "#3a86ff", "#2b9348"], sfx="bell"))
    A(item("st_pomelo_tree", "文旦樹", "Pomelo Tree", "植物", [400, 380, 400], [
        part("cylinder", [30, 120, 30], [0, 60, 0], "#7f5539"),
        part("sphere", [400, 240, 400], [0, 260, 0], "#2d6a4f"),
        part("sphere", [20, 18, 20], [120, 160, -100], "#d9e36a", collide=False),
        part("sphere", [20, 18, 20], [-110, 180, 90], "#d9e36a", collide=False),
        part("sphere", [20, 18, 20], [60, 150, 140], "#d9e36a", collide=False)],
        fill=0.25, sfx="orange", flavor="結滿文旦的老欉文旦樹。"))
    A(item("st_cherry_tree", "山櫻花", "Taiwan Cherry", "植物", [420, 450, 420], [
        part("cylinder", [34, 180, 34], [0, 90, 0], "#5c4033"),
        part("sphere", [420, 280, 420], [0, 300, 0], "#ffafcc")],
        fill=0.25, flavor="槿寶家門口的山櫻花，粉紅色的花瓣一直飄下來。"))
    A(item("st_car", "家裡的白色汽車", "Family Car", "交通", [180, 150, 450], [
        part("box", [180, 80, 450], [0, 55, 0], "#f8f9fa"),
        part("box", [160, 60, 230], [0, 125, 20], "#f8f9fa")],
        fill=0.4, model="st_car_white", sfx="car_horn", flavor="爸爸的車，週末載全家去冬山河。"))
    A(item("st_car_red", "紅色汽車", "Red Car", "交通", [180, 150, 450], [
        part("box", [180, 80, 450], [0, 55, 0], "#e63946"),
        part("box", [160, 60, 230], [0, 125, 20], "#e63946")],
        fill=0.4, model="st_car_red", sfx="car_horn"))
    A(item("st_car_blue", "藍色汽車", "Blue Car", "交通", [180, 150, 450], [
        part("box", [180, 80, 450], [0, 55, 0], "#3a86ff"),
        part("box", [160, 60, 230], [0, 125, 20], "#3a86ff")],
        fill=0.4, model="st_car_blue", sfx="car_horn"))

    # 建築與大型地標（不可黏）
    A(item("st_farmhouse", "農舍", "Farmhouse", "建築", [1080, 530, 880], [
        part("box", [1000, 350, 800], [0, 175, 0], "#f1e3c6"),
        part("box", [1080, 30, 880], [0, 365, 0], "#9c6644"),
        part("cylinder", [150, 150, 150], [300, 455, 200], "#adb5bd", collide=False),
        part("box", [160, 230, 4], [0, 115, -402], "#6b4f3a", collide=False),
        part("box", [180, 120, 4], [-300, 190, -402], "#a2d2ff", collide=False),
        part("box", [180, 120, 4], [300, 190, -402], "#a2d2ff", collide=False)],
        fill=0.2, pickable=False))
    A(item("st_grocery", "柑仔店", "Village Grocery", "建築", [800, 460, 760], [
        part("box", [800, 400, 600], [0, 200, 60], "#fefae0"),
        part("box", [800, 80, 12], [0, 420, -245], "#e63946", collide=False),
        part("box", [800, 10, 150], [0, 305, -320], "#2a9d8f", collide=False),
        part("box", [300, 260, 4], [0, 130, -242], "#a2d2ff", collide=False),
        part("box", [560, 30, 20], [0, 420, -252], "#f8f9fa", collide=False)],
        fill=0.2, pickable=False, flavor="什麼都賣的柑仔店，放學後最熱鬧。"))
    A(item("st_shrine", "土地公小廟", "Earth God Shrine", "建築", [260, 300, 260], [
        part("box", [240, 220, 240], [0, 110, 0], "#e85d04")],
        fill=0.2, model="st_shrine", pickable=False, flavor="守護田地的土地公小廟。"))
    A(item("st_banyan", "大榕樹", "Banyan Tree", "植物", [1000, 900, 1000], [
        part("cylinder", [160, 320, 160], [0, 160, 0], "#6b4f3a"),
        part("sphere", [1000, 560, 1000], [0, 620, 0], "#2d6a4f", collide=False),
        part("cylinder", [12, 300, 12], [250, 330, 120], "#7f5539", collide=False),
        part("cylinder", [12, 260, 12], [-220, 350, -160], "#7f5539", collide=False)],
        fill=0.2, pickable=False))
    A(item("st_school_gate", "小學大門", "School Gate", "建築", [1320, 480, 120], [
        part("box", [120, 400, 120], [-600, 200, 0], "#e9c46a"),
        part("box", [120, 400, 120], [600, 200, 0], "#e9c46a"),
        part("box", [1320, 80, 120], [0, 440, 0], "#c1121f"),
        part("box", [600, 50, 10], [0, 440, -66], "#f8f9fa", collide=False)],
        fill=0.2, pickable=False))
    A(item("st_home_house", "槿寶的家", "Jinbao's House", "建築", [1500, 420, 1100], [
        part("box", [1500, 340, 1100], [0, 170, 0], "#fdf0d5"),
        part("box", [1560, 40, 1160], [0, 360, 0], "#b56576"),
        part("box", [220, 240, 4], [0, 120, 552], "#9c6644", collide=False),
        part("box", [260, 130, 4], [-450, 190, 552], "#a2d2ff", collide=False),
        part("box", [260, 130, 4], [450, 190, 552], "#a2d2ff", collide=False),
        part("cylinder", [160, 140, 160], [500, 450, -300], "#adb5bd", collide=False)],
        fill=0.2, pickable=False, flavor="槿寶的家，第 1 關就在這裡。"))
    return it


# ---------- 第 2 關場景 ----------

ROAD_Z0, ROAD_Z1 = -300, 300          # 主路（柏油）
CANAL_Z0, CANAL_Z1 = 380, 600         # 南側灌溉水圳
CANAL_BOTTOM = -38
PADDY_Y = -18
PADDY_COLOR = "#3f7f2a"
RICE_COLOR = "#6aa63c"
X0, X1 = -3600, 30000                 # 東西範圍
Z0, Z1 = -7000, 7000                  # 南北範圍


def build_level(items):
    lv = Level("street", "上學的路",
               "第 2 關：宜蘭冬山鄉間的上學路。從槿寶家門口沿著農路往東，經過稻田、水圳、農舍、"
               "土地公小廟、柑仔店、文旦園與鴨寮，終點是小學大門。單位公分。")
    lv.set_env(sky="#a9d6f5", fog_color="#dcecf5", fog_per_d=0.0035)

    # 最底下的安全地面（萬一從縫隙掉下去）
    lv.floor("底層", X0 - 3000, Z0 - 3000, (X1 - X0) + 6000, (Z1 - Z0) + 6000, y=-200, pattern="soil",
             color="#8d6e4f", repeat=200, thickness=20)

    # 主路與路肩
    lv.floor("主路", X0, ROAD_Z0, X1 - X0, ROAD_Z1 - ROAD_Z0, y=0, pattern="asphalt", color="#5a5f66",
             repeat=300, thickness=200)
    lv.floor("北側路肩", X0, ROAD_Z0 - 80, X1 - X0, 80, y=-8, pattern="grass", color="#86b35a", repeat=200,
             thickness=200)
    lv.floor("南側水圳邊", X0, ROAD_Z1, X1 - X0, CANAL_Z0 - ROAD_Z1, y=0, pattern="concrete", color="#aba79c",
             repeat=300, thickness=200)
    # 水圳：底部是水，兩側牆就是旁邊地板的厚度
    lv.floor("灌溉水圳", X0, CANAL_Z0, X1 - X0, CANAL_Z1 - CANAL_Z0, y=CANAL_BOTTOM, pattern="water",
             color="#2f7f9f", repeat=200, thickness=60)
    # 主路中線（虛線）
    x = X0 + 200
    while x < X1 - 400:
        lv.block("中線", x + 150, 0, 0, 300, 0.6, 14, color="#f8f9fa")
        x += 800

    # 北側（z < -380）由西到東：槿寶家、北田一、北農路、鴨寮與北田二、村子與北田三、北田四、北田五、學校前
    NZ = ROAD_Z0 - 80
    # 南側（z > 600）由西到東：南田一、南田二、文旦園、南田三、學校前南側
    north_fields = [
        ("北田零", X0, -600, Z0, -4200),
        ("北田一", -600, 5000, Z0, NZ),
        ("北田二", 5600, 8600, -4000, NZ),
        ("北田二北", 5600, 8600, Z0, -6400),
        ("北田三", 8600, 15400, Z0, -4200),
        ("北田四", 15400, 21000, Z0, NZ),
        ("北田五", 21000, 26000, Z0, NZ),
    ]
    for name, xa, xb, za, zb in north_fields:
        _paddy_block(lv, name, xa, xb, za, zb)
    south_fields = [
        ("南田一", X0, 3000, CANAL_Z1, Z1),
        ("南田二", 3000, 9000, CANAL_Z1, Z1),
        ("南田三", 21500, 26000, CANAL_Z1, Z1),
    ]
    for name, xa, xb, za, zb in south_fields:
        _paddy_block(lv, name, xa, xb, za, zb)

    # 槿寶家（西北角）：水泥前院、圍牆、大門、汽車、山櫻花
    hx0, hx1, hz0 = X0, -600, -4200
    lv.floor("槿寶家前院", hx0, hz0, hx1 - hx0, NZ - hz0, y=0, pattern="concrete", color="#b3ada2",
             repeat=200, thickness=200)
    lv.place("st_home_house", (hx0 + hx1) / 2, 0, -3000, rot=0)
    # 圍牆：南面留大門缺口
    wall_z = ROAD_Z0 - 120
    gate_mid = (hx1 - hx0) / 2
    lv.wall((hx0, wall_z), (hx1, wall_z), height=150, thickness=24, color="#e9d8c4",
            gaps=[(gate_mid - 300, gate_mid + 300, 999)])
    lv.wall((hx1, hz0), (hx1, wall_z), height=150, thickness=24, color="#e9d8c4")
    lv.place("st_car", hx0 + 700, 0, wall_z - 420, rot=0)
    lv.place("st_cherry_tree", hx1 - 500, 0, wall_z - 420)
    lv.petals("山櫻花", (hx1 - 500, 0, wall_z - 420), (800, 520, 800), color="#ffafcc", amount=70, petal=7.0,
              fall=60.0)

    # 村子（北側中段）：農舍、柑仔店、土地公小廟、大榕樹
    vx0, vx1, vz0 = 8600, 15400, -4200
    lv.floor("村子空地", vx0, vz0, vx1 - vx0, NZ - vz0, y=0, pattern="concrete", color="#b0a998",
             repeat=300, thickness=200)
    lv.place("st_grocery", 10000, 0, -1300, rot=180)
    lv.place("st_farmhouse", 13700, 0, -3000, rot=180)
    lv.place("st_farmhouse", 9200, 0, -3500, rot=90)
    lv.place("st_shrine", 12000, 0, -1050, rot=180)
    lv.place("st_banyan", 12100, 0, -2500)
    lv.place("st_chess_table", 11500, 0, -1900)
    lv.place("st_chess_table", 12700, 0, -2000)
    lv.place("st_bus_stop", 11300, 0, -560)
    lv.place("st_mailbox_pair", 9300, 0, -650)
    lv.place("st_vending", 10750, 0, -700, rot=180)
    lv.place("st_ice_box", 9550, 0, -800)

    # 往北的農路與鴨寮
    lv.floor("北農路", 5000, Z0, 600, NZ - Z0, y=0, pattern="concrete", color="#aba79c", repeat=300,
             thickness=200)
    lv.floor("鴨寮空地", 5600, -6400, 3000, 2400, y=0, pattern="soil", color="#a98467", repeat=200, thickness=200)
    lv.floor("鴨池", 6000, -6100, 1200, 900, y=-45, pattern="water", color="#3f8fae", repeat=200, thickness=60)
    lv.stairs_up("鴨池樓梯", (6600, 0, -5200), 180, width=300, base_y=-45, slope_deg=22, style="blocks",
                 colors=["#c9c6bd", "#b8b3a7"])
    lv.stairs_up("鴨池樓梯", (6600, 0, -6100), 0, width=300, base_y=-45, slope_deg=22, style="lego")

    # 文旦園（南側中段，水圳南邊，比稻田高一點的泥土地）
    ox0, ox1 = 9000, 21500
    lv.floor("文旦園", ox0, CANAL_Z1, ox1 - ox0, Z1 - CANAL_Z1, y=-15, pattern="grass", color="#7f9f45",
             repeat=200, thickness=200)
    for i, tx in enumerate(range(ox0 + 700, ox1 - 500, 1100)):
        for j, tz in enumerate(range(1900, 6000, 1700)):
            lv.place("st_pomelo_tree", tx + (j % 2) * 400, -15, tz, rot=(i * 37 + j * 53) % 360)

    # 學校前（東端）
    sx0 = 26000
    lv.floor("學校前廣場", sx0, -3600, X1 - sx0, 3600 + NZ, y=0, pattern="paving", color="#c49a76",
             repeat=120, thickness=200)
    lv.floor("學校前北側草地", sx0, Z0, X1 - sx0, -3600 - Z0, y=-10, pattern="grass", color="#86b35a",
             repeat=200, thickness=200)
    lv.floor("學校前南側", sx0, CANAL_Z1, X1 - sx0, 2800, y=0, pattern="paving", color="#c49a76", repeat=120,
             thickness=200)
    lv.floor("學校前南側草地", sx0, CANAL_Z1 + 2800, X1 - sx0, Z1 - CANAL_Z1 - 2800, y=-10, pattern="grass",
             color="#86b35a", repeat=200, thickness=200)
    lv.place("st_school_gate", 29200, 0, 0, rot=90)
    lv.wall((29200, -3600), (29200, -700), height=200, thickness=40, color="#f1e3c6")
    lv.wall((29200, 700), (29200, 3400), height=200, thickness=40, color="#f1e3c6")
    # 學校前的水圳加蓋（整段可通行）
    lv.block("學校前水圳蓋板", (sx0 + X1) / 2, -20, (CANAL_Z0 + CANAL_Z1) / 2, X1 - sx0, 20, CANAL_Z1 - CANAL_Z0,
             color="#b8b3a7")

    # 水圳的橋與出口樓梯：每座橋一側有積木樓梯從水圳底爬回路面
    bridges = [-2000, 2200, 6000, 9800, 13600, 17400, 21200, 25000]
    for bx in bridges:
        lv.block("水圳小橋", bx, -20, (CANAL_Z0 + CANAL_Z1) / 2, 420, 20, CANAL_Z1 - CANAL_Z0 + 40,
                 color="#b8b3a7")
        lv.stairs_up("水圳出口", (bx - 210, 0, (CANAL_Z0 + CANAL_Z1) / 2), 270, width=200,
                     base_y=CANAL_BOTTOM, slope_deg=24, style="lego")
        lv.stairs_up("水圳出口", (bx + 210, 0, (CANAL_Z0 + CANAL_Z1) / 2), 90, width=200,
                     base_y=CANAL_BOTTOM, slope_deg=24, style="blocks", colors=["#c9c6bd", "#b8b3a7", "#d6d3cb"])

    # 電線桿：北側路肩每 30 公尺一根
    for px in range(-200, 28500, 3000):
        lv.place("st_electric_pole", px, -8, ROAD_Z0 - 40)

    # ---------- 散布 ----------
    # 起點附近要很密：一出家門就忙不完
    lv.spawn("家門口", (hx0 + 300, wall_z - 1300, hx1 - hx0 - 600, 1150), 0, {
        "st_bucket": 6, "st_helmet": 5, "st_rain_boots": 4, "st_potted_plant": 6, "st_stool": 6,
        "st_plastic_chair": 4, "st_cabbage": 4, "st_pomelo_box": 3, "st_brick_stack": 4, "st_hose": 2,
        "st_crate": 4, "st_tire": 3, "st_kick_scooter": 2, "flower_pot": 4, "watering_can": 2,
        "trash_can": 2, "soccer_ball": 2, "laundry_basket": 2,
    })
    lv.spawn("主路西段", (X0 + 200, ROAD_Z0 + 40, 9000, ROAD_Z1 - ROAD_Z0 - 80), 0, {
        "st_traffic_cone": 6, "st_bucket": 3, "st_helmet": 3, "st_crate": 4, "st_tire": 3, "st_stool": 3,
        "st_brick_stack": 3, "st_gas_tank": 3, "st_cabbage": 3, "st_watermelon": 2, "st_potted_plant": 4,
        "st_trash_bin": 3, "st_rice_sack": 3, "st_bamboo_basket": 4, "st_signboard": 2,
        "st_wheelbarrow": 2, "st_water_jar": 2, "st_stone_bench": 2, "st_oil_drum": 3, "st_ice_box": 1,
        "st_kick_scooter": 2,
    })
    lv.spawn("水圳邊西段", (X0 + 200, ROAD_Z1 + 10, 9000, CANAL_Z0 - ROAD_Z1 - 20), 0, {
        "st_bucket": 4, "st_stool": 3, "st_bamboo_hat": 4, "st_hose": 3, "st_rain_boots": 3,
    })
    lv.spawn("主路中段", (8600, ROAD_Z0 + 40, 9000, ROAD_Z1 - ROAD_Z0 - 80), 0, {
        "st_traffic_cone": 8, "st_trash_bin": 4, "st_oil_drum": 6, "st_tire": 4, "st_wheelbarrow": 4,
        "st_bike": 3, "st_scooter": 2, "st_water_jar": 3, "st_ice_box": 2, "st_signboard": 3,
        "st_crate": 3, "st_plastic_chair": 3, "st_potted_plant": 3, "st_gas_tank": 3, "st_kick_scooter": 2,
    })
    lv.spawn("主路東段", (17600, ROAD_Z0 + 40, 8400, ROAD_Z1 - ROAD_Z0 - 80), 0, {
        "st_traffic_cone": 8, "st_oil_drum": 6, "st_bike": 3, "st_scooter": 3, "st_wheelbarrow": 4,
        "st_ladder": 4, "st_scarecrow": 2, "st_water_jar": 3, "st_fruit_stall": 1, "st_small_tree": 2,
        "st_stone_bench": 3, "st_vending": 2,
    })
    lv.spawn("村子", (vx0 + 200, vz0 + 200, vx1 - vx0 - 400, NZ - vz0 - 400), 0, {
        "st_plastic_chair": 6, "st_stool": 6, "st_potted_plant": 5, "st_water_jar": 4, "st_gas_tank": 3,
        "st_crate": 5, "st_bike": 3, "st_scooter": 3, "st_oil_drum": 4, "st_stone_bench": 4, "st_tire": 4,
        "st_ladder": 3, "st_wheelbarrow": 3, "st_kick_scooter": 3, "st_signboard": 3, "st_small_tree": 2,
        "st_vending": 1, "st_fruit_stall": 1, "st_rice_sack": 3, "st_watermelon": 2, "st_bucket": 3,
    })
    lv.spawn("鴨寮", (5700, -6300, 2800, 2200), 0, {
        "st_feed_sack": 6, "st_bucket": 4, "st_coop": 4, "st_bamboo_basket": 4, "st_crate": 4,
        "st_wheelbarrow": 2, "st_oil_drum": 2,
    })
    lv.spawn("北農路", (5050, Z0 + 300, 500, 6200), 0, {
        "st_bike": 3, "st_scooter": 2, "st_bamboo_hat": 3, "st_hoe": 4, "st_rice_sack": 4, "st_tire": 2,
    })
    for name, xa, xb, za, zb in north_fields + south_fields:
        if (xb - xa) * (zb - za) < 4_000_000:
            continue
        big = (xb - xa) * (zb - za) > 34_000_000
        lv.spawn(f"{name}田裡", (xa + 200, za + 200, xb - xa - 400, zb - za - 400), PADDY_Y, {
            "st_frog": 2, "st_seedling_tray": 4, "st_bamboo_hat": 2, "st_hoe": 2, "st_scarecrow": 2 if big else 1,
            "st_rice_sack": 2, "st_rain_boots": 1, "st_bucket": 1, "st_water_buffalo": 1 if big else 0,
        })
    lv.spawn("文旦園", (ox0 + 200, CANAL_Z1 + 200, ox1 - ox0 - 400, Z1 - CANAL_Z1 - 400), -15, {
        "st_pomelo": 24, "st_pomelo_box": 12, "st_bamboo_basket": 6, "st_crate": 6, "st_ladder": 5,
        "st_wheelbarrow": 4, "st_pomelo_sapling": 8, "st_fruit_stall": 2, "st_scooter": 1, "st_oil_drum": 2,
        "st_water_buffalo": 1,
    }, avoid_furniture=True)
    lv.spawn("學校前", (sx0 + 200, -3400, 2800, 3400 + ROAD_Z0 - 200), 0, {
        "st_scooter": 6, "st_bike": 6, "st_kick_scooter": 3, "st_helmet": 3, "st_traffic_cone": 4,
        "st_signboard": 2, "st_small_tree": 2, "st_stone_bench": 3, "st_vending": 2, "st_trash_bin": 3,
    })
    lv.spawn("學校前南側", (sx0 + 200, CANAL_Z1 + 200, 2800, 2400), 0, {
        "st_scooter": 3, "st_bike": 3, "st_small_tree": 2, "st_fruit_stall": 1, "st_car_red": 1,
    })

    # 動物（會走動），活動範圍各自限制在場景內
    critters = [
        ("st_duck", 5900, -5000, (5700, -6300, 2800, 2200)),
        ("st_duck", 7500, -5100, (5700, -6300, 2800, 2200)),
        ("st_duck", 7700, -4700, (5700, -6300, 2800, 2200)),
        ("st_duck", 8100, -5600, (5700, -6300, 2800, 2200)),
        ("st_duck", 5800, -4500, (5700, -6300, 2800, 2200)),
        ("st_chicken", 7900, -4500, (7400, -6300, 1100, 2200)),
        ("st_chicken", 8100, -5300, (7400, -6300, 1100, 2200)),
        ("st_chicken", 11300, -1800, (10600, -2600, 1600, 1600)),
        ("st_egret", 1800, -3000, (-500, -6800, 5300, 6300)),
        ("st_egret", 6000, 3000, (3100, 800, 5800, 5000)),
        ("st_egret", 18000, -4000, (15500, -6800, 5300, 6300)),
        ("st_egret", 23500, 3500, (21600, 800, 4300, 5000)),
        ("st_dog_local", 10500, -2000, (8800, -4000, 6400, 3400)),
        ("st_dog_local", 27500, -1500, (26100, -3400, 2900, 3000)),
        ("st_cat_local", 9800, -900, (9000, -2400, 2400, 1900)),
        ("st_cat_local", -1200, -1500, (-3400, -2300, 2700, 1800)),
    ]
    for cid, cx, cz, roam in critters:
        y = PADDY_Y if cid == "st_egret" else 0
        lv.place(cid, cx, y, cz, rot=0, roam=roam, blocks_spawn=False)

    # 場景邊界：四周的竹林樹籬，球不會滾出世界
    for a, b in [((X0, Z0), (X1, Z0)), ((X0, Z1), (X1, Z1)), ((X0, Z0), (X0, Z1)), ((X1, Z0), (X1, Z1))]:
        lv.wall(a, b, height=700, thickness=200, color="#4f772d", y=-30)

    # 遠方的山（宜蘭三面環山，從平原看出去）
    for i, (mx, mz, w, h, c) in enumerate([
        (2000, -26000, 16000, 5200, "#5f8f6a"), (16000, -30000, 22000, 7600, "#4f7d5c"),
        (30000, -25000, 14000, 4800, "#6a9a72"), (-12000, -18000, 14000, 6200, "#5a8865"),
        (-14000, 6000, 12000, 5000, "#62906b"), (12000, 24000, 20000, 4200, "#6f9c76"),
    ]):
        lv.decor(f"遠山{i + 1}", "cone", (mx, -200, mz), (w, h, w * 0.6), c, no_shadow=True)

    # 區域名稱
    lv.area("槿寶家門口", hx0, hz0, hx1 - hx0, ROAD_Z1 - hz0)
    lv.area("稻田", X0, Z0, 9000 - X0, Z1 - Z0)
    lv.area("鴨寮", 5600, -6400, 3000, 2400)
    lv.area("村子", vx0, vz0, vx1 - vx0, ROAD_Z1 - vz0)
    lv.area("文旦園", ox0, CANAL_Z1, ox1 - ox0, Z1 - CANAL_Z1)
    lv.area("稻田", 15400, Z0, sx0 - 15400, Z1 - Z0)
    lv.area("學校大門", sx0, -3600, X1 - sx0, 7000)

    lv.set_start((-2050, 0.5, 100), 270)
    lv.set_rescue((12500, 0.5, 0), 270)
    lv.set_stage(
        start_cm=100, goal_cm=300, time_sec=480, comet_sec=240, seed=2201, music="street",
        intro="出發上學囉！沿著稻田邊的路，長到 3 公尺就能進學校",
        zones=[], gates={}, tuning={},
        start={"pos": [-2050, 0.5, 100], "yaw_deg": 270},
        grades=[
            {"min_ratio": 0.0, "text": "星婆婆：路還很長，再滾一次吧！"},
            {"min_ratio": 1.0, "text": "星婆婆：準時到學校了！路上好乾淨。"},
            {"min_ratio": 1.3, "text": "星婆婆：連文旦攤車都滾起來了？阿伯會嚇一跳！"},
            {"min_ratio": 1.6, "text": "星婆婆：好大一顆！電線桿都黏在上面了！"},
            {"min_ratio": 1.9, "text": "星婆婆：太厲害了！整條上學路都變成星星啦！"},
        ],
    )
    return lv


def _paddy_block(lv, name, xa, xb, za, zb):
    """一大片稻田：田地板加上田埂（每格約 30 公尺 × 20 公尺）。
    靠近槿寶家的兩塊是剛插秧的水田（看得到水），其他是長高的綠色稻子。"""
    if name in ("北田一", "南田一"):
        lv.floor(name, xa, za, xb - xa, zb - za, y=PADDY_Y, pattern="paddy", color=PADDY_COLOR, repeat=260,
                 thickness=200)
    else:
        lv.floor(name, xa, za, xb - xa, zb - za, y=PADDY_Y, pattern="grass", color=RICE_COLOR, repeat=240,
                 thickness=200)
    gx = 3000
    x = xa + gx
    while x < xb - 500:
        lv.block(f"{name}田埂", x, PADDY_Y, (za + zb) / 2, 50, 22, zb - za, color="#7a9a4a")
        x += gx
    gz = 2000
    z = za + gz
    while z < zb - 500:
        lv.block(f"{name}田埂", (xa + xb) / 2, PADDY_Y, z, xb - xa, 22, 50, color="#7a9a4a")
        z += gz


def main():
    items = street_items()
    save_items("street.json", "第 2 關「上學的路」的物件（宜蘭冬山鄉間）。id 前綴 st_；第 3 關也會用到其中一部分。", items)
    lv = build_level(items)
    lv.save()
    base = json.loads((ROOT / "godot" / "data" / "items.json").read_text(encoding="utf-8"))["items"]
    budget(lv, items + base, 100, 300, [(0, 20), (20, 40), (40, 70), (70, 120), (120, 210), (210, 99999)])


if __name__ == "__main__":
    main()
