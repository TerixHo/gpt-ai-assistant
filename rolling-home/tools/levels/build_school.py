"""第 3 關「小學與街區」：產生物件定義 data/items/school.json 與場景配置 data/levels/school.json。

故事：槿寶滾進小學大門時已經 3 公尺，要在校園和附近街區長到 10 公尺。
校園有操場跑道、司令台、升旗台、遊戲場（溜滑梯、鞦韆、蹺蹺板、攀爬架）、籃球場、腳踏車棚、校車；
校外南邊是大馬路與街區（平房、商店、攤販、汽車、機車），東邊是稻田與農機。

執行（在 rolling-home 資料夾）：
    python3 tools/levels/build_school.py

單位公分；x 往東、z 往南、y 往上。校門在南邊（z = 6000），起點在校門內往北看。
第 2 關的 st_ 物件（機車、腳踏車、電線桿、小樹、汽車…）在這一關變成小東西，直接沿用。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from levelkit import Level  # noqa: E402
from build_street import ROOT, budget, item, part, save_items, street_items, wheel  # noqa: E402


# ---------- 第 3 關物件 ----------

def school_items():
    it = []
    A = it.append

    # 校園設施
    A(item("sc_classroom", "教室大樓", "Classroom Building", "建築", [1600, 1300, 1600], [
        part("box", [1600, 1240, 1600], [0, 620, 0], "#ead7c0"),
        part("box", [1640, 60, 1640], [0, 1270, 0], "#c1121f"),
        part("box", [1604, 120, 1500], [0, 300, 0], "#a2d2ff", collide=False),
        part("box", [1604, 120, 1500], [0, 700, 0], "#a2d2ff", collide=False),
        part("box", [1500, 120, 1604], [0, 1050, 0], "#a2d2ff", collide=False)],
        fill=0.2, pickable=False, flavor="三層樓的教室，槿寶的教室在二樓。"))
    A(item("sc_slide", "溜滑梯", "Slide", "遊戲場", [120, 260, 460], [
        part("box", [120, 200, 120], [0, 100, 150], "#ffbe0b"),
        part("box", [80, 30, 330], [0, 110, -60], "#3a86ff", rot=[-28, 0, 0])],
        fill=0.25, model="sc_slide", sfx="squeak", flavor="下課搶著玩的溜滑梯。"))
    A(item("sc_swing", "鞦韆", "Swing Set", "遊戲場", [320, 250, 180], [
        part("box", [8, 260, 8], [-155, 122, -42], "#e63946", rot=[-19, 0, 0]),
        part("box", [8, 260, 8], [-155, 122, 42], "#e63946", rot=[19, 0, 0]),
        part("box", [8, 260, 8], [155, 122, -42], "#e63946", rot=[-19, 0, 0]),
        part("box", [8, 260, 8], [155, 122, 42], "#e63946", rot=[19, 0, 0]),
        part("cylinder", [12, 320, 12], [0, 245, 0], "#e63946", rot=[0, 0, 90]),
        part("box", [50, 5, 22], [-70, 50, 0], "#ffbe0b", collide=False),
        part("box", [50, 5, 22], [70, 50, 0], "#ffbe0b", collide=False)],
        fill=0.15, flavor="盪得越高越開心的鞦韆。"))
    A(item("sc_seesaw", "蹺蹺板", "Seesaw", "遊戲場", [60, 80, 400], [
        part("box", [40, 50, 40], [0, 25, 0], "#6c757d"),
        part("box", [36, 8, 400], [0, 55, 0], "#8ac926", rot=[8, 0, 0]),
        part("box", [50, 30, 6], [0, 80, -170], "#e63946", collide=False)],
        fill=0.2))
    A(item("sc_jungle_gym", "攀爬架", "Jungle Gym", "遊戲場", [300, 200, 300], [
        part("box", [300, 8, 8], [0, 196, -146], "#3a86ff"),
        part("box", [300, 8, 8], [0, 196, 146], "#3a86ff"),
        part("box", [8, 8, 300], [0, 196, 0], "#3a86ff", collide=False),
        part("box", [8, 200, 8], [-146, 100, -146], "#ff006e"),
        part("box", [8, 200, 8], [146, 100, -146], "#ff006e"),
        part("box", [8, 200, 8], [-146, 100, 146], "#ff006e"),
        part("box", [8, 200, 8], [146, 100, 146], "#ff006e"),
        part("box", [300, 8, 8], [0, 100, 0], "#ffbe0b", collide=False)],
        fill=0.12))
    A(item("sc_spring_rider", "搖搖馬", "Spring Rider", "遊戲場", [40, 90, 80], [
        part("cylinder", [30, 40, 30], [0, 20, 0], "#adb5bd"),
        part("sphere", [36, 40, 76], [0, 62, 0], "#ff8fab", tint=True)],
        fill=0.4, colors=["#ff8fab", "#8ac926", "#ffbe0b", "#3a86ff"], sfx="squeak"))
    A(item("sc_basketball_hoop", "籃球架", "Basketball Hoop", "運動", [180, 395, 300], [
        part("box", [160, 40, 200], [0, 20, 60], "#1d4e89"),
        part("cylinder", [20, 340, 20], [0, 210, 80], "#adb5bd"),
        part("box", [16, 16, 120], [0, 360, 10], "#adb5bd"),
        part("box", [180, 105, 6], [0, 340, -50], "#f8f9fa"),
        part("cylinder", [46, 4, 46], [0, 305, -76], "#fb8500", collide=False)],
        fill=0.15))
    A(item("sc_soccer_goal", "足球門", "Soccer Goal", "運動", [500, 200, 150], [
        part("box", [10, 200, 10], [-245, 100, -70], "#f8f9fa"),
        part("box", [10, 200, 10], [245, 100, -70], "#f8f9fa"),
        part("box", [500, 10, 10], [0, 195, -70], "#f8f9fa"),
        part("box", [500, 200, 140], [0, 100, 5], "#dee2e6", collide=False)],
        fill=0.1))
    A(item("sc_flagpole", "旗桿", "Flagpole", "校園", [30, 1000, 30], [
        part("cylinder", [30, 40, 30], [0, 20, 0], "#6c757d"),
        part("cylinder", [14, 960, 14], [0, 520, 0], "#e9ecef"),
        part("box", [4, 90, 140], [0, 900, 72], "#3a86ff", collide=False, tint=True)],
        fill=0.15, colors=["#3a86ff", "#2b9348", "#ffbe0b"], flavor="每天早上升旗的旗桿。"))
    A(item("sc_bench", "長椅", "Bench", "校園", [180, 45, 50], [
        part("box", [180, 6, 50], [0, 42, 0], "#b08968"),
        part("box", [10, 39, 40], [-75, 19.5, 0], "#495057"),
        part("box", [10, 39, 40], [75, 19.5, 0], "#495057")],
        fill=0.3))
    A(item("sc_flower_bed", "花圃", "Flower Bed", "植物", [200, 50, 100], [
        part("box", [200, 35, 100], [0, 17.5, 0], "#b5523b"),
        part("box", [190, 12, 90], [0, 40, 0], "#52b788", collide=False),
        part("sphere", [26, 20, 26], [-60, 50, 10], "#ff006e", collide=False),
        part("sphere", [26, 20, 26], [0, 50, -15], "#ffbe0b", collide=False),
        part("sphere", [26, 20, 26], [60, 50, 12], "#c77dff", collide=False)],
        fill=0.5, flavor="小朋友輪流澆水的花圃。"))
    A(item("sc_hurdle", "跨欄", "Hurdle", "運動", [120, 90, 60], [
        part("box", [120, 12, 4], [0, 84, 0], "#f8f9fa"),
        part("box", [6, 84, 6], [-57, 42, 0], "#495057"),
        part("box", [6, 84, 6], [57, 42, 0], "#495057"),
        part("box", [120, 4, 60], [0, 2, 10], "#495057")],
        fill=0.15))
    A(item("sc_ball_cart", "球車", "Ball Cart", "運動", [80, 90, 60], [
        part("box", [80, 60, 60], [0, 50, 0], "#adb5bd"),
        part("sphere", [26, 26, 26], [-20, 82, 0], "#fb8500", collide=False),
        part("sphere", [26, 26, 26], [10, 84, 8], "#fb8500", collide=False),
        part("sphere", [26, 26, 26], [22, 80, -8], "#f8f9fa", collide=False)],
        fill=0.3, flavor="裝滿籃球和排球的球車。"))
    A(item("sc_podium", "司令台講桌", "Podium", "校園", [100, 110, 60], shape="box", color="#9c6644", fill=0.5))
    A(item("sc_speaker", "大音箱", "PA Speaker", "校園", [60, 100, 60], [
        part("box", [60, 100, 60], [0, 50, 0], "#343a40"),
        part("cylinder", [40, 4, 40], [0, 60, -30], "#6c757d", rot=[90, 0, 0], collide=False)],
        fill=0.5, sfx="school_bell"))
    A(item("sc_school_drum", "大鼓", "Big Drum", "校園", [100, 90, 100], [
        part("cylinder", [100, 70, 100], [0, 55, 0], "#c1121f"),
        part("cylinder", [104, 4, 104], [0, 90, 0], "#f1faee"),
        part("box", [80, 20, 80], [0, 10, 0], "#6b4f3a")],
        fill=0.4, sfx="bell"))
    A(item("sc_bike_shed", "腳踏車棚", "Bike Shed", "校園", [800, 250, 300], [
        part("box", [800, 10, 300], [0, 245, 0], "#2a9d8f"),
        part("box", [12, 240, 12], [-390, 120, -140], "#adb5bd"),
        part("box", [12, 240, 12], [390, 120, -140], "#adb5bd"),
        part("box", [12, 240, 12], [-390, 120, 140], "#adb5bd"),
        part("box", [12, 240, 12], [390, 120, 140], "#adb5bd")],
        fill=0.1))
    A(item("sc_school_bus", "校車", "School Bus", "交通", [250, 320, 1000], [
        part("box", [250, 290, 1000], [0, 175, 0], "#ffbe0b")],
        fill=0.35, model="sc_school_bus", sfx="car_horn", flavor="載住比較遠的小朋友上學的校車。"))
    A(item("sc_palm", "大王椰子", "Royal Palm", "植物", [300, 1200, 300], [
        part("cylinder", [55, 1000, 55], [0, 500, 0], "#b7a99a"),
        part("cylinder", [60, 140, 60], [0, 1050, 0], "#52b788"),
        part("sphere", [320, 110, 320], [0, 1140, 0], "#2d6a4f", collide=False),
        part("cone", [140, 90, 140], [0, 1215, 0], "#40916c", collide=False)],
        fill=0.15, flavor="校門口兩排高高的大王椰子。"))
    A(item("sc_camphor", "老樟樹", "Old Camphor Tree", "植物", [550, 750, 550], [
        part("cylinder", [90, 300, 90], [0, 150, 0], "#6b4f3a"),
        part("sphere", [550, 470, 550], [0, 510, 0], "#2d6a4f")],
        fill=0.25, flavor="校園裡最老的樟樹，夏天下面最涼。"))
    A(item("sc_street_tree", "行道樹", "Street Tree", "植物", [300, 500, 300], [
        part("cylinder", [36, 220, 36], [0, 110, 0], "#7f5539"),
        part("sphere", [300, 300, 300], [0, 350, 0], "#40916c")],
        fill=0.25))
    A(item("sc_pickup", "小貨車", "Pickup Truck", "交通", [170, 190, 470], [
        part("box", [170, 90, 470], [0, 65, 0], "#f1faee", tint=True),
        part("box", [160, 80, 160], [0, 150, -140], "#f1faee", tint=True),
        part("box", [150, 50, 4], [0, 160, -222], "#3d5a80", collide=False),
        wheel(64, 24, [-78, 32, -150]), wheel(64, 24, [78, 32, -150]),
        wheel(64, 24, [-78, 32, 150])],
        fill=0.35, colors=["#f1faee", "#3a86ff", "#adb5bd"], sfx="car_horn", flavor="載文旦、載菜的小貨車。"))
    A(item("sc_truck", "卡車", "Truck", "交通", [250, 320, 750], [
        part("box", [240, 260, 180], [0, 160, -280], "#e63946", tint=True),
        part("box", [250, 220, 540], [0, 170, 100], "#e9ecef"),
        wheel(100, 30, [-105, 50, -270]), wheel(100, 30, [105, 50, -270]),
        wheel(100, 30, [-105, 50, 250]), wheel(100, 30, [105, 50, 250])],
        fill=0.35, colors=["#e63946", "#3a86ff", "#2b9348"], sfx="car_horn"))
    A(item("sc_tractor", "耕耘機", "Tractor", "農具", [180, 220, 380], [
        part("box", [120, 100, 200], [0, 110, -60], "#d62828"),
        wheel(140, 40, [-80, 70, 70], "#343a40"), wheel(140, 40, [80, 70, 70], "#343a40"),
        wheel(70, 24, [-60, 35, -130], "#343a40"), wheel(70, 24, [60, 35, -130], "#343a40"),
        part("box", [90, 90, 10], [0, 190, 40], "#212529", collide=False)],
        fill=0.3, flavor="在田裡犁田的耕耘機。"))
    A(item("sc_hay_bale", "稻草捲", "Rice Straw Bale", "農具", [150, 150, 150], [
        part("cylinder", [150, 150, 150], [0, 75, 0], "#e9c46a", rot=[0, 0, 90])],
        fill=0.6, flavor="收割後捲起來的稻草。"))
    A(item("sc_container", "貨櫃", "Shipping Container", "建材", [244, 259, 606], shape="box", color="#2a9d8f",
         fill=0.5, colors=["#2a9d8f", "#e76f51", "#3a86ff", "#adb5bd"]))
    A(item("sc_shed", "鐵皮工具屋", "Tin Tool Shed", "建築", [400, 300, 500], [
        part("box", [400, 260, 500], [0, 130, 0], "#8ecae6"),
        part("box", [420, 40, 520], [0, 280, 0], "#adb5bd"),
        part("box", [160, 200, 4], [0, 100, -251], "#6c757d", collide=False)],
        fill=0.4))
    A(item("sc_stall", "攤販車", "Food Cart", "街道", [150, 220, 260], [
        part("box", [150, 100, 240], [0, 70, 0], "#f8f9fa"),
        part("box", [150, 10, 260], [0, 215, 0], "#e63946", tint=True),
        part("box", [8, 100, 8], [-70, 165, -120], "#adb5bd", collide=False),
        part("box", [8, 100, 8], [70, 165, 120], "#adb5bd", collide=False),
        wheel(40, 10, [-80, 20, 60], "#495057"), wheel(40, 10, [80, 20, 60], "#495057")],
        fill=0.3, colors=["#e63946", "#ffbe0b", "#2b9348"], sfx="snack", flavor="放學時賣雞蛋糕的攤車。"))
    A(item("sc_bus_shelter", "公車候車亭", "Bus Shelter", "街道", [400, 280, 160], [
        part("box", [420, 12, 170], [0, 274, 0], "#1d4e89"),
        part("box", [400, 230, 6], [0, 150, 75], "#caf0f8"),
        part("box", [10, 268, 10], [-195, 134, 70], "#adb5bd"),
        part("box", [10, 268, 10], [195, 134, 70], "#adb5bd"),
        part("box", [300, 8, 40], [0, 45, 50], "#b08968")],
        fill=0.12))
    A(item("sc_traffic_light", "紅綠燈", "Traffic Light", "街道", [40, 550, 300], [
        part("cylinder", [24, 550, 24], [0, 275, 0], "#495057"),
        part("box", [12, 12, 260], [0, 520, -130], "#495057"),
        part("box", [30, 90, 30], [0, 470, -250], "#212529"),
        part("sphere", [16, 16, 16], [0, 495, -266], "#e63946", collide=False),
        part("sphere", [16, 16, 16], [0, 445, -266], "#2b9348", collide=False)],
        fill=0.1))
    A(item("sc_street_lamp", "路燈", "Street Lamp", "街道", [40, 700, 160], [
        part("cylinder", [20, 700, 20], [0, 350, 0], "#adb5bd"),
        part("box", [12, 12, 140], [0, 690, -70], "#adb5bd"),
        part("box", [36, 14, 50], [0, 680, -140], "#fff3b0", collide=False)],
        fill=0.1))
    A(item("sc_big_rock", "景觀石", "Garden Rock", "校園", [260, 180, 200], shape="sphere", color="#8d99ae", fill=0.7,
         flavor="刻著校訓的大石頭。"))
    A(item("sc_pavilion", "涼亭", "Pavilion", "校園", [500, 420, 500], [
        part("cone", [560, 140, 560], [0, 350, 0], "#c1121f"),
        part("box", [24, 280, 24], [-220, 140, -220], "#9c6644"),
        part("box", [24, 280, 24], [220, 140, -220], "#9c6644"),
        part("box", [24, 280, 24], [-220, 140, 220], "#9c6644"),
        part("box", [24, 280, 24], [220, 140, 220], "#9c6644"),
        part("cylinder", [120, 70, 120], [0, 35, 0], "#adb5bd")],
        fill=0.12))
    A(item("sc_water_tower", "高架水塔", "Water Tower", "建築", [220, 550, 220], [
        part("cylinder", [220, 200, 220], [0, 450, 0], "#adb5bd"),
        part("box", [14, 350, 14], [-90, 175, -90], "#6c757d"),
        part("box", [14, 350, 14], [90, 175, -90], "#6c757d"),
        part("box", [14, 350, 14], [-90, 175, 90], "#6c757d"),
        part("box", [14, 350, 14], [90, 175, 90], "#6c757d")],
        fill=0.2))
    A(item("sc_house", "平房", "Single-story House", "建築", [900, 450, 800], [
        part("box", [900, 380, 800], [0, 190, 0], "#fefae0", tint=True),
        part("box", [940, 40, 840], [0, 400, 0], "#b56576"),
        part("cylinder", [140, 120, 140], [250, 480, 200], "#adb5bd", collide=False),
        part("box", [160, 230, 4], [0, 115, -402], "#9c6644", collide=False),
        part("box", [220, 130, 4], [-280, 200, -402], "#a2d2ff", collide=False)],
        fill=0.2, colors=["#fefae0", "#f1faee", "#ffe5d9", "#e9f5db"]))
    A(item("sc_shop", "街角商店", "Corner Shop", "建築", [800, 720, 1200], [
        part("box", [800, 700, 1200], [0, 350, 0], "#e9ecef", tint=True),
        part("box", [810, 90, 12], [0, 380, -606], "#2a9d8f", collide=False, tint=True),
        part("box", [600, 240, 4], [0, 130, -602], "#a2d2ff", collide=False)],
        fill=0.2, pickable=False, colors=["#e9ecef", "#fff1e6", "#e2ece9"]))
    return it


# ---------- 第 3 關場景 ----------

X0, X1 = -6000, 34000
Z0, Z1 = -12000, 16000
CAMPUS = (0, -8000, 20000, 14000)        # x, z, 寬, 深
ROAD_Z0, ROAD_Z1 = 6600, 8000            # 校門前大馬路
PADDY_Y = -18


def build_level():
    lv = Level("school", "小學與街區",
               "第 3 關：冬山鄉的小學與附近街區。校園有操場、司令台、遊戲場、籃球場、腳踏車棚與校車；"
               "校外南邊是大馬路與街區，東邊是稻田。單位公分。")
    lv.set_env(sky="#a9d6f5", fog_color="#dcecf5", fog_per_d=0.0035)
    cx, cz, cw, cd = CAMPUS

    lv.floor("底層", X0 - 3000, Z0 - 3000, (X1 - X0) + 6000, (Z1 - Z0) + 6000, y=-200, pattern="soil",
             color="#8d6e4f", repeat=300, thickness=20)

    # 校園地面：草地為底，跑道、操場、籃球場、遊戲場另外鋪
    lv.floor("校園草地", cx, cz, cw, cd, y=0, pattern="grass", color="#7cb342", repeat=300, thickness=200)
    lv.floor("跑道", 5000, -2000, 10000, 5500, y=1, pattern="soil", color="#c0533a", repeat=300, thickness=200)
    lv.floor("操場草皮", 6200, -900, 7600, 3300, y=2, pattern="grass", color="#5fa83c", repeat=300, thickness=200)
    lv.floor("籃球場", 16000, -2500, 3500, 7000, y=1, pattern="concrete", color="#7d9fbf", repeat=500,
             thickness=200)
    lv.floor("遊戲場沙地", 500, -2500, 4000, 5500, y=1, pattern="sand", color="#d9c08c", repeat=200, thickness=200)
    lv.floor("校門大道", 9000, 3500, 2000, 2500, y=1, pattern="paving", color="#c49a76", repeat=150,
             thickness=200)
    lv.floor("前庭", 3000, -6000, 14000, 2600, y=1, pattern="paving", color="#bfa58a", repeat=150, thickness=200)
    # 跑道白線（直線段）
    for k in range(4):
        lv.block("跑道線", 10000, 1, -1700 + k * 250, 10000, 1.5, 12, color="#f8f9fa")
        lv.block("跑道線", 10000, 1, 3200 - k * 250, 10000, 1.5, 12, color="#f8f9fa")

    # 教室大樓：北側主棟與東西兩翼（大型障礙物）
    for i, x in enumerate(range(3800, 17000, 1600)):
        lv.place("sc_classroom", x, 0, -7200, rot=0)
    lv.place("sc_classroom", 3800, 0, -5600, rot=0)
    lv.place("sc_classroom", 16600, 0, -5600, rot=0)

    # 司令台與升旗台：台子兩側都有樓梯
    lv.block("司令台", 10000, 0, -3300, 3000, 120, 1200, color="#e9d8c4")
    lv.block("司令台屋頂柱", 8650, 120, -3800, 60, 300, 60, color="#c1121f")
    lv.block("司令台屋頂柱", 11350, 120, -3800, 60, 300, 60, color="#c1121f")
    lv.stairs_up("司令台樓梯", (8800, 120, -2700), 180, width=500, slope_deg=28, style="lego")
    lv.stairs_up("司令台樓梯", (11200, 120, -2700), 180, width=500, slope_deg=28, style="lego")
    lv.stairs_up("司令台側樓梯", (8500, 120, -3300), 270, width=500, slope_deg=28, style="blocks",
                 colors=["#e9d8c4", "#d6c4ae"])
    lv.stairs_up("司令台側樓梯", (11500, 120, -3300), 90, width=500, slope_deg=28, style="blocks",
                 colors=["#e9d8c4", "#d6c4ae"])
    lv.decor("司令台屋頂", "box", (10000, 420, -3750), (3200, 30, 700), "#c1121f")
    lv.place("sc_podium", 10000, 120, -3500)
    lv.place("sc_speaker", 9200, 120, -3600)
    lv.place("sc_speaker", 10800, 120, -3600)
    lv.place("sc_school_drum", 9600, 120, -3200)
    for fx in (9400, 10000, 10600):
        lv.place("sc_flagpole", fx, 0, -2300)

    # 校園圍籬（矮樹籬，3 公尺的球過不去，長大一點就跨得過）：南面校門、東西側門留缺口
    hedge = "#4f772d"
    lv.wall((cx, cz + cd), (cx + cw, cz + cd), height=150, thickness=80, color=hedge,
            gaps=[(9000, 11000, 999), (2500, 3700, 999), (16300, 17500, 999)])
    lv.wall((cx, cz), (cx, cz + cd), height=150, thickness=80, color=hedge, gaps=[(9000, 10600, 999)])
    lv.wall((cx + cw, cz), (cx + cw, cz + cd), height=150, thickness=80, color=hedge, gaps=[(7000, 8600, 999)])
    lv.wall((cx, cz), (cx + cw, cz), height=150, thickness=80, color=hedge, gaps=[(1000, 2400, 999)])
    lv.place("st_school_gate", 10000, 0, cz + cd, rot=0)

    # 校外：南邊大馬路與人行道、街區
    lv.floor("北人行道", X0, cz + cd, X1 - X0, ROAD_Z0 - (cz + cd), y=15, pattern="paving", color="#b8a48c",
             repeat=150, thickness=200)
    lv.floor("大馬路", X0, ROAD_Z0, X1 - X0, ROAD_Z1 - ROAD_Z0, y=0, pattern="asphalt", color="#5a5f66",
             repeat=400, thickness=200)
    lv.floor("南人行道", X0, ROAD_Z1, X1 - X0, 600, y=15, pattern="paving", color="#b8a48c", repeat=150,
             thickness=200)
    lv.floor("南邊街區", X0, ROAD_Z1 + 600, 20600 - X0, Z1 - ROAD_Z1 - 600, y=0, pattern="concrete",
             color="#aaa496", repeat=400, thickness=200)
    x = X0 + 300
    while x < X1 - 600:
        lv.block("馬路中線", x + 200, 0, (ROAD_Z0 + ROAD_Z1) / 2, 400, 0.8, 16, color="#ffd166")
        x += 1000
    # 斑馬線（校門口）
    for k in range(7):
        lv.block("斑馬線", 9300 + k * 230, 0, (ROAD_Z0 + ROAD_Z1) / 2, 120, 0.8, ROAD_Z1 - ROAD_Z0 - 100,
                 color="#f8f9fa")

    # 西邊巷道與街區
    lv.floor("西巷", -2000, Z0, 1400, cz + cd - Z0, y=0, pattern="asphalt", color="#62676e", repeat=400,
             thickness=200)
    lv.floor("西邊住家", X0, Z0, -2000 - X0, cz + cd - Z0, y=0, pattern="concrete", color="#aaa496",
             repeat=400, thickness=200)
    lv.floor("校園西側", -600, Z0, 600, cz + cd - Z0, y=0, pattern="grass", color="#7cb342", repeat=300,
             thickness=200)
    lv.floor("校園北側", 0, Z0, 20600, cz - Z0, y=0, pattern="grass", color="#7cb342", repeat=300, thickness=200)

    # 東邊：農路與稻田
    lv.floor("東農路", 20000, Z0, 1000, cz + cd - Z0, y=0, pattern="concrete", color="#aba79c", repeat=400,
             thickness=200)
    lv.floor("東農路南段", 20000, ROAD_Z1 + 600, 600, Z1 - ROAD_Z1 - 600, y=0, pattern="concrete",
             color="#aba79c", repeat=400, thickness=200)
    lv.floor("東邊稻田", 21000, Z0, X1 - 21000, ROAD_Z0 - Z0, y=PADDY_Y, pattern="grass", color="#6aa63c",
             repeat=300, thickness=200)
    lv.floor("東南稻田", 20600, ROAD_Z1 + 600, X1 - 20600, Z1 - ROAD_Z1 - 600, y=PADDY_Y, pattern="paddy",
             color="#3f7f2a", repeat=300, thickness=200)
    for gx in range(24000, X1 - 500, 3000):
        lv.block("田埂", gx, PADDY_Y, (Z0 + ROAD_Z0) / 2, 60, 22, ROAD_Z0 - Z0, color="#7a9a4a")
    for gz in range(Z0 + 3000, ROAD_Z0 - 500, 3000):
        lv.block("田埂", (21000 + X1) / 2, PADDY_Y, gz, X1 - 21000, 22, 60, color="#7a9a4a")

    # 南邊街區的房子與商店（不可黏的街屋＋可黏的平房）
    shops = [(-3000, 10200, 180), (1000, 10200, 180), (5200, 10200, 180), (14200, 10200, 180),
             (18200, 10200, 180)]
    for sx, sz, rot in shops:
        lv.place("sc_shop", sx, 0, sz, rot=rot)
    houses = [(-4200, 14000), (-1000, 14200), (2400, 13800), (6000, 14100), (9400, 13900), (12800, 14200),
              (16400, 13800), (19000, 14000)]
    for i, (hx, hz) in enumerate(houses):
        lv.place("sc_house", hx, 0, hz, rot=180 if i % 2 == 0 else 0)
    for i, (hx, hz) in enumerate([(-4400, -9800), (-4300, -5600), (-4500, -1500), (-4200, 2600)]):
        lv.place("sc_house", hx, 0, hz, rot=90)

    # 行道樹與路燈、紅綠燈、候車亭
    for tx in range(X0 + 800, X1 - 400, 3600):
        lv.place("sc_street_tree", tx, 15, cz + cd + 300)
        lv.place("sc_street_lamp", tx + 1200, 15, ROAD_Z1 + 300, rot=0)
    lv.place("sc_traffic_light", 8800, 15, cz + cd + 450, rot=180)
    lv.place("sc_traffic_light", 11200, 15, ROAD_Z1 + 300, rot=0)
    lv.place("sc_bus_shelter", 13500, 15, ROAD_Z1 + 300, rot=180)
    lv.place("sc_bus_shelter", 4500, 15, cz + cd + 350, rot=0)

    # 校園裡的固定設施
    for px in (8400, 11600):
        for pz in range(3900, 5900, 700):
            lv.place("sc_palm", px, 0, pz)
    lv.place("sc_bike_shed", 5500, 0, 5000, rot=0)
    lv.place("sc_bike_shed", 14500, 0, 5000, rot=0)
    for bx in (16600, 17300, 18000):
        lv.place("sc_school_bus", bx, 0, 5300, rot=0)
    lv.place("sc_pavilion", 2500, 0, 4300)
    lv.place("sc_big_rock", 7500, 0, 5300)
    lv.place("sc_water_tower", 19200, 0, -7300)
    for (tx, tz) in [(1200, -7000), (18800, -4500), (1500, 5200), (19000, 5300), (600, -4400)]:
        lv.place("sc_camphor", tx, 0, tz)
    # 遊戲場
    lv.place("sc_slide", 1500, 1, -1500, rot=90)
    lv.place("sc_slide", 3500, 1, 1800, rot=270)
    lv.place("sc_swing", 1400, 1, 1500, rot=0)
    lv.place("sc_swing", 3400, 1, -1800, rot=0)
    lv.place("sc_jungle_gym", 2500, 1, 0)
    lv.place("sc_seesaw", 1000, 1, 400, rot=0)
    lv.place("sc_seesaw", 4000, 1, 400, rot=0)
    # 籃球場
    for bz in (-2200, 1300):
        lv.place("sc_basketball_hoop", 17750, 1, bz, rot=0)
        lv.place("sc_basketball_hoop", 17750, 1, bz + 2900, rot=180)
    lv.place("sc_soccer_goal", 6600, 2, 750, rot=90)
    lv.place("sc_soccer_goal", 13400, 2, 750, rot=270)

    # ---------- 散布 ----------
    # 起點（校門內大道兩側）要很密
    lv.spawn("校門大道", (6800, 3600, 6400, 2200), 1, {
        "st_bike": 10, "st_scooter": 6, "st_kick_scooter": 6, "sc_bench": 6, "sc_flower_bed": 6,
        "sc_spring_rider": 4, "st_potted_plant": 8, "st_trash_bin": 4, "st_traffic_cone": 6, "sc_ball_cart": 3,
        "st_oil_drum": 4, "st_stool": 6, "st_plastic_chair": 6, "sc_hurdle": 4,
    }, avoid_furniture=True)
    lv.spawn("遊戲場", (600, -2400, 3800, 5300), 1, {
        "sc_spring_rider": 8, "st_kick_scooter": 4, "sc_bench": 4, "st_bucket": 6, "sc_ball_cart": 2,
        "st_small_tree": 2, "sc_hay_bale": 2,
    }, avoid_furniture=True)
    lv.spawn("跑道", (5100, -1900, 9800, 900), 1, {
        "sc_hurdle": 10, "sc_ball_cart": 3, "st_traffic_cone": 8, "sc_bench": 3,
    })
    lv.spawn("操場", (6300, -800, 7400, 3100), 2, {
        "sc_hurdle": 4, "sc_ball_cart": 3, "st_traffic_cone": 6, "sc_school_drum": 2, "sc_speaker": 2,
        "sc_hay_bale": 2,
    }, avoid_furniture=True)
    lv.spawn("籃球場", (16100, -2400, 3300, 6800), 1, {
        "sc_ball_cart": 4, "sc_bench": 4, "st_bike": 4, "st_scooter": 2,
    }, avoid_furniture=True)
    lv.spawn("前庭", (3100, -5900, 13800, 2300), 1, {
        "sc_flower_bed": 8, "sc_bench": 6, "st_bike": 6, "st_potted_plant": 6, "st_vending": 3,
        "st_small_tree": 4, "sc_speaker": 2, "sc_big_rock": 2,
    }, avoid_furniture=True)
    lv.spawn("校園草地", (cx + 300, -1800, 4400, 7500), 0, {
        "st_small_tree": 3, "sc_flower_bed": 2,
    }, avoid_furniture=True)
    lv.spawn("校園東側", (15200, -5500, 4500, 10500), 0, {
        "st_bike": 4, "sc_tractor": 1, "sc_container": 1, "sc_shed": 2, "st_small_tree": 4, "sc_flower_bed": 2,
    }, avoid_furniture=True)
    lv.spawn("北人行道", (X0 + 200, cz + cd + 50, X1 - X0 - 400, ROAD_Z0 - (cz + cd) - 100), 15, {
        "st_scooter": 12, "st_bike": 8, "st_trash_bin": 6, "st_vending": 3, "st_potted_plant": 6,
        "st_mailbox_pair": 2,
    })
    lv.spawn("大馬路", (X0 + 200, ROAD_Z0 + 100, X1 - X0 - 400, ROAD_Z1 - ROAD_Z0 - 200), 0, {
        "st_car_red": 3, "st_car_blue": 3, "st_car": 2, "sc_pickup": 3, "sc_truck": 2, "st_scooter": 8,
    })
    lv.spawn("南人行道", (X0 + 200, ROAD_Z1 + 50, X1 - X0 - 400, 500), 15, {
        "st_scooter": 12, "st_bike": 6, "sc_stall": 4, "st_fruit_stall": 3, "st_trash_bin": 4,
        "st_signboard": 4, "st_plastic_chair": 6,
    })
    lv.spawn("南邊街區", (X0 + 200, ROAD_Z1 + 700, 20600 - X0 - 400, Z1 - ROAD_Z1 - 900), 0, {
        "st_car_red": 2, "st_car_blue": 2, "st_car": 1, "sc_pickup": 2, "st_scooter": 10, "sc_stall": 2,
        "sc_street_tree": 3, "sc_container": 1, "sc_shed": 2, "sc_water_tower": 1, "st_small_tree": 6,
        "sc_bench": 4, "st_electric_pole": 6,
    }, avoid_furniture=True)
    lv.spawn("西邊住家", (X0 + 200, Z0 + 300, -2000 - X0 - 400, cz + cd - Z0 - 600), 0, {
        "st_car_red": 1, "st_car": 1, "st_scooter": 6, "sc_pickup": 1, "st_water_jar": 4, "sc_shed": 1,
        "st_small_tree": 4, "sc_street_tree": 3, "sc_water_tower": 1,
    }, avoid_furniture=True)
    lv.spawn("西巷", (-1900, Z0 + 300, 1200, cz + cd - Z0 - 600), 0, {
        "st_scooter": 6, "st_bike": 4, "st_electric_pole": 6, "sc_pickup": 1,
    })
    lv.spawn("校園北側", (300, Z0 + 300, 20000, cz - Z0 - 600), 0, {
        "sc_camphor": 1, "sc_street_tree": 3, "sc_shed": 1, "sc_container": 1, "st_small_tree": 6,
        "sc_hay_bale": 4, "sc_tractor": 1,
    }, avoid_furniture=True)
    lv.spawn("東農路", (20100, Z0 + 300, 800, cz + cd - Z0 - 600), 0, {
        "sc_tractor": 2, "sc_pickup": 2, "st_scooter": 4, "st_electric_pole": 8, "sc_hay_bale": 4,
    })
    lv.spawn("東邊稻田", (21300, Z0 + 300, X1 - 21600, ROAD_Z0 - Z0 - 600), PADDY_Y, {
        "sc_hay_bale": 16, "st_scarecrow": 8, "st_water_buffalo": 6, "sc_tractor": 3, "sc_shed": 2,
        "sc_water_tower": 2, "st_pomelo_tree": 3, "sc_street_tree": 3, "sc_container": 1,
    })
    lv.spawn("東南稻田", (20900, ROAD_Z1 + 900, X1 - 21200, Z1 - ROAD_Z1 - 1200), PADDY_Y, {
        "sc_hay_bale": 6, "st_scarecrow": 4, "st_water_buffalo": 3, "sc_tractor": 1, "st_pomelo_tree": 1,
    })

    # 動物
    critters = [
        ("st_dog_local", 2500, 2500, (500, -2500, 4000, 5500)),
        ("st_dog_local", -1000, 4000, (-1900, -7000, 1200, 13000)),
        ("st_dog_local", 15000, 12000, (12000, 8800, 8000, 6600)),
        ("st_cat_local", 9000, 12500, (6000, 8800, 6000, 6600)),
        ("st_cat_local", -4000, 0, (-5800, -11000, 3700, 16500)),
        ("st_egret", 26000, -6000, (21500, -11500, 12000, 17500)),
        ("st_egret", 30000, 0, (21500, -11500, 12000, 17500)),
        ("st_egret", 28000, 12000, (21000, 9000, 12500, 6500)),
        ("st_chicken", -3500, -3000, (-5800, -11000, 3700, 16500)),
        ("st_duck", 27000, 13000, (21000, 9000, 12500, 6500)),
        ("st_duck", 28000, 12500, (21000, 9000, 12500, 6500)),
    ]
    for cid, x0, z0, roam in critters:
        y = PADDY_Y if (x0 > 20500 and cid in ("st_egret", "st_duck")) else 0
        lv.place(cid, x0, y, z0, roam=roam, blocks_spawn=False)

    # 邊界與遠山
    for a, b in [((X0, Z0), (X1, Z0)), ((X0, Z1), (X1, Z1)), ((X0, Z0), (X0, Z1)), ((X1, Z0), (X1, Z1))]:
        lv.wall(a, b, height=1200, thickness=400, color="#4f772d", y=-30)
    for i, (mx, mz, w, h, c) in enumerate([
        (0, -60000, 50000, 16000, "#4f7d5c"), (40000, -52000, 36000, 12000, "#5f8f6a"),
        (-40000, -30000, 40000, 14000, "#5a8865"), (-45000, 20000, 36000, 11000, "#62906b"),
    ]):
        lv.decor(f"遠山{i + 1}", "cone", (mx, -200, mz), (w, h, w * 0.6), c, no_shadow=True)

    # 區域
    lv.area("遊戲場", 500, -2500, 4000, 5500)
    lv.area("操場", 5000, -2000, 10000, 5500)
    lv.area("司令台", 8500, -3900, 3000, 1200)
    lv.area("籃球場", 16000, -2500, 3500, 7000)
    lv.area("校門口", 6500, 3500, 7000, 2500)
    lv.area("教室前", 3000, -8000, 14000, 4600)
    lv.area("小學", cx, cz, cw, cd)
    lv.area("大馬路", X0, cz + cd, X1 - X0, ROAD_Z1 + 600 - (cz + cd))
    lv.area("街區", X0, ROAD_Z1 + 600, 20600 - X0, Z1 - ROAD_Z1)
    lv.area("西邊巷子", X0, Z0, -600 - X0, cz + cd - Z0)
    lv.area("稻田", 20000, Z0, X1 - 20000, Z1 - Z0)
    lv.area("學校後面", 0, Z0, 20600, cz - Z0)

    start = (10000, 2, 4700)
    lv.set_start(start, 0)
    lv.set_rescue((10000, 3, 1000), 0)
    lv.set_stage(
        start_cm=300, goal_cm=1000, time_sec=540, comet_sec=270, seed=2301, music="school",
        intro="到學校了！操場、遊戲場、校車都在等你，目標 10 公尺",
        zones=[], gates={}, tuning={},
        start={"pos": list(start), "yaw_deg": 0},
        grades=[
            {"min_ratio": 0.0, "text": "星婆婆：學校好大，下課再來滾一次！"},
            {"min_ratio": 1.0, "text": "星婆婆：整個學校都滾過一圈了，好棒！"},
            {"min_ratio": 1.3, "text": "星婆婆：連校車都黏起來了？明天大家要走路上學了！"},
            {"min_ratio": 1.6, "text": "星婆婆：大王椰子跟老樟樹都在上面，好壯觀！"},
            {"min_ratio": 1.9, "text": "星婆婆：太厲害了！整個街區都變成星星啦！"},
        ],
    )
    return lv


def main():
    items = school_items()
    save_items("school.json", "第 3 關「小學與街區」的物件。id 前綴 sc_；也沿用第 2 關的 st_ 物件。", items)
    lv = build_level()
    lv.save()
    base = json.loads((ROOT / "godot" / "data" / "items.json").read_text(encoding="utf-8"))["items"]
    budget(lv, items + street_items() + base, 300, 1000,
           [(0, 100), (100, 210), (210, 350), (350, 500), (500, 700), (700, 99999)])


if __name__ == "__main__":
    main()
