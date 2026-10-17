"""第 4 關「滾到冬山火車站」：產生 godot/data/items/station.json 與 godot/data/levels/station.json。

執行：python3 tools/levels/build_station.py   （在 rolling-home 目錄）

場景：宜蘭冬山鄉的小鎮、稻田、文旦果園與茶園、冬山河、工廠區、住宅區，一路滾到高架的冬山車站。
塊球從 10 公尺長到 100 公尺。單位公分；x 往東、z 往南（北邊是 -z）。

配置（俯視，北在上）：
    北半部（z < 15000）：西邊工廠區、中間住宅區與廟、東邊高架鐵路與冬山車站，車站北側是森林公園。
    冬山河（z 15000 到 24000）：由西往東橫過整張地圖，兩岸是緩坡河堤，河上有兩座車行大橋、兩座人行橋。
    南半部（z > 24000）：西南是起點小鎮、中間是稻田與農舍、鐵路東側是文旦果園與茶園。
    最外圈有一圈圍牆擋住，牆外西邊與南邊是遠山（雪山山脈、中央山脈方向），不碰撞。

查證的在地事實與來源見 docs/08_第4關_滾到冬山火車站.md。
"""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from levelkit import Level  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ITEMS_OUT = ROOT / "godot" / "data" / "items" / "station.json"


# ---------- 物件定義 ----------

def B(dims, pos, color, rot=None, collide=True, tint=False, name=None):
    return _part("box", dims, pos, color, rot, collide, tint, name)


def C(dims, pos, color, rot=None, collide=True, tint=False, name=None):
    return _part("cylinder", dims, pos, color, rot, collide, tint, name)


def S(dims, pos, color, rot=None, collide=True, tint=False, name=None):
    return _part("sphere", dims, pos, color, rot, collide, tint, name)


def K(dims, pos, color, rot=None, collide=True, tint=False, name=None):
    return _part("cone", dims, pos, color, rot, collide, tint, name)


def _part(shape, dims, pos, color, rot, collide, tint, name):
    p = {"shape": shape, "dims": list(dims), "pos": list(pos), "color": color}
    if rot:
        p["rot"] = list(rot)
    if not collide:
        p["collide"] = False
    if tint:
        p["tint"] = True
    if name:
        p["name"] = name
    return p


ITEMS = []


def item(id_, name, name_en, category, dims, parts, fill=0.5, flavor=None, **kw):
    d = {"id": id_, "name": name, "name_en": name_en, "category": category, "shape": "parts",
         "dims": list(dims), "fill": fill, "parts": parts}
    if flavor:
        d["flavor"] = flavor
    d.update(kw)
    ITEMS.append(d)
    return d


CAR_COLORS = ["#e63946", "#f1faee", "#457b9d", "#ffd166", "#2a9d8f", "#adb5bd", "#1d3557", "#f4a261"]
WHEEL = "#2b2d42"
GLASS = "#a8dadc"


def wheels(width, y, z1, z2, d=64):
    return [C((d, width, d), (0, y, z1), WHEEL, rot=(0, 0, 90)), C((d, width, d), (0, y, z2), WHEEL, rot=(0, 0, 90))]


# 第一層（1 到 7 公尺）：10 到 20 公尺的球主要靠這些長大
item("sn_car", "汽車", "Car", "交通", (180, 150, 450), [
    B((180, 70, 450), (0, 55, 0), "#e63946", tint=True),
    B((160, 55, 240), (0, 117, -20), GLASS),
    B((150, 8, 200), (0, 148, -20), "#e63946", collide=False, tint=True),
] + wheels(186, 32, 140, -140), colors=CAR_COLORS, flavor="鎮上的小汽車。")
item("sn_taxi", "計程車", "Taxi", "交通", (180, 160, 450), [
    B((180, 70, 450), (0, 55, 0), "#ffd60a"),
    B((160, 55, 240), (0, 117, -20), GLASS),
    B((40, 14, 60), (0, 152, -20), "#f8f9fa", collide=False),
] + wheels(186, 32, 140, -140), sfx="car_horn", flavor="黃色計程車，黏到時會叭叭叫。")
item("sn_scooter", "機車", "Scooter", "交通", (70, 115, 190), [
    B((40, 50, 120), (0, 55, 0), "#e63946", tint=True),
    B((35, 12, 70), (0, 88, -20), "#212529"),
    B((50, 45, 15), (0, 100, 62), "#e63946", tint=True),
    C((50, 12, 50), (0, 25, 70), WHEEL, rot=(0, 0, 90)),
    C((50, 12, 50), (0, 25, -65), WHEEL, rot=(0, 0, 90)),
], fill=0.4, colors=["#e63946", "#f8f9fa", "#3a86ff", "#ffbe0b", "#8338ec", "#2b2d42"], flavor="上班上學都靠它。")
item("sn_bicycle", "腳踏車", "Bicycle", "交通", (55, 105, 175), [
    C((66, 6, 66), (0, 33, 55), WHEEL, rot=(0, 0, 90)),
    C((66, 6, 66), (0, 33, -55), WHEEL, rot=(0, 0, 90)),
    B((5, 5, 110), (0, 60, 0), "#3a86ff", rot=(12, 0, 0), tint=True),
    B((12, 6, 24), (0, 90, -25), "#212529"),
    B((55, 4, 4), (0, 100, 45), "#adb5bd"),
], fill=0.25, colors=["#3a86ff", "#e63946", "#06d6a0", "#ffbe0b"], sfx="bike_bell", flavor="叮叮！騎去冬山河邊吹風。")
item("sn_minitruck", "小貨車", "Mini Truck", "交通", (170, 190, 480), [
    B((170, 150, 140), (0, 105, 170), "#f1faee", tint=True),
    B((150, 50, 10), (0, 140, 241), GLASS, collide=False),
    B((170, 60, 330), (0, 70, -70), "#adb5bd"),
    B((150, 50, 200), (0, 125, -60), "#d9ed92", collide=False),
] + wheels(176, 35, 160, -120, d=70), colors=["#f1faee", "#3a86ff", "#e63946"], flavor="載著剛採的文旦，要送去市場。")
item("sn_tractor", "曳引機", "Tractor", "農業", (180, 280, 330), [
    B((90, 100, 200), (0, 120, 40), "#d62828"),
    B((140, 110, 120), (0, 210, -60), GLASS),
    B((150, 12, 130), (0, 272, -60), "#d62828"),
    C((160, 180, 160), (0, 80, -90), WHEEL, rot=(0, 0, 90)),
    C((90, 150, 90), (0, 45, 120), WHEEL, rot=(0, 0, 90)),
    C((10, 80, 10), (30, 200, 110), "#495057", collide=False),
], flavor="田裡耕田的大紅曳引機。")
item("sn_bus", "公車", "Bus", "交通", (250, 320, 1100), [
    B((250, 260, 1100), (0, 160, 0), "#2a9d8f", tint=True),
    B((254, 70, 1000), (0, 210, 0), "#3d5a80", collide=False),
    B((230, 20, 1000), (0, 300, 0), "#e9ecef", collide=False),
] + wheels(260, 50, 350, -350, d=100), colors=["#2a9d8f", "#f1faee", "#3a86ff", "#e9c46a"], flavor="往車站的公車。")
item("sn_firetruck", "消防車", "Fire Truck", "交通", (250, 330, 900), [
    B((250, 220, 900), (0, 140, 0), "#d62828"),
    B((240, 60, 10), (0, 200, 452), GLASS, collide=False),
    B((80, 30, 700), (0, 265, -80), "#adb5bd"),
    B((100, 15, 30), (0, 257, 400), "#3a86ff", collide=False),
] + wheels(260, 50, 300, -300, d=100), sfx="car_horn", flavor="紅色消防車，喔咿喔咿！")
item("sn_tanker", "油罐車", "Tanker Truck", "交通", (250, 350, 1100), [
    B((250, 260, 220), (0, 160, 440), "#f1faee"),
    C((240, 880, 240), (0, 210, -100), "#ced4da", rot=(90, 0, 0)),
    B((240, 40, 900), (0, 70, -100), "#495057"),
] + wheels(260, 50, 420, -350, d=100), flavor="要開去加油站的油罐車。")
item("sn_garbage_truck", "垃圾車", "Garbage Truck", "交通", (250, 320, 800), [
    B((250, 230, 200), (0, 150, 300), "#f1faee"),
    B((250, 280, 580), (0, 170, -100), "#ffd166"),
] + wheels(260, 50, 280, -250, d=100), flavor="每天晚上來收垃圾的黃色垃圾車。")
item("sn_excavator", "怪手", "Excavator", "工程", (300, 380, 800), [
    B((300, 90, 450), (0, 45, 0), "#343a40"),
    B((250, 160, 300), (0, 170, -40), "#ffbe0b"),
    B((120, 150, 120), (70, 300, 40), GLASS),
    B((60, 60, 450), (-50, 300, 250), "#ffbe0b", rot=(-30, 0, 0)),
    B((120, 80, 80), (-50, 120, 400), "#495057"),
], flavor="工地的黃色怪手。")
item("sn_container", "貨櫃", "Shipping Container", "工業", (244, 260, 1200), [
    B((244, 260, 1200), (0, 130, 0), "#e76f51", tint=True),
    B((248, 20, 1204), (0, 250, 0), "#495057", collide=False),
], colors=["#e76f51", "#2a9d8f", "#264653", "#e9c46a", "#3a86ff"], flavor="工廠旁邊堆著的大貨櫃。")
item("sn_street_tree", "行道樹", "Street Tree", "植物", (350, 650, 350), [
    C((50, 300, 50), (0, 150, 0), "#7f5539"),
    S((350, 330, 350), (0, 470, 0), "#52b788", tint=True),
    S((250, 220, 250), (60, 590, 30), "#52b788", collide=False, tint=True),
], fill=0.3, colors=["#52b788", "#40916c", "#74c69d", "#2d6a4f"], flavor="路邊的樹，夏天給大家遮陽。")
item("sn_pomelo_tree", "文旦樹（披白紗）", "Pomelo Tree in Net", "植物", (450, 420, 450), [
    C((50, 150, 50), (0, 75, 0), "#7f5539"),
    S((450, 300, 450), (0, 270, 0), "#40916c"),
    S((470, 310, 470), (0, 275, 0), "#f1f3f5", collide=False),
    S((45, 45, 45), (150, 160, 140), "#d9ed92", collide=False),
    S((45, 45, 45), (-160, 190, -60), "#d9ed92", collide=False),
], fill=0.3, sfx="orange",
    flavor="冬山是宜蘭縣文旦最大的產地。快採收時，果農會幫文旦樹罩上白色的網子保護果實。")
