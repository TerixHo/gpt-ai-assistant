"""第 1 關「槿寶的家」：宜蘭冬山鄉的單層平房，6 公分滾到 1 公尺。

執行（在 rolling-home 資料夾）：
    python3 tools/levels/build_dongshan_home.py
會同時產生：
    godot/data/items/home.json          本關專用物件（定義在 home_items.py）
    godot/data/levels/dongshan_home.json 場景配置

座標：x 往東、z 往南、y 往上，單位公分。房子在 x 0..1500、z 0..1100，南邊是門口、前院與圍牆。
    北排（z 0..450）：哥哥的房間、姐姐的房間、妹妹的房間、廁所、浴室
    走廊（z 450..600）：東西向貫穿整棟
    南排（z 600..1100）：書房、客廳、廚房與餐廳
    門口（z 1100..1250）：前廊，地面和室內一樣高
    前院（z 1250..1800，比室內低 12 公分）：西半邊停車、山櫻花樹；東半邊是小花園
設計說明見 docs/06_第1關_槿寶的家.md。
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from levelkit import Level, direction  # noqa: E402
import home_items  # noqa: E402

lv = Level("dongshan_home", "槿寶的家（宜蘭冬山）",
           "原創場景：宜蘭冬山鄉的單層平房與前院。由 tools/levels/build_dongshan_home.py 產生，請改腳本後重新執行，"
           "不要直接改這個檔案。單位公分；x 往東、z 往南（南邊是門口與前院）。")

# 樓梯佔地（x, z, 寬, 深），地面散布物件時要避開
STAIR_RECTS = []


def stairs(name, top, facing, width, slope=30.0, base_y=0.0, step=3.0, style="lego", colors=None):
    bottom = lv.stairs_up(name, top, facing, width=width, slope_deg=slope, base_y=base_y, step=step,
                          style=style, colors=colors)
    dx, dz = direction(facing)
    px, pz = -dz, dx
    xs, zs = [], []
    for (x, z) in ((top[0], top[2]), (bottom[0], bottom[2])):
        for s in (-1, 1):
            xs.append(x + px * width * 0.5 * s)
            zs.append(z + pz * width * 0.5 * s)
    m = 3.0
    STAIR_RECTS.append((round(min(xs) - m, 1), round(min(zs) - m, 1),
                        round(max(xs) - min(xs) + 2 * m, 1), round(max(zs) - min(zs) + 2 * m, 1)))
    return bottom


def overlaps(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def floor_spawn(zone, rect, y, items, extra_exclude=()):
    """地面散布：自動避開樓梯與指定範圍（家具由 avoid_furniture 自動避開）。"""
    ex = [r for r in STAIR_RECTS if overlaps(r, rect)] + list(extra_exclude)
    lv.spawn(zone, rect, y, items, avoid_furniture=True, exclude=ex or None)


def top_spawn(zone, rect, y, items, exclude=()):
    """家具頂面散布：不避開家具（頂面本身就是家具）。"""
    lv.spawn(zone, rect, y, items, avoid_furniture=False, exclude=list(exclude) or None)


EXT = "#dcc8a6"      # 外牆
INT = "#e6d9c0"      # 內牆
DOOR = "#d6b38a"     # 木門
BRICK = "#b5523b"

# ---------------------------------------------------------------- 地面
lv.floor("田野", -5000, -4000, 11500, 9500, y=-14, pattern="paddy", color="#86c45a", repeat=140, thickness=4)
lv.floor("鄉間小路", -5000, 1815, 11500, 700, y=-13, pattern="asphalt", color="#5c5f66", repeat=300, thickness=3)
lv.floor("走廊", 0, 450, 1500, 150, pattern="tile", color="#eee6d8", repeat=80, thickness=14)
lv.floor("客廳", 400, 600, 550, 500, pattern="tile", color="#f0e9dc", repeat=80, thickness=14)
lv.floor("書房", 0, 600, 400, 500, pattern="wood", color="#d9b98c", repeat=90, thickness=14)
lv.floor("廚房", 950, 600, 550, 500, pattern="tile", color="#efe9df", repeat=40, thickness=14)
lv.floor("哥哥的房間", 0, 0, 380, 450, pattern="wood", color="#cfa77a", repeat=90, thickness=14)
lv.floor("姐姐的房間", 380, 0, 380, 450, pattern="wood", color="#e0c097", repeat=90, thickness=14)
lv.floor("妹妹的房間", 760, 0, 340, 450, pattern="wood", color="#e8cfa9", repeat=90, thickness=14)
lv.floor("廁所", 1100, 0, 180, 450, pattern="mosaic", color="#8ecfc9", repeat=40, thickness=14)
lv.floor("浴室", 1280, 0, 220, 450, pattern="mosaic", color="#7fb7e0", repeat=40, thickness=14)
lv.floor("門口", 0, 1100, 1500, 150, pattern="terrazzo", color="#cfc3b1", repeat=50, thickness=12)
lv.floor("前院", 0, 1250, 950, 550, y=-12, pattern="concrete", color="#a9aba3", repeat=200, thickness=4)
lv.floor("小花園", 950, 1250, 550, 550, y=-12, pattern="grass", color="#7cb867", repeat=120, thickness=4)

for name, x, z, w, d in (("哥哥的房間", 0, 0, 380, 450), ("姐姐的房間", 380, 0, 380, 450),
                         ("妹妹的房間", 760, 0, 340, 450), ("廁所", 1100, 0, 180, 450), ("浴室", 1280, 0, 220, 450),
                         ("走廊", 0, 450, 1500, 150), ("書房", 0, 600, 400, 500), ("客廳", 400, 600, 550, 500),
                         ("廚房和餐廳", 950, 600, 550, 500), ("門口", 0, 1100, 1500, 150),
                         ("前院", 0, 1250, 950, 560), ("小花園", 950, 1250, 550, 560)):
    lv.area(name, x, z, w, d)

# ---------------------------------------------------------------- 牆
# 外牆
lv.wall((0, 0), (1500, 0), thickness=14, color=EXT)
lv.wall((0, 0), (0, 1100), thickness=14, color=EXT)
lv.wall((1500, 0), (1500, 1100), thickness=14, color=EXT)
lv.wall((0, 1100), (1500, 1100), thickness=14, color=EXT, gaps=[(470, 670, 215), (1300, 1420, 205)])
# 北排房間與走廊之間（門：哥哥、姐姐、妹妹、廁所、浴室）
lv.wall((0, 450), (1500, 450), color=INT,
        gaps=[(120, 270), (500, 650), (870, 1020), (1110, 1270), (1310, 1470)])
for x in (380, 760, 1100, 1280):
    lv.wall((x, 0), (x, 450), color=INT)
# 走廊與南排之間（門：書房、客廳）
lv.wall((0, 600), (1500, 600), color=INT, gaps=[(140, 260), (470, 670)])
# 書房｜客廳（門），客廳｜廚房（大開口）
lv.wall((400, 600), (400, 1100), color=INT, gaps=[(40, 160)])
lv.wall((950, 600), (950, 1100), color=INT, gaps=[(50, 270, 215)])

# 圍牆（紅磚，比前院地面高 150）與鐵門
lv.block("西側圍牆", 0, -12, 1450, 14, 162, 700, color=BRICK, pattern="brick", repeat=60)
lv.block("東側圍牆", 1500, -12, 1450, 14, 162, 700, color=BRICK, pattern="brick", repeat=60)
lv.block("南側圍牆西段", 61.5, -12, 1800, 137, 162, 14, color=BRICK, pattern="brick", repeat=60)
lv.block("南側圍牆東段", 1018.5, -12, 1800, 977, 162, 14, color=BRICK, pattern="brick", repeat=60)
lv.block("門柱西", 130, -12, 1800, 26, 182, 26, color="#c9b8a6")
lv.block("門柱東", 530, -12, 1800, 26, 182, 26, color="#c9b8a6")
lv.block("鐵門", 330, -12, 1800, 374, 150, 6, color="#3d405b")
for i in range(9):
    lv.block(f"鐵門欄杆{i}", 170 + i * 40, -12, 1800, 4, 150, 9, color="#2b2d42")

# ---------------------------------------------------------------- 門（尺寸門檻）
lv.gate("kitchen_door", "廚房的拉門", (950, 0, 760), (6, 205, 220), 10,
        "廚房的門打開了！聞到咖哩的香味了嗎？", color=DOOR, slide=(0, 0, 220))
lv.gate("study_door", "書房的門", (400, 0, 700), (6, 205, 120), 12,
        "書房的門打開了！書桌上有人在畫畫喔", color=DOOR, slide=(0, 0, 120))
lv.gate("hall_door", "客廳到走廊的拉門", (520, 0, 600), (100, 205, 6), 14,
        "走廊的門打開了！去哥哥姐姐的房間看看", color=DOOR, slide=(-100, 0, 0))
lv.gate("hall_door_b", "客廳到走廊的拉門", (620, 0, 600), (100, 205, 6), 14, "", color=DOOR, slide=(100, 0, 0))
lv.gate("study_hall_door", "書房到走廊的門", (200, 0, 600), (120, 205, 6), 14, "", color=DOOR, slide=(-120, 0, 0))
lv.gate("toilet_door", "廁所的門", (1190, 0, 450), (160, 205, 6), 14, "", color="#cde7e5", slide=(0, -212, 0))
lv.gate("sister_door", "姐姐的房門", (575, 0, 450), (150, 205, 6), 16,
        "姐姐的房門打開了！桌上有好多串珠", color="#ffc8dd", slide=(150, 0, 0))
lv.gate("brother_door", "哥哥的房門", (195, 0, 450), (150, 205, 6), 18,
        "哥哥的房門打開了！小心籃球！", color="#a0c4ff", slide=(150, 0, 0))
lv.gate("ysister_door", "妹妹的房門", (945, 0, 450), (150, 205, 6), 20,
        "妹妹的房門打開了！到處都是玩具", color="#fdffb6", slide=(-150, 0, 0))
lv.gate("bath_door", "浴室的門", (1390, 0, 450), (160, 205, 6), 22,
        "浴室的門打開了！浴缸裡有小黃鴨", color="#bfdcf5", slide=(0, -212, 0))
lv.gate("front_door", "大門", (570, 0, 1100), (200, 215, 6), 35,
        "大門打開了！去前院看看車子和櫻花樹", color="#adb5bd", slide=(-200, 0, 0))
lv.gate("back_door", "廚房後門", (1360, 0, 1100), (120, 205, 6), 40,
        "廚房後門也打開了！", color=DOOR, slide=(-120, 0, 0))

# ---------------------------------------------------------------- 客廳：吃零食
lv.place("hm_tv_cabinet", 427.5, 0, 940, rot=-90)
lv.place("hm_tv", 414, 50, 940, rot=-90)
stairs("電視櫃樓梯", (428, 50, 849), 0, 26)
lv.place("hm_sofa", 902.5, 0, 980, rot=90)
stairs("沙發樓梯", (861, 45, 975), 270, 30)
lv.place("hm_coffee_table", 730, 0, 965, rot=90)
stairs("茶几樓梯", (730, 40, 909), 0, 28, style="books")
lv.block("客廳地毯", 770, 0, 959, 180, 0.6, 258, color="#cdb4db", pattern="carpet", repeat=120)
lv.place("house_plant", 440, 0, 1062)
lv.place("hm_fan", 430, 0, 815, rot=-90)
lv.place("hm_floor_cushion", 820, 0.6, 1060, color="#f4a261")
lv.place("cat", 700, 0, 760, rot=45, roam=(410, 610, 530, 480))
RUG = (678, 828, 184, 262)
floor_spawn("lr_rug", (685, 835, 170, 248), 0.6, {
    "hm_chip": 14, "hm_popcorn": 12, "hm_gummy": 8, "hm_milk_candy": 6, "konpeito": 5, "candy": 5,
    "hm_pineapple_cake": 4, "hm_rice_cracker": 3, "hm_egg_roll": 3, "hm_seaweed": 3, "hm_lollipop": 2,
    "hm_lactic_drink": 2, "cookie": 3, "hm_coin_1": 3, "hm_coin_10": 2, "lego_2x2": 3, "marble": 3,
    "hm_puzzle": 3, "hm_tea_cup": 1, "hm_guava": 1, "juice_box": 1, "hm_game_pad": 1, "remote": 1, "hm_comic": 1})
top_spawn("lr_table", (703, 913, 54, 104), 40, {
    "hm_chips_bag": 1, "hm_fruit_plate": 1, "hm_teapot": 1, "hm_tea_cup": 3, "hm_chip": 6, "hm_popcorn": 6,
    "hm_guava": 2, "hm_lactic_drink": 2})
top_spawn("lr_sofa", (866, 896, 56, 168), 45, {
    "cushion": 1, "hm_comic": 2, "hm_chip": 5, "remote": 1, "plush_small": 1})
top_spawn("lr_tv", (421, 858, 27, 166), 50, {
    "hm_photo_frame": 2, "mini_figure": 3, "animal_figure": 2, "keychain": 2})
# 起點旁邊打翻的一包零食：一開始就有東西可以黏
floor_spawn("lr_spill", (500, 690, 180, 220), 0, {
    "hm_chip": 24, "hm_pineapple_cake": 6, "hm_egg_roll": 4, "hm_puzzle": 6, "hm_coin_10": 4, "hm_coin_5": 3,
    "candy": 8, "hm_rice_cracker": 3}, extra_exclude=[RUG])
floor_spawn("lr_floor", (410, 610, 530, 478), 0, {
    "hm_chip": 22, "hm_popcorn": 18, "candy": 10, "hm_gummy": 10, "hm_milk_candy": 5, "konpeito": 6,
    "hm_pineapple_cake": 4, "hm_rice_cracker": 4, "hm_egg_roll": 3, "hm_seaweed": 3, "hm_coin_5": 4,
    "hm_coin_50": 2, "hm_coin_1": 3, "lego_2x4": 6, "lego_2x2": 3, "hm_puzzle": 8, "marble": 3, "minicar": 3,
    "bouncy_ball": 4, "hm_juice_bottle": 2, "hm_chips_bag": 3, "hm_popcorn_bucket": 3, "tissue_box": 1,
    "hm_comic": 4, "hm_slipper": 2, "hm_cat_food_can": 2, "yarn_ball": 2, "cat_teaser": 1, "hm_photo_frame": 1,
    "hm_lollipop": 2, "hm_lactic_drink": 2, "cookie": 3, "juice_box": 1, "hm_tea_cup": 1, "hm_guava": 1},
    extra_exclude=[RUG])

# ---------------------------------------------------------------- 書房：畫蠟筆、玩玩具、小毛線
lv.place("hm_desk_study", 37, 0, 930, rot=-90)
stairs("書桌樓梯", (68, 75, 930), 90, 32)
lv.place("desk_lamp", 25, 75, 885)
lv.place("hm_bookshelf", 300, 0, 1078)
lv.place("toy_box", 377, 0, 840, rot=90)
lv.place("hm_knit_basket", 23, 0, 1040)
lv.place("hm_globe", 250, 0, 780)
top_spawn("st_desk", (9, 872, 56, 116), 75, {
    "crayon": 8, "hm_crayon_big": 4, "hm_crayon_box": 1, "hm_drawing_paper": 2, "hm_yarn_small": 5,
    "colored_pencil": 4, "eraser": 2, "sharpener": 1, "minicar": 1, "dinosaur": 1, "hm_puzzle": 2},
    exclude=[(13, 873, 24, 24)])
floor_spawn("st_floor", (10, 612, 382, 478), 0, {
    "crayon": 10, "hm_crayon_big": 6, "hm_drawing_paper": 4, "hm_yarn_small": 6, "hm_yarn_ball": 3,
    "hm_wood_block": 10, "hm_wood_arch": 4, "hm_puzzle": 6, "lego_2x4": 6, "toy_train": 1, "toy_robot": 1,
    "spinning_top": 2, "picture_book": 3, "hm_zhuyin_book": 2, "colored_pencil": 6, "marker": 4,
    "hm_crayon_box": 1, "glue_stick": 2, "kids_scissors": 1, "tape_roll": 2, "rubiks_cube": 1, "yoyo": 1})

# ---------------------------------------------------------------- 廚房與餐廳：正在煮咖哩
lv.place("hm_counter", 1150, 0, 636, rot=180)
lv.place("hm_curry_pot", 1040, 85, 636)
lv.place("hm_electric_pot", 1105, 85, 634)
lv.place("hm_cutting_board", 1165, 85, 640)
stairs("流理台樓梯", (1150, 85, 668), 180, 36, slope=32)
lv.place("hm_fridge", 1350, 0, 640, rot=180)
lv.place("hm_cupboard", 1470.5, 0, 760, rot=90)
lv.place("hm_dining_table", 1250, 0, 960)
stairs("餐桌樓梯", (1174, 75, 960), 270, 32)
# 餐椅靠牆放，不圍住餐桌（球在桌子底下長大時才不會被困住）
for x, z, r in ((1470, 960, 90), (1470, 1030, 90), (1060, 1065, 0)):
    lv.place("dining_chair", x, 0, z, rot=r)
lv.place("hm_orange_basket", 1290, 75, 940)
lv.place("trash_can", 969, 0, 1079)
lv.place("hm_rice_bag", 1485, 0, 880, rot=90)
top_spawn("kt_counter", (1002, 608, 296, 57), 85, {
    "hm_carrot": 3, "hm_carrot_cube": 8, "hm_potato": 3, "hm_potato_cube": 8, "hm_onion": 3,
    "hm_curry_roux": 6, "hm_ladle": 1, "hm_spoon": 3, "hm_chopsticks": 2, "hm_spice_jar": 3, "hm_orange": 3,
    "hm_bowl": 2, "hm_dish_soap": 1, "hm_scrub": 1},
    exclude=[(1022, 620, 36, 32), (1087, 617, 36, 34), (1145, 625, 40, 30), (1212, 610, 56, 46)])
top_spawn("kt_board", (1151, 630, 28, 20), 87, {"hm_carrot_cube": 4, "hm_potato_cube": 3})
top_spawn("kt_table", (1177, 917, 146, 86), 75, {
    "hm_curry_rice": 3, "hm_plate": 2, "hm_bowl": 2, "hm_spoon": 3, "hm_chopsticks": 3, "hm_tea_cup": 2,
    "hm_orange": 3, "hm_juice_bottle": 1}, exclude=[(1272, 925, 36, 30)])
floor_spawn("kt_floor", (957, 607, 534, 484), 0, {
    "hm_orange": 14, "hm_carrot": 4, "hm_potato": 5, "hm_onion": 4, "hm_carrot_cube": 4, "hm_potato_cube": 4,
    "hm_curry_roux": 4, "hm_spoon": 3, "hm_chopsticks": 3, "hm_bowl": 2, "hm_plate": 2,
    "hm_slipper": 2, "hm_apron": 1, "hm_kettle": 1, "hm_dish_soap": 1, "hm_scrub": 2, "hm_spice_jar": 2,
    "hm_coin_1": 3, "hm_guava": 3, "cherry_tomato": 6, "hm_cat_food_can": 1, "milk_carton": 1})

# ---------------------------------------------------------------- 走廊
lv.place("small_pot", 1475, 0, 525)
floor_spawn("hall", (12, 460, 1476, 130), 0, {
    "hm_schoolbag": 3, "school_hat": 2, "hm_water_bottle": 3, "hm_bento": 2, "hm_slipper": 4, "hm_umbrella": 2,
    "hm_sneaker": 2, "hm_comic": 2, "hm_zhuyin_book": 2, "picture_book": 2, "hm_coin_10": 4, "marble": 3,
    "bouncy_ball": 3, "hm_yarn_ball": 1, "hm_baseball": 2, "hm_sock": 3, "hm_rain_boots": 1})

# ---------------------------------------------------------------- 哥哥的房間
lv.place("hm_bed", 57, 0, 112, color="#a0c4ff")
stairs("哥哥床樓梯", (108, 45, 160), 90, 40)
lv.place("hm_desk_kid", 262, 0, 34.5, rot=180, color="#a0c4ff")
stairs("哥哥書桌樓梯", (262, 72, 63), 180, 40)
lv.place("hm_wardrobe", 345, 0, 300, rot=90)
lv.place("chair_boy", 190, 0, 300, rot=180)
top_spawn("br_bed", (12, 52, 90, 156), 45, {
    "hm_comic": 3, "hm_game_pad": 1, "plush_bear": 1, "hm_baseball": 1, "lego_2x4": 4})
top_spawn("br_desk", (214, 9, 96, 51), 72, {
    "pencil": 3, "eraser": 2, "hm_calculator": 1, "hm_comic": 2, "minicar": 2, "hm_xiangqi": 6, "ruler": 1,
    "notebook": 1})
floor_spawn("br_floor", (10, 10, 362, 432), 0, {
    "hm_basketball": 1, "soccer_ball": 1, "hm_baseball": 2, "hm_baseball_glove": 1, "hm_bat": 1,
    "hm_model_plane": 1, "rc_car": 1, "toy_robot": 1, "dinosaur": 3, "minicar": 3, "lego_2x4": 6,
    "lego_2x2": 6, "hm_xiangqi": 6, "hm_comic": 4, "hm_sneaker": 2, "hm_schoolbag": 1, "hm_water_bottle": 1,
    "spinning_top": 2, "die": 3, "trading_card": 4, "hm_sock": 2, "toy_dino_big": 1})

# ---------------------------------------------------------------- 姐姐的房間
lv.place("hm_bed", 705, 0, 112, color="#ffc6ff")
stairs("姐姐床樓梯", (654, 45, 160), 270, 40)
lv.place("hm_desk_kid", 470, 0, 34.5, rot=180, color="#ffafcc")
stairs("姐姐書桌樓梯", (470, 72, 63), 180, 40, style="books")
lv.place("bead_case", 440, 72, 28)
lv.place("hm_bookshelf", 400, 0, 330, rot=-90)
lv.place("chair_girl", 545, 0, 100, rot=180)
lv.block("姐姐的地毯", 555, 0, 330, 170, 0.6, 180, color="#ffc8dd", pattern="carpet", repeat=120)
SIS_RUG = (468, 238, 174, 184)
top_spawn("si_bed", (660, 52, 90, 156), 45, {
    "plush_bear": 1, "teddy_small": 2, "hm_diary": 1, "hm_scrunchie": 3, "hm_bracelet": 2})
top_spawn("si_desk", (422, 9, 96, 51), 72, {
    "bead_6": 6, "bead_8": 5, "fuse_bead": 5, "hm_bracelet": 3, "hair_clip": 4, "hair_tie": 4,
    "star_sticker": 4, "puffy_sticker": 4, "hm_diary": 1, "hm_hand_mirror": 1, "hm_perler_art": 1},
    exclude=[(430, 20, 22, 16)])
top_spawn("si_rug", (472, 242, 166, 176), 0.6, {
    "hm_scrunchie": 4, "hm_bracelet": 4, "fuse_bead": 8, "hm_perler_art": 3, "sticker_book": 1,
    "hm_hand_mirror": 1, "teddy_small": 1, "plush_small": 1, "doll": 1})
floor_spawn("si_floor", (390, 10, 362, 432), 0, {
    "hm_ukulele": 1, "keyboard_harmonica": 1, "recorder": 1, "picture_book": 3, "hm_diary": 1, "jump_rope": 1,
    "plush_small": 1, "doll": 2, "hm_schoolbag": 1, "hm_water_bottle": 1, "colored_pencil_box": 1,
    "pencil_case": 1, "hm_scrunchie": 3, "hair_tie": 4, "hm_sock": 2, "hm_slipper": 2, "hm_coin_5": 3,
    "hm_coin_50": 2}, extra_exclude=[SIS_RUG])

# ---------------------------------------------------------------- 妹妹的房間
lv.place("hm_bed_low", 1050, 0, 102)
stairs("妹妹床樓梯", (1004, 32, 130), 270, 36, style="blocks", colors=["#ffadad", "#fdffb6", "#caffbf", "#a0c4ff"])
lv.place("hm_kids_table", 860, 0, 120)
stairs("小桌樓梯", (860, 45, 146), 180, 34)
lv.place("hm_kids_chair", 790, 0, 228, color="#ffadad")
lv.place("hm_kids_chair", 1050, 1.0, 402, rot=180, color="#a0c4ff")
lv.block("巧拼地墊", 900, 0, 350, 200, 1.0, 180, color="#ffadad", pattern="jointmat", repeat=60)
MAT = (798, 258, 204, 184)
lv.place("hm_toy_kitchen", 782, 0, 340, rot=-90)
lv.place("hm_rocking_horse", 1078, 0, 330)
top_spawn("ys_bed", (1010, 42, 80, 146), 32, {
    "plush_small": 1, "hm_unicorn": 1, "teddy_small": 1, "hm_soft_block": 1})
top_spawn("ys_table", (827, 97, 66, 46), 45, {
    "crayon": 4, "hm_stacking_cups": 1, "toy_teacup": 3, "toy_cake": 1, "hm_music_box": 1})
top_spawn("ys_mat", (802, 262, 196, 176), 1.0, {
    "hm_soft_block": 6, "hm_wood_block": 6, "hm_stacking_cups": 2, "toy_teacup": 3, "toy_cake": 2, "doll": 2,
    "plush_small": 2, "bouncy_ball": 3, "hm_unicorn": 1, "toy_piano": 1, "picture_book": 2, "hm_rubber_duck": 1})
floor_spawn("ys_floor", (770, 10, 322, 432), 0, {
    "crayon": 6, "hm_crayon_big": 4, "hm_soft_block": 3, "plush_small": 1, "doll": 1, "gacha_capsule": 3,
    "hm_lollipop": 2, "picture_book": 2, "hm_slipper": 1, "hm_sock": 2}, extra_exclude=[MAT])

# ---------------------------------------------------------------- 廁所：小昆蟲
lv.place("hm_toilet", 1190, 0, 45, rot=180)
lv.place("hm_toilet_brush", 1240, 0, 30)
lv.place("hm_wash_basin", 1252.5, 0, 280, rot=90)
stairs("洗手台樓梯", (1229, 80, 280), 270, 30, slope=35)
floor_spawn("to_floor", (1108, 90, 164, 350), 0, {
    "hm_ant": 8, "hm_ladybug": 6, "hm_beetle": 5, "hm_cricket": 5, "hm_toilet_paper": 3, "hm_slipper": 2,
    "hm_air_freshener": 1, "hm_comic": 1, "hm_sock": 1})
top_spawn("to_basin", (1232, 253, 30, 54), 80, {
    "hm_soap": 1, "hm_tooth_cup": 1, "hm_toothbrush": 2, "hm_toothpaste": 1, "hm_ladybug": 1})

# ---------------------------------------------------------------- 浴室：洗澡玩具
TUB = "#5fa8d3"
# 浴缸外圍貼馬賽克磁磚（台灣老式浴缸的樣子）
lv.block("浴缸北緣", 1389, 0, 14, 198, 45, 8, color=TUB, pattern="mosaic", repeat=40)
lv.block("浴缸南緣", 1389, 0, 86, 198, 45, 8, color=TUB, pattern="mosaic", repeat=40)
lv.block("浴缸西緣", 1294, 0, 50, 8, 45, 64, color=TUB, pattern="mosaic", repeat=40)
lv.block("浴缸東緣", 1484, 0, 50, 8, 45, 64, color=TUB, pattern="mosaic", repeat=40)
lv.block("浴缸底", 1389, 0, 50, 182, 6, 64, color="#74c0e3")
stairs("浴缸外樓梯", (1340, 45, 91), 180, 40, style="blocks", colors=["#90e0ef", "#caf0f8", "#ade8f4"])
stairs("浴缸內樓梯", (1440, 45, 81), 0, 34, slope=33, base_y=6, style="blocks",
       colors=["#ffd6a5", "#fdffb6", "#caffbf"])
lv.place("hm_red_stool", 1477, 0, 300)
top_spawn("ba_tub", (1300, 20, 118, 60), 6, {
    "hm_rubber_duck": 4, "hm_toy_boat": 1, "hm_water_gun": 1, "hm_bath_puff": 1, "hm_bubble_bottle": 1})
floor_spawn("ba_floor", (1290, 96, 200, 346), 0, {
    "hm_basin": 2, "hm_shampoo": 3, "hm_bubble_bottle": 2, "hm_towel": 2, "hm_bath_puff": 1, "hm_rubber_duck": 3,
    "hm_soap": 2, "hm_toothbrush": 1, "hm_water_gun": 1, "hm_slipper": 1})

# ---------------------------------------------------------------- 門口（前廊）
lv.place("hm_shoe_cabinet", 380, 0, 1124.5, rot=180)
lv.place("umbrella_stand", 705, 0, 1125)
lv.place("hm_laundry_rack", 135, 0, 1180)
lv.place("hm_bench", 1000, 0, 1130)
lv.place("flower_pot", 790, 0, 1130)
lv.place("small_pot", 1460, 0, 1130)
floor_spawn("porch", (10, 1110, 1480, 136), 0, {
    "hm_sneaker": 3, "hm_rain_boots": 2, "hm_slipper": 4, "hm_umbrella": 2, "hm_helmet": 2, "hm_schoolbag": 1,
    "school_hat": 1, "hm_tshirt": 1, "hm_sock": 3, "hm_bamboo_basket": 1, "laundry_basket": 1, "hm_red_stool": 2,
    "hm_bucket": 1, "hm_basketball": 1, "soccer_ball": 1, "hm_cardboard_box": 1, "hm_coin_10": 3, "pebble": 4})
# 門口到前院：機車斜坡（前院比室內低 12 公分）
CONCRETE = ["#bdbdb5", "#c9c9c4"]
stairs("機車斜坡西", (570, 0, 1251), 180, 180, slope=12, base_y=-12, step=1.5, style="blocks", colors=CONCRETE)
stairs("機車斜坡東", (1180, 0, 1251), 180, 180, slope=12, base_y=-12, step=1.5, style="blocks", colors=CONCRETE)

# ---------------------------------------------------------------- 前院：車子、山櫻花樹
lv.place("hm_car", 330, -12, 1530, rot=180)
lv.place("hm_cherry_tree", 760, -12, 1640)
lv.petals("山櫻花", (760, -12, 1600), (560, 420, 480), color="#ff8fab", amount=110, petal=2.4, fall=20)
lv.place("hm_scooter", 880, -12, 1340, rot=90)
lv.place("kids_bike", 120, -12, 1340)
lv.place("hm_mailbox", 565, -12, 1770)
lv.place("hm_garden_lamp", 930, -12, 1770)
lv.place("dog", 600, -12, 1450, rot=180, roam=(20, 1265, 1460, 520))
floor_spawn("yd_petals", (580, 1462, 360, 316), -12, {"hm_petal": 26})
# 山櫻花樹下，阿公的泡茶桌和塑膠椅
lv.place("hm_tea_table", 690, -12, 1500)
for x, z, r in ((690, 1445, 0), (690, 1555, 180), (635, 1500, 90), (745, 1500, -90)):
    lv.place("hm_plastic_chair", x, -12, z, rot=r, color="#e63946")
# 車頭和圍牆之間只有 40 公分，不放東西（大球進不去，會一直卡在那裡）
floor_spawn("yd_floor", (10, 1312, 935, 476), -12, {
    "hm_plastic_chair": 1, "hm_red_stool": 5, "hm_bucket": 4, "hm_cardboard_box": 4, "hm_tire": 2, "hm_helmet": 2,
    "hm_basketball": 2, "soccer_ball": 2, "laundry_basket": 2, "flower_pot": 2, "planter": 2, "watering_can": 1,
    "hm_bamboo_basket": 2, "hm_kite": 1, "jump_rope": 1, "hm_tshirt": 2, "hm_sock": 3, "hm_sneaker": 2,
    "toy_box": 1, "trash_can": 2, "hm_floor_cushion": 1, "hm_hose_reel": 1, "pebble": 4,
    "hm_rice_bag": 1, "hm_schoolbag": 1, "hm_coin_10": 3, "hm_tricycle": 1, "hm_watermelon": 2, "hm_cooler": 2,
    "hm_quilt": 2, "hm_crate": 2, "hm_soil_bag": 1, "hm_big_pot": 1}, extra_exclude=[(230, 1745, 200, 50)])

# ---------------------------------------------------------------- 小花園
lv.place("hm_dog_house", 1030, -12, 1330)
lv.place("hm_water_jar", 1462, -12, 1330)
lv.place("hm_frog", 1455, 43, 1322, rot=200)
lv.block("花圃", 1095, -12, 1700, 210, 12, 120, color="#8d6e4f", pattern="soil", repeat=80)
lv.block("菜園", 1370, -12, 1700, 220, 12, 120, color="#7f5f43", pattern="soil", repeat=80)
for x, z in ((1020, 1742), (1062, 1750), (1172, 1744)):
    lv.place("hm_sunflower", x, 0, z, rot=180)
lv.place("hm_garden_lamp", 1230, -12, 1700)
lv.place("hm_chicken", 1150, -12, 1500, rot=30, roam=(960, 1390, 530, 240))
lv.place("hm_chicken", 1310, -12, 1560, rot=210, roam=(960, 1390, 530, 240))
floor_spawn("gd_floor", (960, 1382, 530, 252), -12, {
    "hm_hose_reel": 1, "watering_can": 1, "hm_bucket": 2, "hm_trowel": 2, "hm_snail": 5, "hm_butterfly": 3,
    "hm_frog": 2, "hm_flower": 6, "flower_pot": 3, "small_pot": 3, "planter": 2, "hm_tire": 1, "hm_garden_lamp": 1,
    "hm_bamboo_basket": 1, "pebble": 3, "hm_cabbage": 1, "hm_red_stool": 2, "hm_plastic_chair": 1,
    "hm_cardboard_box": 1, "hm_big_pot": 1, "hm_soil_bag": 1, "hm_crate": 1, "hm_watermelon": 1})
lv.spawn("bed_a", (995, 1645, 200, 110), 0, {"hm_flower": 12, "hm_butterfly": 2, "hm_snail": 2},
         avoid_furniture=True)
lv.spawn("bed_b", (1265, 1645, 210, 110), 0, {
    "hm_cabbage": 5, "hm_green_onion": 12, "cherry_tomato": 8, "hm_trowel": 1, "hm_snail": 2},
    avoid_furniture=True)

# ---------------------------------------------------------------- 圍牆外：稻田、小路、電線桿、遠山、鄰居
for x in (-300, 700, 1700):
    lv.decor("電線桿", "cylinder", (x, -14, 1870), (26, 850, 26), "#9a9a96")
for i, (x, z) in enumerate(((-700, 300), (-650, 900), (2200, 200), (2300, 1000), (2100, 2700))):
    lv.decor(f"樹幹{i}", "cylinder", (x, -14, z), (30, 160, 30), "#6f4518")
    lv.decor(f"樹冠{i}", "sphere", (x, 110, z), (260, 220, 260), "#55a630")
lv.decor("鄰居家", "box", (-1300, -14, 600), (650, 320, 520), "#e9d8c4")
lv.decor("鄰居家屋頂", "box", (-1300, 306, 600), (690, 30, 560), "#c4553b", pattern="roof_tile")
lv.decor("鄰居家2", "box", (2800, -14, 1300), (600, 300, 500), "#f1e3c8")
lv.decor("鄰居家2屋頂", "box", (2800, 286, 1300), (640, 30, 540), "#8d99ae", pattern="roof_tile")
for name, pos, size, col in (("遠山北", (-1500, -14, -4200), (5200, 1400, 2400), "#6a994e"),
                             ("遠山東北", (3200, -14, -4600), (6000, 1800, 3000), "#588157"),
                             ("遠山西", (-4600, -14, 600), (2600, 1100, 4200), "#7aa37a"),
                             ("遠山南", (1500, -14, 6200), (7000, 1600, 2600), "#6b9a8b")):
    lv.decor(name, "cone", pos, size, col, no_shadow=True)

# ---------------------------------------------------------------- 起點、救援點、關卡設定
lv.set_start((600, 1.0, 800), 180)
lv.set_rescue((570, 1.0, 720), 180)
lv.set_env(sky="#cfe8ff", fog_color="#e6f2ff", fog_per_d=0.0)
lv.set_stage(
    start_cm=6, goal_cm=100, time_sec=720, comet_sec=480, seed=2026, music="home",
    intro="歡迎來到冬山的家！先把客廳的零食黏起來吧",
    zones=[], gates={}, tuning={},
    grades=[
        {"min_ratio": 0.0, "text": "星婆婆：家裡好大喔，再滾一次吧！"},
        {"min_ratio": 1.0, "text": "星婆婆：一公尺！全家都整理好了，連貓咪小狗都抱回來了。"},
        {"min_ratio": 1.3, "text": "星婆婆：哇，連爸爸的塑膠椅都滾起來了！"},
        {"min_ratio": 1.6, "text": "星婆婆：你把整個院子都滾成一顆大星星了！"},
        {"min_ratio": 1.9, "text": "星婆婆：太厲害了！冬山最會滾的小朋友就是你！"},
    ])


def main():
    items = home_items.write_items()
    import json
    base = json.loads((Path(home_items.ROOT) / "godot" / "data" / "items.json").read_text(encoding="utf-8"))
    known = set(items) | {d["id"] for d in base["items"]}
    missing = set()
    for p in lv.d["placements"]:
        if p["item"] not in known:
            missing.add(p["item"])
    for s in lv.d["spawns"]:
        for k in s["items"]:
            if k not in known:
                missing.add(k)
    if missing:
        raise SystemExit(f"未定義的物件：{sorted(missing)}")
    lv.save()
    total = sum(sum(s["items"].values()) for s in lv.d["spawns"]) + len(lv.d["placements"])
    print(f"[home] 物件總數（散布＋擺放）：{total}，樓梯 {len(lv.d['stairs'])} 座")


if __name__ == "__main__":
    main()