item("sn_kumquat", "金桔盆栽", "Kumquat Pot", "植物", (120, 160, 120), [
    C((90, 60, 90), (0, 30, 0), "#bc6c25"),
    S((120, 100, 120), (0, 110, 0), "#2d6a4f"),
    S((25, 25, 25), (40, 120, 35), "#f77f00", collide=False),
    S((25, 25, 25), (-35, 135, -30), "#f77f00", collide=False),
], fill=0.4, sfx="orange", flavor="冬山也種金桔，小小的橘色果子好可愛。")
item("sn_tea_row", "茶樹", "Tea Bushes", "農業", (150, 90, 600), [
    B((150, 70, 600), (0, 35, 0), "#2d6a4f"),
    C((150, 600, 150), (0, 70, 0), "#52b788", rot=(90, 0, 0), collide=False),
], flavor="山腳下一排一排的茶樹。")
item("sn_bus_stop", "公車亭", "Bus Shelter", "街道", (170, 260, 420), [
    B((170, 15, 420), (0, 252, 0), "#3a86ff"),
    B((10, 200, 400), (-75, 140, 0), "#caf0f8"),
    B((50, 10, 300), (-35, 45, 0), "#adb5bd"),
    B((10, 245, 10), (75, 122, 195), "#6c757d"),
    B((10, 245, 10), (75, 122, -195), "#6c757d"),
], fill=0.25, flavor="等公車去車站。")
item("sn_utility_pole", "電線桿", "Utility Pole", "街道", (200, 1000, 60), [
    C((30, 1000, 30), (0, 500, 0), "#adb5bd"),
    B((200, 15, 15), (0, 920, 0), "#6c757d"),
    C((50, 80, 50), (25, 800, 0), "#6c757d", collide=False),
], fill=0.2, flavor="田邊一根一根的電線桿。")
item("sn_scarecrow", "稻草人", "Scarecrow", "農業", (120, 190, 40), [
    B((8, 180, 8), (0, 90, 0), "#7f5539"),
    B((120, 8, 8), (0, 130, 0), "#7f5539"),
    B((50, 60, 25), (0, 110, 0), "#e63946", tint=True),
    S((35, 35, 35), (0, 160, 0), "#e9c46a"),
    K((60, 25, 60), (0, 182, 0), "#bc6c25"),
], fill=0.3, colors=["#e63946", "#3a86ff", "#06d6a0"], flavor="幫稻田趕麻雀的稻草人。")
item("sn_haystack", "稻草捆", "Haystack", "農業", (160, 180, 160), [
    C((160, 140, 160), (0, 70, 0), "#e9c46a"),
    K((170, 40, 170), (0, 160, 0), "#d4a373"),
], fill=0.6, flavor="割完稻子綁起來的稻草。")
item("sn_egret", "白鷺鷥", "Egret", "動物", (30, 90, 70), [
    S((30, 30, 50), (0, 55, 0), "#f8f9fa"),
    B((10, 30, 10), (0, 80, 18), "#f8f9fa"),
    B((4, 40, 4), (0, 20, 0), "#343a40", collide=False),
], fill=0.4, flavor="在稻田裡踩來踩去找小蟲吃的白鷺鷥。")
item("sn_buffalo", "水牛", "Water Buffalo", "動物", (130, 160, 280), [
    B((120, 110, 220), (0, 100, 0), "#4a4e69"),
    B((70, 60, 70), (0, 120, 140), "#4a4e69", name="head"),
    B((140, 10, 15), (0, 160, 150), "#e9ecef", collide=False),
    B((100, 50, 180), (0, 25, 0), "#3d405b"),
], fill=0.4, size=205.0,
    critter={"kind": "dog", "walk": 60, "run": 160, "sight": 1500, "paw_cooldown": 8.0, "sound": "bell"},
    flavor="慢慢走的水牛，脖子上的鈴鐺叮叮響。")
item("sn_duck", "鴨子", "Duck", "動物", (30, 35, 45), [
    S((30, 25, 40), (0, 15, 0), "#f8f9fa"),
    S((16, 16, 16), (0, 30, 15), "#f8f9fa", name="head"),
    B((8, 4, 10), (0, 30, 25), "#f77f00", collide=False),
], fill=0.5,
    critter={"kind": "dog", "walk": 40, "run": 120, "sight": 800, "paw_cooldown": 8.0, "sound": "duck"},
    flavor="在冬山河游來游去的鴨子，呱呱！")
item("sn_dragon_boat", "龍舟", "Dragon Boat", "河", (150, 150, 1800), [
    B((150, 60, 1700), (0, 30, 0), "#e63946", tint=True),
    B((154, 10, 1700), (0, 55, 0), "#ffd166", collide=False),
    B((60, 100, 80), (0, 90, 880), "#ffd166"),
    B((40, 80, 60), (0, 70, -870), "#ffd166"),
    C((50, 40, 50), (0, 80, 0), "#9d0208", collide=False),
], fill=0.35, colors=["#e63946", "#2a9d8f", "#3a86ff", "#f77f00"],
    flavor="冬山河是宜蘭龍舟比賽的場地，咚咚咚划起來！")
item("sn_gazebo", "涼亭", "Gazebo", "公園", (520, 450, 520), [
    B((500, 40, 500), (0, 20, 0), "#adb5bd"),
    B((30, 300, 30), (220, 190, 220), "#9c6644"),
    B((30, 300, 30), (-220, 190, -220), "#9c6644"),
    B((30, 300, 30), (220, 190, -220), "#9c6644", collide=False),
    B((30, 300, 30), (-220, 190, 220), "#9c6644", collide=False),
    K((620, 200, 620), (0, 350, 0), "#bc4749"),
], fill=0.3, flavor="河邊的涼亭，可以坐下來休息。")
item("sn_slide", "溜滑梯", "Playground Slide", "公園", (250, 330, 600), [
    B((200, 250, 200), (0, 125, -180), "#ffbe0b"),
    B((100, 10, 450), (0, 140, 100), "#3a86ff", rot=(32, 0, 0)),
    K((260, 80, 260), (0, 290, -180), "#e63946"),
    B((80, 200, 30), (0, 100, -300), "#06d6a0"),
], fill=0.3, sfx="squeak", flavor="公園裡的溜滑梯，咻～")
item("sn_shed", "鐵皮工具間", "Tin Shed", "農業", (440, 320, 540), [
    B((400, 260, 500), (0, 130, 0), "#ced4da", tint=True),
    B((440, 40, 540), (0, 280, 0), "#219ebc"),
    B((150, 200, 10), (0, 100, 252), "#6c757d", collide=False),
], colors=["#ced4da", "#f1faee", "#bde0fe"], flavor="放鋤頭和肥料的小鐵皮屋。")
item("sn_shrine", "土地公廟", "Tudigong Shrine", "廟", (460, 420, 420), [
    B((400, 60, 400), (0, 30, 0), "#adb5bd"),
    B((300, 250, 300), (0, 185, 0), "#e63946"),
    B((420, 50, 420), (0, 335, 0), "#ffbe0b"),
    B((460, 30, 60), (0, 375, 0), "#ffbe0b"),
    B((60, 30, 60), (220, 392, 0), "#2a9d8f", rot=(0, 0, 30), collide=False),
    B((60, 30, 60), (-220, 392, 0), "#2a9d8f", rot=(0, 0, -30), collide=False),
], sfx="bell", flavor="田邊的土地公廟，保佑大家平安。")
item("sn_vendor_cart", "攤車", "Food Cart", "街道", (150, 220, 250), [
    B((150, 90, 250), (0, 75, 0), "#f1faee"),
    B((170, 10, 270), (0, 212, 0), "#e63946", tint=True),
    B((10, 120, 10), (70, 150, 120), "#adb5bd", collide=False),
    C((60, 160, 60), (0, 30, 0), WHEEL, rot=(0, 0, 90)),
], fill=0.4, colors=["#e63946", "#f77f00", "#3a86ff", "#06d6a0"], flavor="賣烤玉米和三星蔥餅的小攤車。")
item("sn_vending", "自動販賣機", "Vending Machine", "街道", (100, 190, 80), [
    B((100, 190, 80), (0, 95, 0), "#3a86ff", tint=True),
    B((80, 90, 4), (0, 120, 41), "#caf0f8", collide=False),
], fill=0.6, colors=["#3a86ff", "#e63946", "#f8f9fa"], flavor="投錢就會掉出飲料。")
item("sn_mailbox", "郵筒", "Mailboxes", "街道", (120, 130, 50), [
    B((55, 110, 45), (-30, 55, 0), "#d62828"),
    B((55, 110, 45), (30, 55, 0), "#2d6a4f"),
    B((120, 12, 50), (0, 116, 0), "#495057", collide=False),
], fill=0.6, flavor="紅色和綠色的郵筒，一個寄急件、一個寄平信。")

item("sn_truck", "大貨車", "Lorry", "交通", (250, 360, 900), [
    B((250, 250, 220), (0, 165, 340), "#3a86ff", tint=True),
    B((240, 60, 10), (0, 230, 452), GLASS, collide=False),
    B((250, 280, 640), (0, 180, -120), "#f1faee"),
    B((230, 40, 860), (0, 50, -20), "#495057"),
] + wheels(260, 50, 320, -300, d=100), colors=["#3a86ff", "#e63946", "#2a9d8f", "#f77f00"], flavor="載滿貨物的大貨車。")
item("sn_tin_house", "鐵皮小屋", "Tin House", "建築", (720, 460, 920), [
    B((700, 330, 900), (0, 165, 0), "#bde0fe", tint=True),
    B((720, 60, 920), (0, 360, 0), "#219ebc", rot=(0, 0, 5)),
    B((200, 220, 10), (100, 110, 452), "#6c757d", collide=False),
    B((200, 100, 10), (-200, 200, 452), GLASS, collide=False),
], colors=["#bde0fe", "#f1faee", "#ffe5d9", "#d8f3dc"], flavor="田邊的鐵皮小屋，下雨時叮叮咚咚響。")
item("sn_bamboo", "竹叢", "Bamboo Clump", "植物", (500, 900, 500), [
    C((300, 700, 300), (0, 350, 0), "#6a994e"),
    C((500, 400, 500), (0, 700, 0), "#90be6d"),
    C((40, 900, 40), (120, 450, 80), "#a7c957", collide=False),
], fill=0.3, flavor="農舍後面的竹叢，風一吹沙沙響。")
item("sn_shade_tree", "遮蔭大樹", "Shade Tree", "植物", (650, 850, 650), [
    C((80, 400, 80), (0, 200, 0), "#7f5539"),
    S((650, 450, 650), (0, 600, 0), "#40916c", tint=True),
    S((420, 300, 420), (-80, 770, 60), "#52b788", collide=False, tint=True),
], fill=0.3, colors=["#40916c", "#2d6a4f", "#52b788"], flavor="廟口和路口常見的大樹，阿公阿嬤在樹下聊天。")
item("sn_stall_row", "市集攤棚", "Market Stalls", "街道", (400, 300, 900), [
    B((380, 90, 880), (0, 45, 0), "#f1faee"),
    B((400, 10, 900), (0, 290, 0), "#e63946", tint=True),
    B((10, 200, 10), (190, 190, 440), "#adb5bd", collide=False),
    B((360, 40, 860), (0, 110, 0), "#ffd166", collide=False),
], fill=0.35, colors=["#e63946", "#f77f00", "#3a86ff", "#06d6a0"], flavor="早市的攤棚，擺滿青菜和水果。")


# 第二層（5 到 20 公尺）：20 到 35 公尺的球
item("sn_farmhouse", "紅磚農舍", "Brick Farmhouse", "建築", (1300, 600, 1000), [
    B((1200, 380, 900), (0, 190, 0), "#b5523b"),
    B((1300, 60, 1000), (0, 410, 0), "#8d99ae"),
    C((150, 150, 150), (350, 515, 200), "#adb5bd"),
    B((150, 230, 10), (0, 115, 452), "#6c584c", collide=False),
    B((800, 120, 10), (0, 240, 452), GLASS, collide=False),
], flavor="田中央的紅磚農舍，屋頂上有水塔。")
item("sn_sanheyuan", "紅磚三合院", "Courtyard House", "建築", (2600, 700, 2200), [
    B((2600, 450, 700), (0, 225, -750), "#b5523b"),
    B((2700, 120, 800), (0, 510, -750), "#9d0208"),
    B((600, 400, 1500), (-1000, 200, 350), "#b5523b"),
    B((600, 400, 1500), (1000, 200, 350), "#b5523b"),
    B((700, 100, 1600), (-1000, 450, 350), "#9d0208"),
    B((700, 100, 1600), (1000, 450, 350), "#9d0208"),
], flavor="紅磚三合院，中間的大空地可以曬稻穀。")
item("sn_townhouse", "透天厝", "Townhouse", "建築", (500, 1300, 1500), [
    B((500, 1200, 1500), (0, 600, 0), "#e9ecef", tint=True),
    C((120, 120, 120), (100, 1260, -400), "#adb5bd"),
    B((420, 300, 10), (0, 150, 752), "#adb5bd", collide=False),
    B((440, 150, 10), (0, 520, 752), GLASS, collide=False),
    B((440, 150, 10), (0, 860, 752), GLASS, collide=False),
    B((480, 20, 100), (0, 400, 800), "#8d99ae", collide=False),
], model="sn_townhouse", colors=["#e9ecef", "#f8edeb", "#dde5b6", "#cddafd", "#ffe5d9", "#fde2e4"],
    flavor="一樓開店、樓上住人的透天厝。")
item("sn_shophouse", "店面透天厝", "Shop House", "建築", (600, 1000, 1200), [
    B((500, 950, 1100), (0, 475, 0), "#f8edeb", tint=True),
    B((600, 20, 200), (0, 330, 630), "#e63946", collide=False),
    B((420, 280, 10), (0, 140, 552), "#ffd166", collide=False),
    B((440, 150, 10), (0, 600, 552), GLASS, collide=False),
    C((120, 120, 120), (-100, 1010, -300), "#adb5bd"),
], colors=["#f8edeb", "#e9ecef", "#fff3b0", "#d8f3dc"], flavor="一樓是小吃店的透天厝，聞起來好香。")
item("sn_two_story", "兩層樓平房", "Two-Story House", "建築", (820, 720, 1000), [
    B((800, 640, 1000), (0, 320, 0), "#ffe5d9", tint=True),
    B((820, 60, 1020), (0, 670, 0), "#8d99ae"),
    B((600, 120, 10), (0, 420, 502), GLASS, collide=False),
    B((160, 230, 10), (-200, 115, 502), "#6c584c", collide=False),
], colors=["#ffe5d9", "#f8edeb", "#dde5b6", "#e9ecef"], flavor="巷子裡的兩層樓小房子。")
item("sn_train_car", "電聯車車廂", "Commuter Train Car", "鐵路", (300, 420, 2000), [
    B((300, 340, 2000), (0, 230, 0), "#f1faee"),
    B((304, 90, 1800), (0, 290, 0), "#3d5a80", collide=False),
    B((304, 30, 2000), (0, 200, 0), "#3a86ff", collide=False),
    B((260, 30, 1900), (0, 415, 0), "#adb5bd"),
    B((260, 60, 1600), (0, 30, 0), "#343a40"),
], model="sn_train_car", sfx="train_horn", flavor="往宜蘭、羅東方向的通勤電聯車。")
item("sn_train_set", "一整列電聯車", "Commuter Train (4 cars)", "鐵路", (300, 420, 8200), [
    B((300, 340, 8200), (0, 230, 0), "#f1faee"),
    B((304, 90, 8000), (0, 290, 0), "#3d5a80", collide=False),
    B((304, 30, 8200), (0, 200, 0), "#3a86ff", collide=False),
    B((260, 30, 8100), (0, 415, 0), "#adb5bd"),
    B((260, 60, 7800), (0, 30, 0), "#343a40"),
], fill=0.45, sfx="train_horn", flavor="四節車廂連在一起的火車，長長的一條。")
item("sn_big_tree", "大榕樹", "Banyan Tree", "植物", (1600, 1300, 1600), [
    C((250, 600, 250), (0, 300, 0), "#6f4e37"),
    S((1600, 700, 1600), (0, 850, 0), "#40916c"),
    S((1000, 500, 1000), (300, 1050, 200), "#52b788", collide=False),
], fill=0.3, flavor="廟口的老榕樹，樹下很涼快。")
item("sn_water_tower", "水塔", "Water Tower", "建築", (800, 2500, 800), [
    B((500, 1500, 500), (0, 750, 0), "#adb5bd"),
    C((800, 800, 800), (0, 1900, 0), "#e9ecef"),
    K((820, 200, 820), (0, 2400, 0), "#d62828"),
], fill=0.3, flavor="高高的水塔。")
item("sn_greenhouse", "溫室", "Greenhouse", "農業", (820, 400, 2000), [
    B((800, 300, 2000), (0, 150, 0), "#e0fbfc"),
    B((820, 100, 2000), (0, 350, 0), "#f1faee"),
], fill=0.3, flavor="種菜苗的溫室。")
item("sn_rice_silo", "穀倉", "Grain Silo", "農業", (640, 1500, 640), [
    C((600, 1300, 600), (0, 650, 0), "#ced4da"),
    K((640, 220, 640), (0, 1410, 0), "#adb5bd"),
], fill=0.5, flavor="存放稻穀的大圓筒。")
item("sn_pavilion", "河濱大涼亭", "Riverside Pavilion", "公園", (1000, 700, 1000), [
    B((1000, 60, 1000), (0, 30, 0), "#adb5bd"),
    B((60, 400, 60), (420, 260, 420), "#9c6644"),
    B((60, 400, 60), (-420, 260, -420), "#9c6644"),
    B((60, 400, 60), (420, 260, -420), "#9c6644", collide=False),
    B((60, 400, 60), (-420, 260, 420), "#9c6644", collide=False),
    K((1200, 280, 1200), (0, 560, 0), "#bc4749"),
], fill=0.3, flavor="河邊的大涼亭。")
item("sn_billboard", "大看板", "Billboard", "街道", (100, 850, 1000), [
    B((60, 500, 60), (0, 250, 0), "#6c757d"),
    B((40, 400, 1000), (0, 650, 0), "#ffbe0b", tint=True),
], fill=0.2, colors=["#ffbe0b", "#06d6a0", "#ff006e", "#3a86ff"], flavor="還沒貼上廣告的大看板。")
item("sn_power_tower", "高壓電塔", "Power Pylon", "建築", (2000, 5000, 1000), [
    B((1000, 1500, 1000), (0, 750, 0), "#adb5bd"),
    B((600, 2500, 600), (0, 2750, 0), "#adb5bd"),
    B((300, 1000, 300), (0, 4500, 0), "#adb5bd"),
    B((2000, 60, 100), (0, 4000, 0), "#adb5bd"),
    B((1600, 60, 100), (0, 3400, 0), "#adb5bd", collide=False),
], fill=0.12, flavor="田中央的高壓電塔，電線一路連到遠方。")

item("sn_row_houses", "連棟透天", "Row Houses", "建築", (2000, 1300, 1500), [
    B((2000, 1200, 1500), (0, 600, 0), "#e9ecef", tint=True),
    B((2004, 150, 1504), (0, 520, 0), GLASS, collide=False),
    B((2004, 150, 1504), (0, 860, 0), GLASS, collide=False),
    B((1960, 300, 10), (0, 150, 752), "#adb5bd", collide=False),
    C((150, 150, 150), (600, 1275, -300), "#adb5bd"),
], colors=["#e9ecef", "#f8edeb", "#dde5b6", "#cddafd"], flavor="四間連在一起的透天厝。")
item("sn_fire_station", "消防分隊", "Fire Station", "建築", (1800, 1000, 2000), [
    B((1800, 900, 2000), (0, 450, 0), "#f8f9fa"),
    B((1820, 100, 2020), (0, 950, 0), "#d62828"),
    B((1500, 400, 10), (0, 200, 1002), "#d62828", collide=False),
], flavor="消防車住的地方。")
item("sn_supermarket", "超市", "Supermarket", "建築", (2000, 700, 2500), [
    B((2000, 600, 2500), (0, 300, 0), "#fefae0"),
    B((2050, 100, 2550), (0, 650, 0), "#06d6a0"),
    B((1800, 250, 10), (0, 130, 1252), GLASS, collide=False),
], flavor="大家買菜的超市（沒有招牌，是遊戲裡的店）。")


# 第三層（20 到 50 公尺）：35 到 70 公尺的球
item("sn_temple", "廟", "Temple", "廟", (2500, 1800, 3500), [
    B((2500, 150, 3500), (0, 75, 0), "#adb5bd"),
    B((2200, 900, 3000), (0, 600, 0), "#e63946"),
    B((2600, 300, 3400), (0, 1200, 0), "#e09f3e"),
    B((2000, 150, 300), (0, 1425, 0), "#2a9d8f"),
    B((400, 200, 300), (1100, 1550, 0), "#2a9d8f", rot=(0, 0, 25), collide=False),
    B((400, 200, 300), (-1100, 1550, 0), "#2a9d8f", rot=(0, 0, -25), collide=False),
], model="sn_temple", sfx="bell", flavor="鎮上的廟，屋頂翹翹的燕尾好漂亮。")
item("sn_temple_big", "大廟", "Grand Temple", "廟", (4000, 2600, 5000), [
    B((4000, 200, 5000), (0, 100, 0), "#adb5bd"),
    B((3500, 1300, 4300), (0, 850, 0), "#e63946"),
    B((4200, 450, 4800), (0, 1725, 0), "#e09f3e"),
    B((3200, 200, 400), (0, 2050, 0), "#2a9d8f"),
], model="sn_temple", sfx="bell", flavor="大大的廟，逢年過節好熱鬧。")
item("sn_apartment", "公寓大樓", "Apartment Block", "建築", (2000, 2800, 1500), [
    B((2000, 2700, 1500), (0, 1350, 0), "#e9ecef", tint=True),
    B((2004, 200, 1504), (0, 700, 0), GLASS, collide=False),
    B((2004, 200, 1504), (0, 1500, 0), GLASS, collide=False),
    B((2004, 200, 1504), (0, 2300, 0), GLASS, collide=False),
    B((600, 200, 600), (0, 2800, 0), "#adb5bd"),
], colors=["#e9ecef", "#f8edeb", "#dde5b6", "#cddafd", "#ffe5d9"], flavor="八層樓的公寓。")
item("sn_tower", "十五樓大樓", "Tower Block", "建築", (3000, 5000, 3000), [
    B((3000, 4800, 3000), (0, 2400, 0), "#dee2e6", tint=True),
    B((3004, 250, 3004), (0, 1300, 0), GLASS, collide=False),
    B((3004, 250, 3004), (0, 2600, 0), GLASS, collide=False),
    B((3004, 250, 3004), (0, 3900, 0), GLASS, collide=False),
    B((900, 300, 900), (0, 4950, 0), "#adb5bd"),
], colors=["#dee2e6", "#e9ecef", "#f8edeb", "#cddafd"], flavor="從頂樓可以看到整片蘭陽平原。")
item("sn_tall_hotel", "大飯店", "Hotel Tower", "建築", (3500, 6000, 3000), [
    B((3500, 5800, 3000), (0, 2900, 0), "#f8edeb", tint=True),
    B((3504, 300, 3004), (0, 1500, 0), GLASS, collide=False),
    B((3504, 300, 3004), (0, 3000, 0), GLASS, collide=False),
    B((3504, 300, 3004), (0, 4500, 0), GLASS, collide=False),
    B((1200, 300, 1200), (0, 5950, 0), "#adb5bd"),
], colors=["#f8edeb", "#fff3b0", "#e9ecef"], flavor="來宜蘭玩的人住的大飯店。")
item("sn_factory", "工廠", "Factory", "工業", (4000, 1200, 3000), [
    B((4000, 900, 3000), (0, 450, 0), "#dee2e6"),
    B((4100, 150, 3100), (0, 975, 0), "#8ecae6"),
    C((300, 1200, 300), (1500, 600, -1000), "#adb5bd"),
    B((800, 500, 10), (0, 250, 1502), "#6c757d", collide=False),
], flavor="做食品罐頭的工廠。")
item("sn_warehouse", "倉庫", "Warehouse", "工業", (2000, 1200, 3000), [
    B((2000, 600, 3000), (0, 300, 0), "#adb5bd"),
    C((1600, 3000, 1600), (0, 400, 0), "#8ecae6", rot=(90, 0, 0)),
], flavor="圓圓屋頂的大倉庫。")
item("sn_gas_station", "加油站", "Gas Station", "街道", (2500, 600, 1800), [
    B((2500, 100, 1800), (0, 550, 0), "#f1faee"),
    B((2520, 40, 1820), (0, 480, 0), "#06d6a0", collide=False),
    B((100, 500, 100), (800, 250, 0), "#adb5bd"),
    B((100, 500, 100), (-800, 250, 0), "#adb5bd"),
    B((300, 180, 120), (500, 90, 0), "#2a9d8f"),
    B((300, 180, 120), (-500, 90, 0), "#2a9d8f"),
], fill=0.3, flavor="加油站（沒有招牌，是遊戲裡自己的加油站）。")
item("sn_rice_mill", "碾米廠", "Rice Mill", "農業", (2500, 1600, 3000), [
    B((2500, 900, 2000), (0, 450, 500), "#e9ecef"),
    B((2600, 120, 2100), (0, 960, 500), "#219ebc"),
    C((700, 1500, 700), (-700, 750, -1100), "#ced4da"),
    C((700, 1500, 700), (700, 750, -1100), "#ced4da"),
], flavor="把稻穀變成白米的碾米廠。")
item("sn_market", "傳統市場", "Market Hall", "建築", (3000, 900, 4000), [
    B((3000, 700, 4000), (0, 350, 0), "#ffe8d6"),
    B((3200, 150, 4200), (0, 775, 0), "#e76f51"),
    B((3100, 20, 400), (0, 350, 2200), "#e63946", collide=False),
], flavor="早上好熱鬧的傳統市場。")
item("sn_footbridge", "人行橋", "Footbridge", "河", (1200, 1300, 11000), [
    B((1200, 100, 11000), (0, 50, 0), "#e9ecef"),
    B((40, 120, 11000), (580, 160, 0), "#ced4da"),
    B((40, 120, 11000), (-580, 160, 0), "#ced4da"),
    B((100, 100, 5800), (0, 1000, -2700), "#f1faee", rot=(18, 0, 0), collide=False),
    B((100, 100, 5800), (0, 1000, 2700), "#f1faee", rot=(-18, 0, 0), collide=False),
    B((600, 500, 600), (0, -250, 0), "#adb5bd"),
], fill=0.25, flavor="跨過冬山河的人行橋，上面有白色的拱。")
item("sn_road_bridge", "冬山河大橋", "River Bridge", "河", (2400, 800, 11000), [
    B((2400, 150, 11000), (0, 75, 0), "#adb5bd"),
    B((30, 4, 10000), (0, 152, 0), "#ffffff", collide=False),
    B((80, 120, 11000), (1160, 210, 0), "#e9ecef"),
    B((80, 120, 11000), (-1160, 210, 0), "#e9ecef"),
    B((800, 600, 800), (0, -300, 2500), "#6c757d"),
    B((800, 600, 800), (0, -300, -2500), "#6c757d"),
], fill=0.25, flavor="車子開過冬山河的大橋。")

item("sn_hospital", "醫院大樓", "Hospital", "建築", (3500, 4000, 5000), [
    B((3500, 3800, 5000), (0, 1900, 0), "#f8f9fa"),
    B((3504, 300, 5004), (0, 1300, 0), GLASS, collide=False),
    B((3504, 300, 5004), (0, 2600, 0), GLASS, collide=False),
    B((1000, 300, 1000), (0, 3950, 0), "#adb5bd"),
    B((800, 800, 60), (0, 3300, 2530), "#e63946", collide=False),
], flavor="白色的醫院大樓，頂樓有直升機停機坪。")
item("sn_logistics", "物流中心", "Logistics Center", "工業", (5000, 1500, 5000), [
    B((5000, 1300, 5000), (0, 650, 0), "#dee2e6"),
    B((5100, 200, 5100), (0, 1400, 0), "#3a86ff"),
    B((4000, 500, 10), (0, 250, 2502), "#6c757d", collide=False),
], flavor="貨車進進出出的大倉庫。")


# 第四層（40 到 70 公尺）：70 到 100 公尺的球
item("sn_big_factory", "大工廠", "Large Factory", "工業", (6000, 1800, 5000), [
    B((6000, 1300, 5000), (0, 650, 0), "#dee2e6"),
    B((6100, 200, 5100), (0, 1400, 0), "#8ecae6"),
    C((500, 1800, 500), (2200, 900, -1800), "#adb5bd"),
    C((500, 1800, 500), (1400, 900, -1800), "#adb5bd"),
    C((1200, 900, 1200), (-2000, 1750, 1200), "#f1faee"),
], flavor="工業區裡最大的工廠。")
item("sn_sports_park", "運動公園看台", "Stadium Stand", "公園", (6000, 1500, 4000), [
    B((6000, 300, 4000), (0, 150, 0), "#adb5bd"),
    B((6000, 900, 1500), (0, 750, -1200), "#e9ecef"),
    B((6200, 100, 1800), (0, 1450, -1200), "#3a86ff"),
    B((5000, 20, 2000), (0, 310, 800), "#52b788", collide=False),
], fill=0.35, flavor="開運動會的看台。")
item("sn_station", "冬山車站", "Dongshan Station", "鐵路", (3600, 2200, 11000), [
    B((3600, 1200, 5000), (0, 600, 0), "#f1faee"),
    B((1000, 150, 11000), (-1200, 1425, 0), "#adb5bd"),
    B((1000, 150, 11000), (1200, 1425, 0), "#adb5bd"),
    B((3600, 120, 11000), (0, 2140, 0), "#f8f9fa"),
    B((3640, 400, 200), (0, 1900, 5400), "#52b788", collide=False),
    B((3640, 400, 200), (0, 1900, -5400), "#52b788", collide=False),
], model="sn_station", fill=0.5, sfx="train_horn",
    flavor="冬山車站是高架車站，月台上的白色棚架一圈一圈，像農場裡的大瓜棚。長到 90 公尺以上才黏得起來！")


# ---------- 場景 ----------

X0, X1 = -150000, 150000
Z0, Z1 = -120000, 120000
RIVER_N, RIVER_S = 15000, 24000          # 河堤頂端（地面邊緣）
WATER_N, WATER_S = 17000, 22000          # 河面範圍
RIVER_Y = -400
RAIL_X = 100000
VIADUCT_Z0, VIADUCT_Z1 = -70000, -20000  # 高架段（北端、南端）
DECK_Y = 1500

GROUND = "#9bc995"


def build():
    rng = random.Random(1004)
    lv = Level("station", "滾到冬山火車站",
               "原創場景：宜蘭冬山鄉的小鎮、稻田、文旦果園、冬山河、工廠區與住宅區，一路滾到高架的冬山車站。"
               "塊球 10 公尺到 100 公尺。單位公分；x 往東、z 往南。")

    # 地面（河道兩側分開）
    lv.floor("北岸地面", X0, Z0, X1 - X0, RIVER_N - Z0, y=0, pattern="grass", color=GROUND, repeat=3000, thickness=400)
    lv.floor("南岸地面", X0, RIVER_S, X1 - X0, Z1 - RIVER_S, y=0, pattern="grass", color=GROUND, repeat=3000, thickness=400)
    lv.floor("冬山河", X0, WATER_N, X1 - X0, WATER_S - WATER_N, y=RIVER_Y, pattern="water", color="#5aa9c9", repeat=2400, thickness=400)
    # 河堤緩坡（雙向都走得上去）
    lv.ramp("北岸河堤", (0, RIVER_Y, WATER_N), (0, 0, RIVER_N), width=X1 - X0, thickness=400, color="#86b86b")
    lv.ramp("南岸河堤", (0, RIVER_Y, WATER_S), (0, 0, RIVER_S), width=X1 - X0, thickness=400, color="#86b86b")

    # 外圍圍牆（遠處看起來像淡綠色的山坡）
    wall_c = "#9fc5a8"
    for a, b in [((X0, Z0), (X1, Z0)), ((X1, Z0), (X1, Z1)), ((X1, Z1), (X0, Z1)), ((X0, Z1), (X0, Z0))]:
        lv.wall(a, b, height=8500, thickness=3000, color=wall_c, y=-600)

    _roads(lv)
    _railway(lv)
    _town(lv, rng)
    _paddies(lv, rng)
    _orchard(lv, rng)
    _riverside(lv, rng)
    _factories(lv, rng)
    _neighborhood(lv, rng)
    _station_area(lv, rng)
    _mountains(lv)

    _thin(lv, 0.55, keep=("town_core",))
    lv.set_start((-112000, 4, 60000), -90)
    lv.set_rescue((-6000, 4, 8000), 0)
    lv.set_env(sky="#bfe0f5", fog_color="#cfe3ec", fog_per_d=0.006)
    lv.set_stage(
        start_cm=1000, goal_cm=10000, time_sec=600, comet_sec=330, seed=4004, music="station",
        intro="從冬山的小鎮出發，一路滾到冬山火車站！長到 100 公尺吧",
        zones=[], gates={}, tuning={},
        grades=[
            {"min_ratio": 0.0, "text": "星婆婆：車站好遠喔，再滾一次，這次一定到得了！"},
            {"min_ratio": 1.0, "text": "星婆婆：做到了！整個冬山都變成星星的一部分了。"},
            {"min_ratio": 1.3, "text": "星婆婆：連冬山河的大橋都滾起來了！"},
            {"min_ratio": 1.6, "text": "星婆婆：哇，連車站的大瓜棚都黏起來了嗎？"},
            {"min_ratio": 1.9, "text": "星婆婆：太厲害了！這顆星星大到從龜山島那邊都看得到吧！"},
        ],
    )
    return lv


def _roads(lv):
    asphalt = "#5c6168"
    # 東西向主幹道（橫過鐵路平交道）與南北向主幹道（過冬山河大橋）
    lv.floor("主幹道（東西）", X0, -1500, X1 - X0, 3000, y=4, pattern="asphalt", color=asphalt, repeat=1500, thickness=20)
    lv.floor("主幹道（南北，北段）", -21500, Z0, 3000, RIVER_N - Z0, y=4, pattern="asphalt", color=asphalt, repeat=1500, thickness=20)
    lv.floor("主幹道（南北，南段）", -21500, RIVER_S, 3000, Z1 - RIVER_S, y=4, pattern="asphalt", color=asphalt, repeat=1500, thickness=20)
    lv.decor("主幹道標線", "box", (0, 4, 0), (X1 - X0, 2, 40), "#f8f9fa", no_shadow=True)
    lv.decor("南北標線（北）", "box", (-20000, 4, (Z0 + RIVER_N) / 2), (40, 2, RIVER_N - Z0), "#f8f9fa", no_shadow=True)
    lv.decor("南北標線（南）", "box", (-20000, 4, (RIVER_S + Z1) / 2), (40, 2, Z1 - RIVER_S), "#f8f9fa", no_shadow=True)


def _railway(lv):
    ballast = "#a39e93"
    # 平面段的道碴（南段過河用鐵路橋）
    lv.floor("鐵路（南段）", RAIL_X - 1000, 0, 2000, Z1, y=8, pattern="gravel", color=ballast, repeat=800, thickness=20)
    lv.floor("鐵路（北段）", RAIL_X - 1000, Z0, 2000, -85000 - Z0, y=8, pattern="gravel", color=ballast, repeat=800, thickness=20)
    lv.block("鐵路橋", RAIL_X, -300, (RIVER_N + RIVER_S) / 2, 2000, 308, RIVER_S - RIVER_N + 400, color="#868e96")
    for z in (WATER_N + 1200, WATER_S - 1200):
        lv.block("鐵路橋墩", RAIL_X, RIVER_Y, z, 800, 300 - RIVER_Y - 300, 800, color="#6c757d")
    # 高架段：橋面與橋墩，兩端是引道坡（雙向通行）
    lv.block("高架橋面", RAIL_X, DECK_Y - 150, (VIADUCT_Z0 + VIADUCT_Z1) / 2, 1400, 150, VIADUCT_Z1 - VIADUCT_Z0, color="#ced4da")
    z = VIADUCT_Z0 + 2500
    while z < VIADUCT_Z1:
        lv.block("高架橋墩", RAIL_X, 0, z, 700, DECK_Y - 150, 700, color="#adb5bd")
        z += 5000
    lv.ramp("高架引道（北）", (RAIL_X, 0, -85000), (RAIL_X, DECK_Y, VIADUCT_Z0), width=1400, thickness=400, color="#ced4da")
    lv.ramp("高架引道（南）", (RAIL_X, 0, -5000), (RAIL_X, DECK_Y, VIADUCT_Z1), width=1400, thickness=400, color="#ced4da")
    # 鋼軌（裝飾）
    rail = "#6c757d"
    for dx in (-80, 80):
        lv.decor("鋼軌（南）", "box", (RAIL_X + dx, 8, Z1 / 2), (20, 18, Z1), rail, no_shadow=True)
        lv.decor("鋼軌（北）", "box", (RAIL_X + dx, 8, (Z0 - 85000) / 2), (20, 18, -85000 - Z0), rail, no_shadow=True)
        lv.decor("鋼軌（高架）", "box", (RAIL_X + dx, DECK_Y, (VIADUCT_Z0 + VIADUCT_Z1) / 2), (20, 18, VIADUCT_Z1 - VIADUCT_Z0), rail, no_shadow=True)


def _row(lv, item_id, x0, z, count, step, rot, rng, jitter=0):
    for i in range(count):
        lv.place(item_id, x0 + i * step + (rng.uniform(-jitter, jitter) if jitter else 0), 4, z, rot=rot)


def _town(lv, rng):
    """西南的起點小鎮：100 公尺見方的街廓、透天厝與店面，起點附近塞滿車子、攤棚、鐵皮屋（10 公尺的球一開始就忙不完）。"""
    tx0, tx1, tz0, tz1 = -140000, -68000, 34000, 98000
    lv.area("冬山小鎮", tx0, tz0, tx1 - tx0, tz1 - tz0)
    lv.floor("小鎮地面", tx0, tz0, tx1 - tx0, tz1 - tz0, y=2, pattern="concrete", color="#c8c3b8", repeat=3000, thickness=20)
    asphalt = "#5c6168"
    streets_z = list(range(40000, 96000, 10000))
    streets_x = list(range(-135000, -68000, 10000))
    for z in streets_z:
        lv.floor("小鎮街道", tx0, z - 1300, tx1 - tx0, 2600, y=5, pattern="asphalt", color=asphalt, repeat=1500, thickness=20)
    for x in streets_x:
        lv.floor("小鎮街道", x - 1300, tz0, 2600, tz1 - tz0, y=5, pattern="asphalt", color=asphalt, repeat=1500, thickness=20)
    # 街廓：沿東西向街道的北側放 2 到 3 間透天厝或店面（面向街道）
    n = 0
    for zi, z in enumerate(streets_z[1:]):
        for xi, x in enumerate(streets_x[:-1]):
            cx = x + 5000
            if (xi + zi) % 3 == 2:
                lv.place("sn_two_story", cx + rng.uniform(-2500, 2500), 4, z - 4500, rot=rng.choice([0, 90]))
                continue
            kind = "sn_shophouse" if (xi + zi) % 2 == 0 else "sn_townhouse"
            count = 3 if (xi + zi) % 2 == 0 else 2
            _row(lv, kind, cx - 1500, z - 1300 - 900 - 800, count, 640, 0, rng)
            n += count
    lv.place("sn_temple", -105000, 4, 66000 - 3500, rot=0)
    lv.place("sn_shade_tree", -101500, 4, 67500)
    lv.place("sn_market", -125000, 4, 76000, rot=90)
    lv.place("sn_water_tower", -137000, 4, 37000)
    lv.place("sn_apartment", -78000, 4, 45000, rot=0)
    lv.place("sn_apartment", -132000, 4, 86000, rot=90)
    lv.place("sn_fire_station", -88000, 4, 63000, rot=0)
    lv.place("sn_supermarket", -96000, 4, 84000, rot=90)
    for x, z in [(-136000, 52000), (-74000, 72000), (-118000, 93000), (-84000, 94000)]:
        lv.place("sn_row_houses", x, 4, z, rot=rng.choice([0, 90]))
    # 起點周圍 300 公尺見方：密集的 2 到 9 公尺物件
    lv.spawn("town_core", (-126000, 46000, 30000, 28000), 5, {
        "sn_car": 14, "sn_taxi": 3, "sn_minitruck": 6, "sn_bus": 5, "sn_truck": 6, "sn_container": 6,
        "sn_tin_house": 5, "sn_stall_row": 6, "sn_shade_tree": 5, "sn_street_tree": 6, "sn_vendor_cart": 3,
        "sn_scooter": 5, "sn_bicycle": 3, "sn_kumquat": 3, "sn_vending": 2, "sn_bus_stop": 2, "sn_firetruck": 1,
        "sn_garbage_truck": 1, "sn_mailbox": 1, "sn_shed": 3,
    }, avoid_furniture=True, exclude=[(-114500, 57500, 5000, 5000)])
    lv.spawn("town_outer", (tx0, tz0, tx1 - tx0, tz1 - tz0), 5, {
        "sn_car": 6, "sn_bus": 2, "sn_truck": 3, "sn_container": 3, "sn_tin_house": 4, "sn_bamboo": 3,
        "sn_shade_tree": 3, "sn_street_tree": 4, "sn_stall_row": 2, "sn_minitruck": 2, "sn_scooter": 2,
    }, avoid_furniture=True, exclude=[(-126000, 46000, 30000, 28000)])


def _paddies(lv, rng):
    """稻田：一塊一塊的秧苗田，中間是田埂（草地）與農路；農舍、稻草人、白鷺鷥、水牛。"""
    px0, px1, pz0, pz1 = -55000, 95000, 30000, 115000
    lv.area("稻田", px0, pz0, px1 - px0, pz1 - pz0)
    w, d, gap = 20000, 12500, 900
    x = px0
    col = 0
    while x + w <= px1 + 1:
        z = pz0
        while z + d <= pz1 + 1:
            # 南北向主幹道經過的那一欄留給道路
            if not (x < -18500 < x + w):
                lv.floor("稻田", x + gap / 2, z + gap / 2, w - gap, d - gap, y=3, pattern="paddy", color="#7dbb4f", repeat=2400, thickness=10)
            z += d
        x += w
        col += 1
    for zr in (55000, 80000, 105000):
        lv.floor("農路", px0, zr - 450, px1 - px0, 900, y=6, pattern="concrete", color="#c9c9c4", repeat=1200, thickness=20)
    farm_spots = [(-45000, 42000), (-5000, 56000), (25000, 44000), (52000, 69000), (-38000, 93000),
                  (10000, 82000), (40000, 106000), (75000, 92000), (68000, 48000), (-12000, 108000),
                  (30000, 68000), (85000, 62000), (-50000, 70000), (5000, 96000)]
    for i, (fx, fz) in enumerate(farm_spots):
        lv.place("sn_farmhouse", fx, 4, fz, rot=rng.choice([0, 90, 180, 270]))
        if i % 2 == 0:
            lv.place("sn_shed", fx + 1200, 4, fz + 300, rot=90)
    for sx, sz in [(-30000, 66000), (60000, 100000), (20000, 30500 + 2600), (-48000, 108000)]:
        lv.place("sn_sanheyuan", sx, 4, sz, rot=0)
    for x, z in [(-35000, 36000), (15000, 62000), (45000, 36000), (-5000, 90000), (70000, 78000), (-45000, 84000)]:
        lv.place("sn_two_story", x, 4, z, rot=rng.choice([0, 90, 180, 270]))
    lv.place("sn_rice_mill", 45000, 4, 88000, rot=90)
    for i in range(4):
        lv.place("sn_rice_silo", 49000 + i * 800, 4, 84000, rot=0)
    lv.place("sn_shrine", -24000, 4, 47000, rot=90)
    lv.place("sn_big_tree", -24000, 4, 51000)
    for i in range(6):
        lv.place("sn_power_tower", -50000 + i * 26000, 4, 75000 + (i % 2) * 1500, rot=90)
    for i, (bx, bz) in enumerate([(-15000, 62000), (35000, 58000), (60000, 85000), (-40000, 100000)]):
        lv.place("sn_buffalo", bx, 4, bz, rot=rng.randint(0, 359), roam=(bx - 3000, bz - 3000, 6000, 6000))
    lv.spawn("paddy_west", (px0, pz0, 36000, pz1 - pz0), 3, {
        "sn_haystack": 5, "sn_scarecrow": 3, "sn_egret": 5, "sn_tractor": 3, "sn_utility_pole": 3,
        "sn_minitruck": 2, "sn_shed": 2, "sn_car": 3, "sn_scooter": 1,
    }, avoid_furniture=True)
    lv.spawn("paddy_east", (-17000, pz0, px1 + 17000, pz1 - pz0), 3, {
        "sn_haystack": 6, "sn_scarecrow": 3, "sn_egret": 6, "sn_tractor": 3, "sn_utility_pole": 4,
        "sn_minitruck": 3, "sn_shed": 3, "sn_greenhouse": 4, "sn_car": 3, "sn_street_tree": 4,
    }, avoid_furniture=True)


def _orchard(lv, rng):
    """鐵路東側：文旦果園（樹罩白網）、茶園、溫室。"""
    ox0, ox1, oz0, oz1 = 103000, 145000, 28000, 115000
    lv.area("文旦果園與茶園", ox0, oz0, ox1 - ox0, oz1 - oz0)
    lv.floor("果園", ox0, oz0, ox1 - ox0, 50000, y=2, pattern="soil", color="#a98467", repeat=1500, thickness=20)
    for i in range(5):
        for j in range(4):
            lv.place("sn_pomelo_tree", ox0 + 4000 + i * 8000, 4, oz0 + 5000 + j * 11000, rot=rng.randint(0, 359))
    for i in range(7):
        for j in range(2):
            lv.place("sn_tea_row", ox0 + 4000 + i * 5000, 4, 88000 + j * 12000, rot=0)
    lv.place("sn_gazebo", 125000, 4, 81000)
    lv.place("sn_rice_mill", 135000, 4, 106000, rot=0)
    lv.spawn("orchard", (ox0, oz0, ox1 - ox0, oz1 - oz0), 4, {
        "sn_greenhouse": 3, "sn_shed": 3, "sn_minitruck": 2, "sn_tractor": 2, "sn_kumquat": 2,
        "sn_scooter": 1, "sn_haystack": 2, "sn_water_tower": 1,
    }, avoid_furniture=True)


def _riverside(lv, rng):
    """冬山河北岸的河濱公園：草地、自行車道、涼亭、溜滑梯、大樹；河上有龍舟、鴨子，四座橋。"""
    lv.area("冬山河畔", X0, 3000, X1 - X0, RIVER_S - 3000)
    lv.floor("河濱自行車道", X0, 12500, X1 - X0, 1200, y=6, pattern="concrete", color="#d8d5cc", repeat=1200, thickness=20)
    lv.place("sn_road_bridge", -20000, 0, (RIVER_N + RIVER_S) / 2, rot=0)
    lv.place("sn_road_bridge", -90000, 0, (RIVER_N + RIVER_S) / 2, rot=0)
    lv.place("sn_footbridge", 40000, 0, (RIVER_N + RIVER_S) / 2, rot=0)
    lv.place("sn_footbridge", 70000, 0, (RIVER_N + RIVER_S) / 2, rot=0)
    for i, x in enumerate((-60000, -40000, 15000, 55000, 85000, -130000)):
        lv.place("sn_dragon_boat", x, RIVER_Y, 18500 + (i % 3) * 1200, rot=90)
    for i, x in enumerate((-45000, -10000, 25000, 60000)):
        lv.place("sn_duck", x, RIVER_Y, 19500, rot=rng.randint(0, 359), roam=(x - 3000, WATER_N + 300, 6000, WATER_S - WATER_N - 600))
        lv.place("sn_duck", x + 400, RIVER_Y, 19900, rot=rng.randint(0, 359), roam=(x - 3000, WATER_N + 300, 6000, WATER_S - WATER_N - 600))
    for x in (-40000, 20000, 50000):
        lv.place("sn_pavilion", x, 4, 7000)
    for x in (-50000, -25000, 5000, 30000):
        lv.place("sn_big_tree", x, 4, 4500 + (x % 3) * 500)
    for x in (-33000, 12000, 42000):
        lv.place("sn_slide", x, 4, 9500, rot=90)
    lv.spawn("riverside", (-145000, 3000, 290000, 9000), 4, {
        "sn_gazebo": 5, "sn_bicycle": 4, "sn_street_tree": 8, "sn_scooter": 2, "sn_car": 5,
        "sn_vendor_cart": 2, "sn_bus_stop": 1, "sn_kumquat": 1,
    }, avoid_furniture=True, exclude=[(-10000, 4000, 8000, 8000), (RAIL_X - 1600, 0, 3200, 15000)])


def _factories(lv, rng):
    """西北的工業區：工廠、倉庫、貨櫃、油罐車、加油站、水塔、碾米廠、高壓電塔。"""
    fx0, fx1, fz0, fz1 = -145000, -60000, -115000, -3000
    lv.area("工業區", fx0, fz0, fx1 - fx0, fz1 - fz0)
    lv.floor("工業區地面", fx0, fz0, fx1 - fx0, fz1 - fz0, y=2, pattern="concrete", color="#c9c9c4", repeat=2000, thickness=20)
    for x, z in [(-130000, -20000), (-100000, -22000), (-75000, -40000), (-130000, -60000), (-100000, -95000), (-75000, -80000)]:
        lv.place("sn_factory", x, 4, z, rot=rng.choice([0, 90]))
    for x, z in [(-118000, -38000), (-88000, -55000), (-140000, -85000), (-112000, -75000), (-80000, -105000), (-65000, -20000)]:
        lv.place("sn_warehouse", x, 4, z, rot=rng.choice([0, 90]))
    for x, z in [(-115000, -105000), (-85000, -75000) , (-140000, -40000), (-70000, -60000), (-120000, -8000)]:
        lv.place("sn_big_factory", x, 4, z, rot=0)
    for x, z in [(-100000, -62000), (-135000, -112000 + 3000), (-70000, -112000 + 3000)]:
        lv.place("sn_logistics", x, 4, z, rot=0)
    lv.place("sn_gas_station", -60000, 4, -5500, rot=0)
    lv.place("sn_gas_station", 60000, 4, 5000, rot=180)
    for x, z in [(-95000, -35000), (-128000, -100000), (-66000, -95000)]:
        lv.place("sn_water_tower", x, 4, z)
    lv.place("sn_rice_mill", -66000, 4, -68000, rot=90)
    for i in range(6):
        lv.place("sn_power_tower", -140000 + i * 15000, 4, -50000 + i * 8000, rot=30)
    lv.spawn("factory_yard", (fx0, fz0, fx1 - fx0, fz1 - fz0), 4, {
        "sn_container": 12, "sn_tanker": 3, "sn_excavator": 3, "sn_minitruck": 3, "sn_car": 5,
        "sn_shed": 3, "sn_street_tree": 4, "sn_scooter": 2, "sn_utility_pole": 3, "sn_bus": 2,
        "sn_billboard": 2, "sn_greenhouse": 2,
    }, avoid_furniture=True)


def _neighborhood(lv, rng):
    """北邊中間的住宅區：透天厝、公寓、大樓、飯店、廟、市場、運動公園。"""
    nx0, nx1, nz0, nz1 = -55000, 88000, -115000, -3000
    lv.area("冬山住宅區", nx0, nz0, nx1 - nx0, nz1 - nz0)
    lv.floor("住宅區地面", nx0, nz0, nx1 - nx0, nz1 - nz0, y=2, pattern="concrete", color="#c8c3b8", repeat=3000, thickness=20)
    asphalt = "#5c6168"
    for z in (-30000, -60000, -90000):
        lv.floor("住宅區街道", nx0, z - 1500, nx1 - nx0, 3000, y=5, pattern="asphalt", color=asphalt, repeat=1500, thickness=20)
    for x in (20000, 55000):
        lv.floor("住宅區街道", x - 1500, nz0, 3000, nz1 - nz0, y=5, pattern="asphalt", color=asphalt, repeat=1500, thickness=20)
    # 主幹道兩側的透天厝
    for z in (-12000, -42000):
        _row(lv, "sn_townhouse", -17000, z, 4, 560, 270, rng)
        _row(lv, "sn_shophouse", -27000, z, 4, 600, 90, rng)
    for x, z in [(-45000, -20000), (-40000, -45000), (-5000, -20000), (8000, -45000), (35000, -20000), (35000, -45000),
                 (70000, -20000), (-45000, -75000), (5000, -75000), (35000, -75000), (70000, -75000), (-5000, -105000),
                 (45000, -105000), (75000, -50000)]:
        lv.place("sn_apartment", x, 4, z, rot=rng.choice([0, 90]))
    for x, z in [(-30000, -70000), (0, -60000 - 9000), (28000, -60000 - 9000), (62000, -38000), (-35000, -100000),
                 (15000, -100000), (62000, -100000), (75000, -10000), (-48000, -33000), (45000, -85000)]:
        lv.place("sn_tower", x, 4, z, rot=0)
    for x, z in [(-20000 + 6000, -82000), (40000, -10000 + -2000), (68000, -65000), (-48000, -58000), (25000, -112000 + 4000)]:
        lv.place("sn_tall_hotel", x, 4, z, rot=0)
    for x, z in [(-35000, -12000), (12000, -28000), (48000, -30000), (-10000, -55000), (60000, -88000), (25000, -40000),
                 (-50000, -88000), (80000, -30000)]:
        lv.place("sn_row_houses", x, 4, z, rot=rng.choice([0, 90]))
    lv.place("sn_supermarket", 48000, 4, -62000, rot=0)
    lv.place("sn_fire_station", -38000, 4, -28000, rot=90)
    for x, z in [(-25000, -88000), (50000, -112000 + 3000), (78000, -95000)]:
        lv.place("sn_hospital", x, 4, z, rot=0)
    lv.place("sn_temple", 0, 4, -40000, rot=0)
    lv.place("sn_big_tree", 0, 4, -34500)
    lv.place("sn_temple_big", 30000, 4, -95000 + 1000, rot=0)
    lv.place("sn_market", 10000, 4, -10000, rot=0)
    lv.place("sn_sports_park", -30000, 4, -108000 + 2000, rot=0)
    lv.spawn("neighborhood_a", (nx0, nz0, 70000, nz1 - nz0), 5, {
        "sn_car": 8, "sn_scooter": 4, "sn_street_tree": 6, "sn_bicycle": 2, "sn_vendor_cart": 2,
        "sn_utility_pole": 3, "sn_bus": 2, "sn_taxi": 2, "sn_shrine": 1, "sn_garbage_truck": 1, "sn_billboard": 1,
    }, avoid_furniture=True)
    lv.spawn("neighborhood_b", (15000, nz0, nx1 - 15000, nz1 - nz0), 5, {
        "sn_car": 7, "sn_scooter": 3, "sn_street_tree": 6, "sn_bicycle": 2, "sn_minitruck": 2,
        "sn_utility_pole": 3, "sn_bus": 2, "sn_shed": 2, "sn_firetruck": 1, "sn_container": 2, "sn_billboard": 1,
    }, avoid_furniture=True)


def _station_area(lv, rng):
    """東北：高架的冬山車站、站前廣場（公車、計程車、停車場）、鐵路上的電聯車、車站北側的森林公園。"""
    lv.area("冬山車站", 86000, -75000, 59000, 72000)
    lv.floor("站前廣場", 84000, -60000, 14500, 30000, y=6, pattern="paving", color="#e3d5ca", repeat=1000, thickness=20)
    station_z = -45000
    lv.place("sn_station", RAIL_X, 4, station_z, rot=0)
    # 月台樓梯（大積木）：從廣場（西）與東側地面上到月台
    lv.stairs_up("車站西側樓梯", top=(RAIL_X - 1700, DECK_Y, station_z - 2500), facing=270, width=1600, slope_deg=32,
                 base_y=6, step=150, style="blocks", colors=["#f1faee", "#ced4da", "#adb5bd"])
    lv.stairs_up("車站東側樓梯", top=(RAIL_X + 1700, DECK_Y, station_z + 2500), facing=90, width=1600, slope_deg=32,
                 base_y=4, step=150, style="blocks", colors=["#f1faee", "#ced4da", "#adb5bd"])
    # 高架上與平面段的電聯車
    for z in (-62000, -27000):
        for i in range(2):
            lv.place("sn_train_car", RAIL_X, DECK_Y, z + i * 2100, rot=0)
    for z in (-100000, -95000, 40000, 45000, 60000, 65000):
        lv.place("sn_train_car", RAIL_X, 10, z, rot=0)
    lv.place("sn_train_set", RAIL_X, 10, -110000 + 4000, rot=0)
    lv.place("sn_train_set", RAIL_X, 10, 95000, rot=0)
    # 森林公園（車站北側）
    lv.area("森林公園", 103000, -115000, 42000, 40000)
    lv.floor("森林公園草地", 103000, -115000, 42000, 40000, y=2, pattern="grass", color="#8cc084", repeat=2500, thickness=20)
    for i in range(5):
        lv.place("sn_big_tree", 108000 + i * 8000, 4, -108000 + (i % 2) * 9000)
    lv.place("sn_pavilion", 125000, 4, -88000)
    lv.place("sn_tower", 125000, 4, -30000, rot=0)
    lv.place("sn_tall_hotel", 132000, 4, -60000, rot=0)
    lv.place("sn_big_factory", 125000, 4, -8000 - 4000, rot=90)
    lv.spawn("station_plaza", (84000, -60000, 14500, 30000), 6, {
        "sn_bus": 4, "sn_taxi": 4, "sn_car": 6, "sn_scooter": 4, "sn_bicycle": 3, "sn_bus_stop": 2,
        "sn_vending": 2, "sn_vendor_cart": 1, "sn_street_tree": 3, "sn_mailbox": 1,
    }, avoid_furniture=True)
    lv.spawn("station_east", (103000, -75000, 42000, 72000), 4, {
        "sn_car": 5, "sn_scooter": 2, "sn_street_tree": 5, "sn_container": 4, "sn_gazebo": 2,
        "sn_shed": 2, "sn_minitruck": 2, "sn_slide": 1, "sn_utility_pole": 2,
    }, avoid_furniture=True, exclude=[(RAIL_X - 1600, -120000, 3200, 120000)])
    lv.spawn("forest_park", (103000, -115000, 42000, 40000), 4, {
        "sn_gazebo": 2, "sn_street_tree": 6, "sn_bicycle": 2, "sn_slide": 1,
    }, avoid_furniture=True)


def _thin(lv, factor, keep=()):
    """效能預算：起點以外的散布區，5 公尺以下的小東西按比例減量（大球時它們幾乎不影響成長）。"""
    by_id = {d["id"]: d for d in ITEMS}
    for sp in lv.d["spawns"]:
        if sp["zone"] in keep:
            continue
        for k, n in list(sp["items"].items()):
            if size_of(by_id[k]) < 500 and n > 1:
                sp["items"][k] = max(1, round(n * factor))


def _mountains(lv):
    """遠山（裝飾，不碰撞）：西邊與南邊，藍綠色。蘭陽平原被雪山山脈與中央山脈環抱。
    山腳一律在外圍圍牆之外，不會蓋到遊戲範圍。"""
    colors = ["#6b8f71", "#5f8575", "#78967c", "#6a8a80"]
    out = 8000
    # 西邊一排（沿 z 方向），南邊一排（沿 x 方向）；(沿線位置, 底面直徑, 高)
    west = [(-100000, 220000, 90000), (-10000, 260000, 110000), (90000, 230000, 95000)]
    south = [(-140000, 240000, 100000), (-20000, 280000, 120000), (100000, 250000, 105000), (210000, 220000, 85000)]
    i = 0
    for z, w, h in west:
        lv.decor("遠山（西）", "cone", (X0 - w / 2 - out, -600, z), (w, h, w), colors[i % 4], no_shadow=True)
        i += 1
    for x, w, h in south:
        lv.decor("遠山（南）", "cone", (x, -600, Z1 + w / 2 + out), (w, h, w), colors[i % 4], no_shadow=True)
        i += 1


# ---------- 成長模擬（檢查材料夠不夠） ----------

def size_of(d):
    if "size" in d:
        return d["size"]
    a = sorted(d["dims"])
    return math.sqrt(a[2] * a[1])


def simulate(lv, start=1000.0, goal=10000.0, efficiency=1.0):
    """理想情況：每次黏起目前黏得到的最大物件（efficiency 為實際黏到的比例）。回傳最後直徑與經過的里程碑。"""
    by_id = {d["id"]: d for d in ITEMS}
    pool = []
    for p in lv.d["placements"]:
        pool.append(by_id[p["item"]])
    for s in lv.d["spawns"]:
        for k, n in s["items"].items():
            pool += [by_id[k]] * n
    pool.sort(key=size_of)
    vol = start ** 3
    taken = [False] * len(pool)
    marks = {}
    acc = 0.0
    while True:
        d = vol ** (1 / 3)
        for m in (2000, 3500, 6000, 8000, 10000):
            if d >= m and m not in marks:
                marks[m] = sum(taken)
        best = -1
        for i, it in enumerate(pool):
            if not taken[i] and size_of(it) <= d * 0.7:
                best = i
        if best < 0:
            break
        taken[best] = True
        acc += efficiency
        if acc >= 1.0:
            acc -= 1.0
            vol += size_of(pool[best]) ** 3 * pool[best].get("fill", 0.5)
    return vol ** (1 / 3), marks, len(pool)


def histogram(lv):
    by_id = {d["id"]: d for d in ITEMS}
    counts = {}
    total = 0
    for p in lv.d["placements"]:
        counts[p["item"]] = counts.get(p["item"], 0) + 1
    for s in lv.d["spawns"]:
        for k, n in s["items"].items():
            counts[k] = counts.get(k, 0) + n
    bins = [(0, 200), (200, 500), (500, 700), (700, 1400), (1400, 2000), (2000, 3000), (3000, 4500), (4500, 7000)]
    out = []
    for lo, hi in bins:
        n = sum(c for k, c in counts.items() if lo <= size_of(by_id[k]) < hi)
        total += n
        out.append(f"{lo / 100:g} 到 {hi / 100:g} 公尺：{n} 件")
    return out, total


def main():
    lv = build()
    ITEMS_OUT.parent.mkdir(parents=True, exist_ok=True)
    ITEMS_OUT.write_text(json.dumps({
        "_note": "第 4 關「滾到冬山火車站」的物件（10 到 100 公尺）。由 tools/levels/build_station.py 產生，請改腳本再重新產生。",
        "items": ITEMS,
    }, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")
    print(f"[station] 物件定義 {len(ITEMS)} 種 → {ITEMS_OUT.name}")
    lv.save()
    lines, total = histogram(lv)
    print(f"[station] 物件總數 {total} 件")
    for line in lines:
        print("   ", line)
    for eff in (1.0, 0.7, 0.5):
        final, marks, n = simulate(lv, efficiency=eff)
        ms = "、".join(f"{m // 100}m 時黏了 {c} 件" for m, c in sorted(marks.items()))
        print(f"[station] 成長模擬（黏到 {int(eff * 100)}%）：最後 {final / 100:.1f} 公尺；{ms}")


if __name__ == "__main__":
    main()
