"""第 1 關「槿寶的家」的物件定義（輸出到 godot/data/items/home.json）。

由 build_dongshan_home.py 呼叫 write_items()。格式與 data/items.json 相同：
    dims：[寬 x, 高 y, 深 z]（公分）；parts 的 pos 是零件中心；cylinder 的 dims 是 [直徑, 高, 直徑]。
    size：吸附尺寸（省略時取最長兩邊的幾何平均）；薄的紙、布類直接指定比較小的 size。
    sfx：黏到時播放的特殊音效鍵；pickable: false 表示永遠黏不起來（大型家具、車子、樹）。
所有物件 id 以 hm_ 開頭。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS_PATH = ROOT / "godot" / "data" / "items" / "home.json"

ITEMS = []


def P(shape, dims, pos, color, rot=None, collide=True, tint=False, name=None):
    """零件。"""
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


def item(iid, name, en, cat, dims, color="#cccccc", shape="box", parts=None, colors=None, fill=0.5,
         flavor=None, sfx=None, pickable=True, size=None, model=None, density=None, critter=None):
    d = {"id": iid, "name": name, "name_en": en, "category": cat}
    if parts:
        d["shape"] = "parts"
        d["parts"] = parts
    else:
        d["shape"] = shape
    d["dims"] = list(dims)
    d["color"] = color
    if colors:
        d["colors"] = colors
    d["fill"] = fill
    if size is not None:
        d["size"] = size
    if model:
        d["model"] = model
    if sfx:
        d["sfx"] = sfx
    if not pickable:
        d["pickable"] = False
    if density is not None:
        d["density"] = density
    if critter:
        d["critter"] = critter
    if flavor:
        d["flavor"] = flavor
    ITEMS.append(d)
    return d


PASTEL = ["#ffadad", "#ffd6a5", "#fdffb6", "#caffbf", "#9bf6ff", "#a0c4ff", "#bdb2ff", "#ffc6ff"]
BRIGHT = ["#e63946", "#f77f00", "#ffd60a", "#2a9d8f", "#3a86ff", "#8338ec", "#ff70a6"]


def define():
    ITEMS.clear()
    # ---------- 客廳：吃零食 ----------
    item("hm_chip", "洋芋片", "Potato Chip", "零食", [3.5, 0.4, 3.0], "#f6c453", "cylinder",
         colors=["#f6c453", "#f2b134", "#f9d77e"], fill=0.5, sfx="snack", flavor="客廳地上掉了好多片，卡滋卡滋！")
    item("hm_chips_bag", "洋芋片袋", "Bag of Chips", "零食", [22, 28, 7], parts=[
        P("box", [22, 24, 7], [0, 12, 0], "#e63946", tint=True),
        P("box", [22, 3, 4], [0, 25.5, 0], "#c1121f", collide=False),
        P("sphere", [9, 9, 1], [0, 13, 3.6], "#ffd60a", collide=False)],
        colors=["#e63946", "#3a86ff", "#2a9d8f"], fill=0.35, sfx="snack", flavor="打開的洋芋片，哥哥說只吃一片。")
    item("hm_popcorn", "爆米花", "Popcorn", "零食", [1.6, 1.4, 1.6], "#fff3c4", "sphere", fill=0.6,
         flavor="從桶子裡跳出來的爆米花。")
    item("hm_popcorn_bucket", "爆米花桶", "Popcorn Bucket", "零食", [14, 18, 14], parts=[
        P("cylinder", [13, 14, 13], [0, 7, 0], "#e63946"),
        P("cylinder", [13.4, 3, 13.4], [0, 6, 0], "#ffffff", collide=False),
        P("sphere", [13, 8, 13], [0, 15, 0], "#fff3c4", collide=False)],
        fill=0.45, sfx="snack", flavor="電影之夜的爆米花，還有一大半。")
    item("hm_pineapple_cake", "鳳梨酥", "Pineapple Cake", "零食", [5, 2, 4], "#e9b872", fill=0.7, sfx="snack",
         flavor="阿嬤最愛的點心，酥酥甜甜。")
    item("hm_egg_roll", "蛋捲", "Egg Roll", "零食", [12, 1.8, 1.8], parts=[
        P("capsule", [1.8, 12, 1.8], [0, 0.9, 0], "#e8a33d", rot=[0, 0, 90])], fill=0.6, sfx="snack")
    item("hm_rice_cracker", "仙貝", "Rice Cracker", "零食", [5, 0.8, 5], "#d9a05b", "cylinder", fill=0.6, sfx="snack")
    item("hm_lollipop", "棒棒糖", "Lollipop", "零食", [4, 12, 1], parts=[
        P("cylinder", [4, 1, 4], [0, 10, 0], "#ff70a6", rot=[90, 0, 0], tint=True),
        P("cylinder", [0.5, 8, 0.5], [0, 4, 0], "#ffffff", collide=False)],
        colors=["#ff70a6", "#70d6ff", "#ffd670", "#caffbf"], fill=0.5)
    item("hm_gummy", "軟糖", "Gummy Candy", "零食", [1.5, 1.5, 1.5], "#ff70a6", "box", colors=BRIGHT, fill=0.7)
    item("hm_milk_candy", "牛奶糖", "Milk Caramel", "零食", [2, 1, 1.2], "#f4e1c1", fill=0.7)
    item("hm_seaweed", "海苔片", "Seaweed Snack", "零食", [6, 0.2, 4], "#2d4a2b", fill=0.5)
    item("hm_tea_cup", "茶杯", "Tea Cup", "餐具", [6, 6, 6], "#f8f4ec", "cylinder", fill=0.4)
    item("hm_teapot", "茶壺", "Teapot", "餐具", [16, 14, 12], parts=[
        P("sphere", [12, 11, 12], [0, 5.5, 0], "#8d5a3b"),
        P("cone", [3, 6, 3], [6.5, 7, 0], "#8d5a3b", rot=[0, 0, -55], collide=False),
        P("cylinder", [5, 2, 5], [0, 11.5, 0], "#6f4518", collide=False)],
        fill=0.4, flavor="阿公泡茶的小茶壺。")
    item("hm_juice_bottle", "果汁瓶", "Juice Bottle", "飲料", [7, 22, 7], parts=[
        P("cylinder", [7, 18, 7], [0, 9, 0], "#ffb703", tint=True),
        P("cylinder", [3, 4, 3], [0, 20, 0], "#ffffff")],
        colors=["#ffb703", "#fb8500", "#8ac926"], fill=0.5)
    item("hm_lactic_drink", "乳酸飲料", "Lactic Drink", "飲料", [4, 9, 4], parts=[
        P("cylinder", [4, 8, 4], [0, 4, 0], "#fff1e6"),
        P("cylinder", [4, 1, 4], [0, 8.5, 0], "#e63946", collide=False)], fill=0.6)
    item("hm_guava", "芭樂", "Guava", "水果", [7, 7, 7], "#a7c957", "sphere", fill=0.6)
    item("hm_fruit_plate", "水果盤", "Fruit Plate", "餐具", [25, 5, 25], parts=[
        P("cylinder", [25, 2, 25], [0, 1, 0], "#ffffff"),
        P("sphere", [6, 4, 6], [-5, 3.5, 2], "#a7c957", collide=False),
        P("sphere", [6, 4, 6], [5, 3.5, -2], "#fb8500", collide=False),
        P("sphere", [5, 3, 5], [1, 3.5, 6], "#e63946", collide=False)], fill=0.35)
    item("hm_game_pad", "遊戲手把", "Game Controller", "玩具", [15, 5, 10], parts=[
        P("box", [15, 4, 7], [0, 2, 0], "#4a4e69"),
        P("cylinder", [5, 4, 5], [-5, 2, 2], "#4a4e69", collide=False),
        P("cylinder", [5, 4, 5], [5, 2, 2], "#4a4e69", collide=False),
        P("sphere", [1.4, 1.4, 1.4], [4, 4.3, -1], "#e63946", collide=False)], fill=0.45)
    item("hm_comic", "漫畫書", "Comic Book", "書", [13, 1.5, 18], "#3a86ff", colors=BRIGHT, fill=0.5)
    item("hm_floor_cushion", "坐墊", "Floor Cushion", "生活", [45, 8, 45], "#f4a261",
         colors=["#f4a261", "#2a9d8f", "#e76f51", "#ffb4a2"], fill=0.3)
    item("hm_photo_frame", "相框", "Photo Frame", "擺飾", [15, 20, 3], parts=[
        P("box", [15, 20, 2], [0, 10, 0], "#b08968"),
        P("box", [11, 15, 0.4], [0, 10, -1.1], "#a0c4ff", collide=False)], fill=0.4,
        flavor="全家去冬山河玩的照片。")
    item("hm_fan", "電風扇", "Electric Fan", "電器", [40, 110, 35], parts=[
        P("cylinder", [35, 4, 35], [0, 2, 0], "#f1faee"),
        P("cylinder", [4, 70, 4], [0, 37, 0], "#e9ecef"),
        P("cylinder", [40, 12, 40], [0, 90, 0], "#a8dadc", rot=[90, 0, 0]),
        P("cylinder", [10, 14, 10], [0, 90, 6], "#f1faee", rot=[90, 0, 0], collide=False)], fill=0.15)
    item("hm_tv", "電視", "TV", "電器", [120, 72, 10], parts=[
        P("box", [120, 70, 6], [0, 37, 0], "#1d1d1f"),
        P("box", [112, 62, 0.5], [0, 37, -3.2], "#264653", collide=False),
        P("box", [30, 2, 10], [0, 1, 0], "#343a40")], pickable=False)
    item("hm_tv_cabinet", "電視櫃", "TV Cabinet", "家具", [180, 50, 45], parts=[
        P("box", [180, 46, 45], [0, 23, 0], "#c9a27e"),
        P("box", [182, 4, 46], [0, 48, 0], "#a47148"),
        P("box", [80, 0.6, 30], [-40, 25, -22.6], "#a47148", collide=False),
        P("box", [80, 0.6, 30], [40, 25, -22.6], "#a47148", collide=False)], pickable=False, fill=0.2)
    item("hm_sofa", "沙發", "Sofa", "家具", [200, 85, 85], parts=[
        P("box", [190, 32, 72], [0, 16, -5], "#7b9e89"),
        P("box", [180, 13, 66], [0, 38.5, -8], "#93b7a1"),
        P("box", [200, 45, 16], [0, 62.5, 34], "#6b8f7b"),
        P("box", [14, 26, 85], [-93, 58, 0], "#6b8f7b"),
        P("box", [14, 26, 85], [93, 58, 0], "#6b8f7b")], pickable=False, fill=0.2)
    item("hm_coffee_table", "客廳茶几", "Coffee Table", "家具", [110, 40, 60], parts=[
        P("box", [110, 4, 60], [0, 38, 0], "#a47148"),
        P("box", [100, 2, 52], [0, 12, 0], "#c9a27e"),
        P("box", [5, 36, 5], [50, 18, 24], "#7f5539"),
        P("box", [5, 36, 5], [-50, 18, 24], "#7f5539"),
        P("box", [5, 36, 5], [50, 18, -24], "#7f5539"),
        P("box", [5, 36, 5], [-50, 18, -24], "#7f5539")], pickable=False, fill=0.2)

    # ---------- 書房：畫蠟筆、玩玩具、小毛線 ----------
    item("hm_desk_study", "書房的大書桌", "Study Desk", "家具", [120, 75, 60], parts=[
        P("box", [120, 4, 60], [0, 73, 0], "#d4a373"),
        P("box", [4, 71, 56], [-57, 35.5, 0], "#c08552"),
        P("box", [42, 71, 56], [38, 35.5, 0], "#c08552"),
        P("box", [70, 30, 2], [-15, 50, 27], "#c08552"),
        P("box", [34, 1, 1], [38, 50, -28.5], "#f1faee", collide=False),
        P("box", [34, 1, 1], [38, 25, -28.5], "#f1faee", collide=False)], pickable=False, fill=0.2)
    item("hm_bookshelf", "書櫃", "Bookshelf", "家具", [80, 180, 30], parts=[
        P("box", [80, 180, 30], [0, 90, 0], "#b08968"),
        P("box", [70, 30, 0.6], [0, 140, -15.2], "#e63946", collide=False),
        P("box", [70, 30, 0.6], [0, 95, -15.2], "#3a86ff", collide=False),
        P("box", [70, 30, 0.6], [0, 50, -15.2], "#ffd60a", collide=False)], pickable=False, fill=0.2)
    item("hm_drawing_paper", "圖畫紙", "Drawing Paper", "文具", [27, 0.3, 38], parts=[
        P("box", [27, 0.3, 38], [0, 0.15, 0], "#fffdf5"),
        P("box", [10, 0.1, 8], [-4, 0.35, -6], "#ffd60a", collide=False, tint=True),
        P("box", [14, 0.1, 3], [3, 0.35, 8], "#3a86ff", collide=False),
        P("box", [3, 0.1, 12], [7, 0.35, -2], "#2a9d8f", collide=False)],
        colors=["#ffd60a", "#ff70a6", "#8ac926"], size=12, fill=0.3,
        flavor="畫了全家人和太陽，還沒畫完。")
    item("hm_crayon_box", "蠟筆盒", "Crayon Box", "文具", [12, 2, 9], parts=[
        P("box", [12, 2, 9], [0, 1, 0], "#ffd60a"),
        P("box", [10, 0.6, 1], [0, 2.3, -3], "#e63946", collide=False),
        P("box", [10, 0.6, 1], [0, 2.3, 0], "#3a86ff", collide=False),
        P("box", [10, 0.6, 1], [0, 2.3, 3], "#2a9d8f", collide=False)], fill=0.5, sfx="crayon")
    item("hm_crayon_big", "粗蠟筆", "Jumbo Crayon", "文具", [11, 1.6, 1.6], parts=[
        P("cylinder", [1.6, 10, 1.6], [0, 0.8, 0], "#e63946", rot=[0, 0, 90], tint=True),
        P("cone", [1.6, 1.4, 1.6], [5.6, 0.8, 0], "#e63946", rot=[0, 0, -90], tint=True, collide=False)],
        colors=BRIGHT, fill=0.7, sfx="crayon", flavor="畫畫畫到一半的蠟筆，摸起來滑滑的。")
    item("hm_yarn_small", "小毛線球", "Little Yarn Ball", "手工藝", [3.5, 3.5, 3.5], "#ffadad", "sphere",
         colors=PASTEL, fill=0.6, sfx="yarn", flavor="書桌旁邊小小的毛線球，軟綿綿。")
    item("hm_yarn_ball", "毛線球", "Yarn Ball", "手工藝", [8, 8, 8], "#bdb2ff", "sphere",
         colors=PASTEL, fill=0.6, sfx="yarn")
    item("hm_knit_basket", "毛線籃", "Knitting Basket", "手工藝", [30, 18, 30], parts=[
        P("cylinder", [30, 14, 30], [0, 7, 0], "#c68b59"),
        P("sphere", [10, 10, 10], [-6, 15, 2], "#ffadad", collide=False),
        P("sphere", [10, 10, 10], [5, 15, -4], "#a0c4ff", collide=False),
        P("sphere", [9, 9, 9], [3, 15, 7], "#caffbf", collide=False)], fill=0.35, sfx="yarn",
        flavor="阿嬤的毛線籃，正在織一條圍巾。")
    item("hm_globe", "地球儀", "Globe", "文具", [25, 38, 25], parts=[
        P("cylinder", [16, 3, 16], [0, 1.5, 0], "#495057"),
        P("cylinder", [2, 10, 2], [0, 7, 0], "#adb5bd", collide=False),
        P("sphere", [25, 25, 25], [0, 25, 0], "#4ea8de"),
        P("sphere", [12, 10, 4], [4, 29, -10], "#8ac926", collide=False)], fill=0.4)
    item("hm_puzzle", "拼圖片", "Puzzle Piece", "玩具", [3, 0.4, 3], "#ffd166", colors=BRIGHT, fill=0.6)
    item("hm_wood_block", "木頭積木", "Wooden Block", "玩具", [4, 4, 4], "#deb887",
         colors=["#deb887", "#e63946", "#3a86ff", "#ffd60a", "#2a9d8f"], fill=0.8)
    item("hm_wood_arch", "拱門積木", "Arch Block", "玩具", [8, 4, 4], parts=[
        P("box", [2.5, 4, 4], [-2.75, 2, 0], "#ffd60a", tint=True),
        P("box", [2.5, 4, 4], [2.75, 2, 0], "#ffd60a", tint=True),
        P("box", [8, 1.5, 4], [0, 3.25, 0], "#ffd60a", tint=True)],
        colors=["#ffd60a", "#e63946", "#3a86ff"], fill=0.6)

    # ---------- 廚房與餐廳：正在煮咖哩 ----------
    item("hm_counter", "流理台", "Kitchen Counter", "家具", [300, 85, 62], parts=[
        P("box", [300, 81, 60], [0, 40.5, 1], "#f1ece3"),
        P("box", [302, 4, 62], [0, 83, 0], "#b8b3ad"),
        P("box", [62, 0.6, 48], [110, 85.3, 0], "#2b2d42", collide=False),
        P("box", [52, 0.6, 38], [-90, 85.3, 0], "#ced4da", collide=False),
        P("box", [280, 0.6, 1], [0, 60, -30.3], "#bfb6a8", collide=False)], pickable=False, fill=0.2)
    item("hm_fridge", "冰箱", "Fridge", "電器", [70, 175, 70], parts=[
        P("box", [70, 175, 70], [0, 87.5, 0], "#e9ecef"),
        P("box", [2, 30, 2], [28, 120, -36], "#adb5bd", collide=False),
        P("box", [6, 6, 1], [-15, 140, -35.5], "#ff70a6", collide=False),
        P("box", [6, 6, 1], [-5, 110, -35.5], "#ffd60a", collide=False)], pickable=False, fill=0.2)
    item("hm_cupboard", "碗櫃", "Cupboard", "家具", [100, 180, 45], parts=[
        P("box", [100, 180, 45], [0, 90, 0], "#c9a27e"),
        P("box", [90, 70, 0.6], [0, 135, -22.6], "#caf0f8", collide=False)], pickable=False, fill=0.2)
    item("hm_dining_table", "餐桌", "Dining Table", "家具", [150, 75, 90], parts=[
        P("box", [150, 4, 90], [0, 73, 0], "#b5835a"),
        P("box", [6, 71, 6], [68, 35.5, 38], "#7f5539"),
        P("box", [6, 71, 6], [-68, 35.5, 38], "#7f5539"),
        P("box", [6, 71, 6], [68, 35.5, -38], "#7f5539"),
        P("box", [6, 71, 6], [-68, 35.5, -38], "#7f5539")], pickable=False, fill=0.2)
    item("hm_curry_pot", "咖哩鍋", "Curry Pot", "廚房", [30, 22, 26], parts=[
        P("cylinder", [26, 16, 26], [0, 8, 0], "#adb5bd"),
        P("cylinder", [24, 1, 24], [0, 15.5, 0], "#c27c0e", collide=False)],
        model="hm_curry_pot", fill=0.45, sfx="curry", flavor="媽媽正在煮咖哩，咕嘟咕嘟好香喔！")
    item("hm_curry_rice", "咖哩飯", "Curry Rice", "廚房", [24, 5, 24], parts=[
        P("cylinder", [24, 2, 24], [0, 1, 0], "#ffffff"),
        P("sphere", [12, 5, 14], [-4, 3, 0], "#fffdf5", collide=False),
        P("sphere", [12, 3, 14], [4, 2.8, 0], "#c27c0e", collide=False)], fill=0.4, sfx="curry",
        flavor="已經盛好的咖哩飯，紅蘿蔔切成星星形狀。")
    item("hm_curry_roux", "咖哩塊", "Curry Roux", "廚房", [6, 1.5, 4], "#8b5a2b", fill=0.7, sfx="curry")
    item("hm_carrot", "紅蘿蔔", "Carrot", "蔬菜", [16, 3, 3], parts=[
        P("cone", [3, 14, 3], [1, 1.5, 0], "#f77f00", rot=[0, 0, -90]),
        P("cone", [2.5, 4, 2.5], [-7.5, 1.5, 0], "#55a630", rot=[0, 0, 90], collide=False)], fill=0.6)
    item("hm_carrot_cube", "紅蘿蔔丁", "Diced Carrot", "蔬菜", [1.5, 1.5, 1.5], "#f77f00", fill=0.8)
    item("hm_potato", "馬鈴薯", "Potato", "蔬菜", [8, 6, 6], "#c9a66b", "sphere", fill=0.7)
    item("hm_potato_cube", "馬鈴薯丁", "Diced Potato", "蔬菜", [2, 2, 2], "#f0d9a0", fill=0.8)
    item("hm_onion", "洋蔥", "Onion", "蔬菜", [8, 8, 8], parts=[
        P("sphere", [8, 7.5, 8], [0, 3.75, 0], "#d4a373"),
        P("cone", [2, 2.5, 2], [0, 8, 0], "#b5835a", collide=False)], fill=0.7)
    item("hm_ladle", "湯勺", "Ladle", "廚房", [8, 4, 30], parts=[
        P("sphere", [8, 4, 8], [0, 2, 11], "#adb5bd"),
        P("box", [1.5, 1, 22], [0, 2, -4], "#6c757d")], fill=0.3)
    item("hm_cutting_board", "砧板", "Cutting Board", "廚房", [35, 2, 25], "#e3c9a0", fill=0.5)
    item("hm_plate", "盤子", "Plate", "餐具", [22, 2, 22], "#ffffff", "cylinder",
         colors=["#ffffff", "#bde0fe", "#ffe5ec"], fill=0.4)
    item("hm_bowl", "碗", "Rice Bowl", "餐具", [12, 6, 12], parts=[
        P("cylinder", [12, 5, 12], [0, 3, 0], "#f8f9fa", tint=True),
        P("cylinder", [7, 1, 7], [0, 0.5, 0], "#f8f9fa", collide=False)],
        colors=["#f8f9fa", "#a0c4ff", "#ffc6ff"], fill=0.4)
    item("hm_spoon", "湯匙", "Spoon", "餐具", [4, 1, 15], parts=[
        P("sphere", [4, 1, 5], [0, 0.5, 5], "#dee2e6"),
        P("box", [1, 0.6, 10], [0, 0.5, -2], "#dee2e6")], fill=0.4)
    item("hm_chopsticks", "筷子", "Chopsticks", "餐具", [1.5, 0.8, 23], "#c68b59", fill=0.6)
    item("hm_spice_jar", "調味罐", "Spice Jar", "廚房", [5, 10, 5], parts=[
        P("cylinder", [5, 8, 5], [0, 4, 0], "#fefae0"),
        P("cylinder", [5, 2, 5], [0, 9, 0], "#e63946", tint=True)],
        colors=["#e63946", "#2a9d8f", "#ffd60a"], fill=0.6)
    item("hm_electric_pot", "電鍋", "Rice Steamer", "電器", [30, 28, 26], parts=[
        P("cylinder", [26, 22, 26], [0, 11, 0], "#e9ecef"),
        P("cylinder", [24, 6, 24], [0, 25, 0], "#dee2e6", collide=False)],
        model="hm_electric_pot", fill=0.4, flavor="家家戶戶都有的電鍋，裡面在蒸飯。")
    item("hm_orange", "橘子", "Orange", "水果", [6.5, 6, 6.5], parts=[
        P("sphere", [6.5, 6, 6.5], [0, 3, 0], "#fb8500"),
        P("sphere", [1.2, 0.4, 2], [0.3, 6, 0], "#2d6a4f", collide=False)],
        model="tangerine", fill=0.6, sfx="orange", flavor="冬天的橘子又甜又多汁，滾來滾去！")
    item("hm_orange_basket", "橘子竹籃", "Basket of Oranges", "水果", [30, 18, 24], parts=[
        P("cylinder", [30, 10, 24], [0, 5, 0], "#c68b59"),
        P("sphere", [8, 8, 8], [-7, 12, 0], "#fb8500", collide=False),
        P("sphere", [8, 8, 8], [3, 12, -5], "#fb8500", collide=False),
        P("sphere", [8, 8, 8], [5, 12, 5], "#f48c06", collide=False),
        P("sphere", [8, 8, 8], [-1, 17, 1], "#fb8500", collide=False)], fill=0.4, sfx="orange")
    item("hm_rice_bag", "米袋", "Rice Sack", "廚房", [30, 40, 15], parts=[
        P("box", [30, 36, 15], [0, 18, 0], "#f1e3c8"),
        P("box", [26, 4, 12], [0, 38, 0], "#e9d8b4", collide=False),
        P("box", [16, 12, 0.4], [0, 20, -7.6], "#55a630", collide=False)], fill=0.5,
        flavor="宜蘭種的白米，一袋好重。")
    item("hm_kettle", "熱水壺", "Kettle", "廚房", [22, 24, 18], parts=[
        P("cylinder", [18, 18, 18], [0, 9, 0], "#e9ecef"),
        P("cylinder", [12, 3, 12], [0, 19.5, 0], "#adb5bd"),
        P("box", [3, 3, 14], [0, 23, 0], "#212529", collide=False)], fill=0.35)
    item("hm_apron", "圍裙", "Apron", "生活", [55, 1, 70], parts=[
        P("box", [55, 1, 70], [0, 0.5, 0], "#ffafcc"),
        P("box", [20, 0.2, 12], [0, 1.1, 8], "#ffffff", collide=False)], size=22, fill=0.3)
    item("hm_slipper", "藍白拖", "Blue-White Slipper", "生活", [10, 3, 26], parts=[
        P("box", [10, 2, 26], [0, 1, 0], "#f8f9fa"),
        P("box", [10.4, 2, 6], [0, 2.5, -4], "#1d4e89", collide=False)], fill=0.5,
        flavor="台灣人的國民拖鞋，啪噠啪噠。")
    item("hm_dish_soap", "洗碗精", "Dish Soap", "廚房", [8, 22, 5], parts=[
        P("box", [8, 19, 5], [0, 9.5, 0], "#80ed99"),
        P("cylinder", [2.5, 3, 2.5], [0, 20.5, 0], "#ffffff", collide=False)], fill=0.5)
    item("hm_scrub", "菜瓜布", "Scrub Sponge", "廚房", [10, 3, 7], parts=[
        P("box", [10, 2, 7], [0, 1, 0], "#ffd60a"),
        P("box", [10, 1, 7], [0, 2.5, 0], "#2d6a4f")], fill=0.6)
    item("hm_cat_food_can", "貓罐頭", "Cat Food Can", "寵物", [7, 4, 7], "#90e0ef", "cylinder", fill=0.7)

    # ---------- 走廊、門口 ----------
    item("hm_schoolbag", "書包", "School Backpack", "學校", [30, 38, 18], parts=[
        P("box", [30, 34, 16], [0, 17, 0], "#3a86ff", tint=True),
        P("box", [26, 14, 2], [0, 12, -8.5], "#1d4e89", collide=False),
        P("box", [6, 3, 1], [0, 22, -9.6], "#ffd60a", collide=False)],
        colors=["#3a86ff", "#e63946", "#8338ec", "#2a9d8f"], fill=0.4, flavor="上學用的書包，放學就丟在走廊。")
    item("hm_umbrella", "雨傘", "Umbrella", "生活", [6, 6, 70], parts=[
        P("cylinder", [6, 55, 6], [0, 3, 5], "#3a86ff", rot=[90, 0, 0], tint=True),
        P("cylinder", [1.2, 20, 1.2], [0, 3, -27], "#495057", rot=[90, 0, 0], collide=False)],
        colors=["#3a86ff", "#ffd60a", "#ff70a6", "#2a9d8f"], fill=0.3, flavor="宜蘭常下雨，出門一定要帶傘。")
    item("hm_rain_boots", "雨鞋", "Rain Boots", "生活", [20, 30, 25], parts=[
        P("box", [9, 28, 10], [-5, 14, 3], "#ffd60a", tint=True),
        P("box", [9, 28, 10], [5, 14, 3], "#ffd60a", tint=True),
        P("box", [20, 7, 24], [0, 3.5, -0.5], "#ffd60a", tint=True)],
        colors=["#ffd60a", "#ff70a6", "#3a86ff"], fill=0.35)
    item("hm_sneaker", "運動鞋", "Sneaker", "生活", [10, 10, 26], parts=[
        P("box", [10, 3, 26], [0, 1.5, 0], "#ffffff"),
        P("box", [9, 7, 18], [0, 6, 3], "#e63946", tint=True)],
        colors=["#e63946", "#3a86ff", "#2a9d8f", "#4a4e69"], fill=0.45)
    item("hm_shoe_cabinet", "鞋櫃", "Shoe Cabinet", "家具", [100, 100, 35], parts=[
        P("box", [100, 100, 35], [0, 50, 0], "#b08968"),
        P("box", [2, 80, 0.5], [0, 50, -17.7], "#7f5539", collide=False)], pickable=False, fill=0.2)
    item("hm_helmet", "安全帽", "Scooter Helmet", "交通", [25, 20, 30], parts=[
        P("sphere", [25, 22, 30], [0, 10, 0], "#e63946", tint=True),
        P("box", [18, 6, 2], [0, 10, -14], "#264653", collide=False)],
        colors=["#e63946", "#ffffff", "#ffd60a", "#3a86ff"], fill=0.4, flavor="爸爸騎機車要戴的安全帽。")
    item("hm_bench", "長板凳", "Wooden Bench", "家具", [120, 45, 30], parts=[
        P("box", [120, 5, 30], [0, 42.5, 0], "#c08552"),
        P("box", [6, 40, 26], [-50, 20, 0], "#9c6644"),
        P("box", [6, 40, 26], [50, 20, 0], "#9c6644")], fill=0.15)

    # ---------- 臥室共用家具 ----------
    item("hm_bed", "單人床", "Single Bed", "家具", [100, 45, 200], parts=[
        P("box", [100, 26, 200], [0, 13, 0], "#c08552"),
        P("box", [96, 19, 194], [0, 35.5, 2], "#f8f9fa"),
        P("box", [100, 70, 6], [0, 35, -98], "#9c6644"),
        P("box", [60, 7, 30], [0, 48, -78], "#ffffff", collide=False),
        P("box", [97, 3, 110], [0, 46.5, 38], "#a0c4ff", collide=False, tint=True)],
        colors=["#a0c4ff", "#ffc6ff", "#caffbf"], pickable=False, fill=0.2)
    item("hm_bed_low", "妹妹的小床", "Toddler Bed", "家具", [90, 32, 180], parts=[
        P("box", [90, 18, 180], [0, 9, 0], "#f4d6cc"),
        P("box", [86, 14, 174], [0, 25, 2], "#fff0f3"),
        P("box", [90, 55, 6], [0, 27.5, -88], "#ffc6ff"),
        P("box", [50, 6, 26], [0, 35, -70], "#ffffff", collide=False),
        P("box", [87, 2, 100], [0, 33, 35], "#ffafcc", collide=False)], pickable=False, fill=0.2)
    item("hm_desk_kid", "小書桌", "Kid's Desk", "家具", [100, 72, 55], parts=[
        P("box", [100, 4, 55], [0, 70, 0], "#e9c46a", tint=True),
        P("box", [4, 68, 52], [-48, 34, 0], "#d4a373"),
        P("box", [36, 68, 52], [32, 34, 0], "#d4a373"),
        P("box", [60, 28, 2], [-12, 50, 25], "#d4a373")],
        colors=["#e9c46a", "#a0c4ff", "#ffafcc"], pickable=False, fill=0.2)
    item("hm_wardrobe", "衣櫃", "Wardrobe", "家具", [120, 200, 60], parts=[
        P("box", [120, 200, 60], [0, 100, 0], "#d6ccc2"),
        P("box", [1, 180, 0.5], [0, 100, -30.3], "#8d99ae", collide=False)], pickable=False, fill=0.2)

    # ---------- 哥哥的房間 ----------
    item("hm_basketball", "籃球", "Basketball", "運動", [24, 24, 24], parts=[
        P("sphere", [24, 24, 24], [0, 12, 0], "#e76f51"),
        P("cylinder", [24.4, 0.6, 24.4], [0, 12, 0], "#3d2b1f", collide=False)], fill=0.6,
        flavor="哥哥每天放學都去打球。")
    item("hm_baseball", "棒球", "Baseball", "運動", [7.4, 7.4, 7.4], "#f8f9fa", "sphere", fill=0.8)
    item("hm_baseball_glove", "棒球手套", "Baseball Glove", "運動", [22, 10, 25], parts=[
        P("sphere", [22, 10, 25], [0, 5, 0], "#a0522d"),
        P("box", [4, 9, 12], [9, 5, -5], "#8b4513", collide=False)], fill=0.4)
    item("hm_bat", "球棒", "Baseball Bat", "運動", [6, 6, 70], parts=[
        P("cylinder", [6, 45, 6], [0, 3, 10], "#deb887", rot=[90, 0, 0]),
        P("cylinder", [3, 25, 3], [0, 3, -24], "#c19a6b", rot=[90, 0, 0])], fill=0.4)
    item("hm_model_plane", "模型飛機", "Model Plane", "玩具", [30, 10, 28], parts=[
        P("capsule", [5, 28, 5], [0, 5, 0], "#f8f9fa", rot=[90, 0, 0]),
        P("box", [30, 1, 7], [0, 5, -1], "#3a86ff"),
        P("box", [10, 6, 1], [0, 8, 12], "#e63946", collide=False)], fill=0.3)
    item("hm_xiangqi", "象棋棋子", "Xiangqi Piece", "傳統玩具", [3, 1.2, 3], parts=[
        P("cylinder", [3, 1.2, 3], [0, 0.6, 0], "#f1dca7"),
        P("cylinder", [2, 0.1, 2], [0, 1.25, 0], "#d62828", collide=False, tint=True)],
        colors=["#d62828", "#1d1d1f"], fill=0.8, flavor="阿公教哥哥下象棋。")
    item("hm_calculator", "計算機", "Calculator", "文具", [8, 1.5, 14], parts=[
        P("box", [8, 1.5, 14], [0, 0.75, 0], "#495057"),
        P("box", [6, 0.2, 3], [0, 1.6, -4.5], "#caffbf", collide=False)], fill=0.5)

    # ---------- 姐姐的房間 ----------
    item("hm_diary", "日記本", "Diary", "文具", [15, 2, 21], parts=[
        P("box", [15, 2, 21], [0, 1, 0], "#ffafcc", tint=True),
        P("box", [3, 0.4, 3], [4, 2.1, -6], "#ffd60a", collide=False)],
        colors=["#ffafcc", "#bdb2ff", "#a0c4ff"], fill=0.5, flavor="姐姐的祕密日記，有一個小鎖頭。")
    item("hm_hand_mirror", "手鏡", "Hand Mirror", "生活", [12, 1.5, 22], parts=[
        P("cylinder", [12, 1.5, 12], [0, 0.75, -5], "#ffc6ff"),
        P("cylinder", [10, 0.2, 10], [0, 1.6, -5], "#e0fbfc", collide=False),
        P("box", [3, 1.5, 10], [0, 0.75, 6], "#ffc6ff")], fill=0.5)
    item("hm_ukulele", "烏克麗麗", "Ukulele", "樂器", [22, 6, 55], parts=[
        P("cylinder", [22, 6, 30], [0, 3, 10], "#d4a373"),
        P("box", [5, 3, 30], [0, 3, -16], "#7f5539"),
        P("cylinder", [6, 0.4, 6], [0, 6.2, 8], "#3d2b1f", collide=False)], fill=0.35,
        flavor="姐姐在學的烏克麗麗，叮叮咚咚。", sfx="bell")
    item("hm_scrunchie", "大髮圈", "Scrunchie", "飾品", [8, 2.5, 8], "#ffc6ff", "cylinder", colors=PASTEL, fill=0.6)
    item("hm_bracelet", "串珠手鍊", "Bead Bracelet", "飾品", [6, 1, 6], "#9bf6ff", "cylinder", colors=PASTEL, fill=0.5)
    item("hm_perler_art", "拼豆作品", "Perler Bead Art", "手工藝", [12, 0.6, 12], parts=[
        P("box", [12, 0.6, 12], [0, 0.3, 0], "#ffd60a"),
        P("box", [6, 0.2, 6], [0, 0.7, 0], "#ff70a6", collide=False)], fill=0.5)

    # ---------- 妹妹的房間 ----------
    item("hm_kids_table", "兒童小桌", "Kids Table", "家具", [70, 45, 50], parts=[
        P("box", [70, 4, 50], [0, 43, 0], "#ffd6a5"),
        P("box", [5, 41, 5], [30, 20.5, 20], "#ffadad"),
        P("box", [5, 41, 5], [-30, 20.5, 20], "#a0c4ff"),
        P("box", [5, 41, 5], [30, 20.5, -20], "#caffbf"),
        P("box", [5, 41, 5], [-30, 20.5, -20], "#bdb2ff")], pickable=False, fill=0.2)
    item("hm_kids_chair", "兒童小椅子", "Kids Chair", "家具", [30, 50, 30], parts=[
        P("box", [30, 3, 30], [0, 26, 0], "#ffadad", tint=True),
        P("box", [30, 22, 3], [0, 38, 13.5], "#ffadad", tint=True),
        P("box", [3, 25, 3], [12, 12.5, 12], "#ffffff"),
        P("box", [3, 25, 3], [-12, 12.5, 12], "#ffffff"),
        P("box", [3, 25, 3], [12, 12.5, -12], "#ffffff"),
        P("box", [3, 25, 3], [-12, 12.5, -12], "#ffffff")],
        colors=["#ffadad", "#a0c4ff", "#caffbf", "#ffd6a5"], fill=0.25)
    item("hm_toy_kitchen", "玩具廚房", "Toy Kitchen", "玩具", [60, 80, 30], parts=[
        P("box", [60, 50, 30], [0, 25, 0], "#ffc6ff"),
        P("box", [60, 30, 4], [0, 65, 13], "#ffadad"),
        P("cylinder", [10, 1, 10], [-14, 50.5, 0], "#495057", collide=False),
        P("cylinder", [10, 1, 10], [12, 50.5, 0], "#495057", collide=False)], fill=0.18,
        flavor="妹妹在煮假裝的咖哩，跟媽媽一樣。")
    item("hm_soft_block", "軟積木", "Soft Block", "玩具", [15, 15, 15], "#ffadad", colors=PASTEL, fill=0.6)
    item("hm_rocking_horse", "搖搖馬", "Rocking Horse", "玩具", [30, 60, 70], parts=[
        P("box", [26, 4, 70], [0, 3, 0], "#ff70a6"),
        P("capsule", [22, 40, 22], [0, 30, 0], "#ffffff", rot=[90, 0, 0]),
        P("capsule", [14, 26, 14], [0, 47, -20], "#ffffff", rot=[35, 0, 0]),
        P("box", [6, 14, 18], [0, 50, -12], "#ff70a6", collide=False)], fill=0.18)
    item("hm_stacking_cups", "疊疊杯", "Stacking Cups", "玩具", [8, 12, 8], parts=[
        P("cylinder", [8, 4, 8], [0, 2, 0], "#e63946"),
        P("cylinder", [6.5, 4, 6.5], [0, 6, 0], "#ffd60a"),
        P("cylinder", [5, 4, 5], [0, 10, 0], "#3a86ff")], fill=0.5)
    item("hm_unicorn", "獨角獸娃娃", "Unicorn Plush", "娃娃", [12, 20, 22], parts=[
        P("sphere", [12, 13, 20], [0, 8, 0], "#fff0f3"),
        P("sphere", [9, 9, 9], [0, 15, -8], "#fff0f3"),
        P("cone", [2, 6, 2], [0, 21, -9], "#ffd60a", collide=False),
        P("box", [3, 8, 6], [0, 15, -2], "#bdb2ff", collide=False)], fill=0.45)
    item("hm_music_box", "音樂盒", "Music Box", "擺飾", [10, 8, 7], parts=[
        P("box", [10, 6, 7], [0, 3, 0], "#ffafcc"),
        P("cylinder", [4, 2, 4], [0, 7, 0], "#ffd60a", collide=False)], fill=0.5, sfx="bell",
        flavor="打開會叮叮咚咚唱歌。")

    # ---------- 廁所：小昆蟲 ----------
    item("hm_toilet", "馬桶", "Toilet", "衛浴", [40, 75, 70], parts=[
        P("cylinder", [38, 40, 50], [0, 20, 6], "#f8f9fa"),
        P("box", [40, 35, 18], [0, 57, 26], "#f8f9fa"),
        P("cylinder", [38, 3, 48], [0, 41.5, 6], "#e9ecef", collide=False)], pickable=False, fill=0.2)
    item("hm_wash_basin", "洗手台", "Wash Basin", "衛浴", [60, 80, 45], parts=[
        P("box", [60, 76, 45], [0, 38, 0], "#e9ecef"),
        P("box", [62, 4, 46], [0, 78, 0], "#f8f9fa"),
        P("box", [34, 0.6, 26], [0, 80.3, -2], "#caf0f8", collide=False),
        P("cylinder", [2.5, 10, 2.5], [0, 85, 14], "#adb5bd", collide=False)], pickable=False, fill=0.2)
    item("hm_toilet_paper", "衛生紙捲", "Toilet Paper Roll", "衛浴", [11, 10, 11], parts=[
        P("cylinder", [11, 10, 11], [0, 5, 0], "#ffffff"),
        P("cylinder", [4, 10.2, 4], [0, 5, 0], "#d6ccc2", collide=False)], fill=0.5)
    item("hm_toilet_brush", "馬桶刷", "Toilet Brush", "衛浴", [10, 40, 10], parts=[
        P("cylinder", [10, 14, 10], [0, 7, 0], "#90e0ef"),
        P("cylinder", [2, 28, 2], [0, 26, 0], "#90e0ef", collide=False)], fill=0.3)
    item("hm_air_freshener", "芳香劑", "Air Freshener", "衛浴", [7, 15, 7], parts=[
        P("cylinder", [7, 12, 7], [0, 6, 0], "#cdb4db"),
        P("cylinder", [5, 3, 5], [0, 13.5, 0], "#ffffff")], fill=0.5)
    item("hm_ant", "螞蟻", "Ant", "昆蟲", [0.4, 0.3, 0.9], parts=[
        P("capsule", [0.35, 0.9, 0.35], [0, 0.18, 0], "#2b2d42", rot=[90, 0, 0])],
        fill=0.8, sfx="bug", flavor="排隊在搬餅乾屑的小螞蟻。")
    item("hm_ladybug", "瓢蟲", "Ladybug", "昆蟲", [1.2, 0.7, 1.4], parts=[
        P("sphere", [1.2, 0.7, 1.2], [0, 0.35, 0.1], "#e63946"),
        P("sphere", [0.6, 0.5, 0.5], [0, 0.3, -0.6], "#1d1d1f", collide=False)],
        fill=0.8, sfx="bug", flavor="紅色的瓢蟲，背上有小黑點。")
    item("hm_beetle", "小甲蟲", "Little Beetle", "昆蟲", [1.8, 1.0, 2.8], parts=[
        P("sphere", [1.8, 1.0, 2.4], [0, 0.5, 0.2], "#2a9d8f"),
        P("sphere", [1.0, 0.7, 0.8], [0, 0.4, -1.1], "#264653", collide=False)],
        fill=0.8, sfx="bug")
    item("hm_cricket", "蟋蟀", "Cricket", "昆蟲", [1.2, 1.0, 3.5], parts=[
        P("capsule", [1.0, 3.2, 1.0], [0, 0.5, 0], "#6b4f3a", rot=[90, 0, 0]),
        P("box", [2.2, 0.2, 0.2], [0, 1.0, 1.2], "#4a3728", collide=False)],
        fill=0.8, sfx="bug", flavor="躲在角落唧唧叫的蟋蟀。")
    item("hm_soap", "肥皂", "Soap", "衛浴", [9, 3, 6], "#ffc8dd", colors=["#ffc8dd", "#caffbf", "#fdffb6"], fill=0.7,
         sfx="bubble")
    item("hm_tooth_cup", "漱口杯", "Tooth Cup", "衛浴", [8, 10, 8], "#a0c4ff", "cylinder", colors=PASTEL, fill=0.4)
    item("hm_toothbrush", "牙刷", "Toothbrush", "衛浴", [2, 2, 18], parts=[
        P("box", [1.5, 1.5, 18], [0, 0.75, 0], "#3a86ff", tint=True),
        P("box", [1.5, 1.5, 2.5], [0, 2, 7.5], "#ffffff", collide=False)],
        colors=["#3a86ff", "#ff70a6", "#8ac926"], fill=0.5)
    item("hm_toothpaste", "牙膏", "Toothpaste", "衛浴", [4, 3, 18], parts=[
        P("box", [4, 3, 15], [0, 1.5, 1], "#ffffff"),
        P("cylinder", [2.5, 3, 2.5], [0, 1.5, -8], "#e63946", rot=[90, 0, 0])], fill=0.5)

    # ---------- 浴室：洗澡玩具 ----------
    item("hm_rubber_duck", "小黃鴨", "Rubber Duck", "洗澡玩具", [7, 7, 9], parts=[
        P("sphere", [7, 5, 9], [0, 2.5, 0], "#ffd60a"),
        P("sphere", [4.5, 4.5, 4.5], [0, 6, -2.5], "#ffd60a", collide=False)],
        model="hm_rubber_duck", fill=0.5, sfx="duck", flavor="洗澡一定要有的小黃鴨，呱呱！")
    item("hm_toy_boat", "玩具小船", "Toy Boat", "洗澡玩具", [8, 7, 16], parts=[
        P("box", [8, 4, 16], [0, 2, 0], "#3a86ff"),
        P("box", [6, 3, 6], [0, 5.5, 2], "#ffffff", collide=False)], fill=0.4, sfx="bubble")
    item("hm_bubble_bottle", "泡泡水", "Bubble Bottle", "洗澡玩具", [5, 12, 5], parts=[
        P("cylinder", [5, 10, 5], [0, 5, 0], "#9bf6ff"),
        P("cylinder", [3, 2, 3], [0, 11, 0], "#ff70a6", collide=False)], fill=0.5, sfx="bubble",
        flavor="吹泡泡用的，一吹就飄滿整間浴室。")
    item("hm_shampoo", "洗髮精", "Shampoo", "衛浴", [8, 20, 5], parts=[
        P("box", [8, 17, 5], [0, 8.5, 0], "#bde0fe", tint=True),
        P("cylinder", [3, 3, 3], [0, 18.5, 0], "#ffffff", collide=False)],
        colors=["#bde0fe", "#ffc8dd", "#caffbf"], fill=0.5)
    item("hm_basin", "臉盆", "Wash Basin Bowl", "衛浴", [35, 12, 35], "#ffafcc", "cylinder",
         colors=["#ffafcc", "#90e0ef", "#caffbf"], fill=0.3, flavor="大大的塑膠臉盆，洗澡、洗菜都用它。")
    item("hm_red_stool", "紅色塑膠凳", "Red Plastic Stool", "家具", [30, 28, 30], parts=[
        P("cylinder", [30, 4, 30], [0, 26, 0], "#d62828"),
        P("cylinder", [26, 24, 26], [0, 12, 0], "#d62828")],
        model="hm_red_stool", fill=0.3, flavor="台灣每個家裡都有的紅色小板凳。")
    item("hm_towel", "毛巾", "Towel", "衛浴", [30, 1, 60], "#a0c4ff", colors=PASTEL, size=15, fill=0.3)
    item("hm_bath_puff", "沐浴球", "Bath Puff", "衛浴", [9, 9, 9], "#ffc6ff", "sphere", colors=PASTEL, fill=0.5,
         sfx="bubble")
    item("hm_water_gun", "水槍", "Water Gun", "洗澡玩具", [4, 10, 16], parts=[
        P("box", [4, 5, 16], [0, 7, 0], "#06d6a0"),
        P("box", [4, 7, 4], [0, 3.5, 5], "#ff9f1c")], fill=0.4, sfx="bubble")

    # ---------- 前院、花園 ----------
    item("hm_car", "家裡的車", "Family Car", "交通", [175, 150, 440], parts=[
        P("box", [175, 75, 440], [0, 52, 0], "#e5e5e5"),
        P("box", [160, 60, 230], [0, 115, 20], "#bde0fe")],
        model="hm_car", pickable=False, fill=0.2, flavor="爸爸開的車，週末全家去冬山河。")
    item("hm_cherry_tree", "山櫻花樹", "Taiwan Cherry Tree", "植物", [340, 420, 340], parts=[
        P("cylinder", [26, 200, 26], [0, 100, 0], "#6f4518"),
        P("sphere", [300, 170, 300], [0, 300, 0], "#ffafcc", collide=False)],
        model="hm_cherry_tree", pickable=False, fill=0.2, flavor="春天開滿粉紅色的花，風一吹就下花瓣雨。")
    item("hm_petal", "櫻花花瓣", "Cherry Petal", "植物", [2.2, 0.1, 2.2], parts=[
        P("cylinder", [2.2, 0.1, 2.2], [0, 0.05, 0], "#ffafcc", tint=True)],
        colors=["#ffafcc", "#ffc8dd", "#ffe5ec"], fill=0.3, flavor="從山櫻花樹飄下來的花瓣。")
    item("hm_scooter", "機車", "Scooter", "交通", [70, 110, 180], parts=[
        P("box", [40, 45, 120], [0, 45, 10], "#4ea8de"),
        P("box", [34, 20, 60], [0, 75, 25], "#212529"),
        P("box", [10, 70, 10], [0, 70, -60], "#4ea8de"),
        P("cylinder", [12, 40, 40], [0, 20, -65], "#212529", rot=[0, 0, 90]),
        P("cylinder", [12, 40, 40], [0, 20, 65], "#212529", rot=[0, 0, 90])],
        model="hm_scooter", pickable=False, fill=0.2, flavor="媽媽每天騎去市場的機車。")
    item("hm_dog_house", "狗屋", "Dog House", "寵物", [80, 85, 90], parts=[
        P("box", [80, 60, 90], [0, 30, 0], "#c08552"),
        P("box", [86, 6, 96], [-20, 72, 0], "#9d0208", rot=[0, 0, 30]),
        P("box", [86, 6, 96], [20, 72, 0], "#9d0208", rot=[0, 0, -30]),
        P("box", [30, 36, 1], [0, 18, -45.2], "#3d2b1f", collide=False)], pickable=False, fill=0.2)
    item("hm_plastic_chair", "塑膠椅", "Plastic Chair", "家具", [45, 80, 45], parts=[
        P("box", [45, 4, 45], [0, 43, 0], "#e63946", tint=True),
        P("box", [45, 36, 4], [0, 63, 20], "#e63946", tint=True),
        P("cylinder", [4, 43, 4], [18, 21, 18], "#e63946", tint=True),
        P("cylinder", [4, 43, 4], [-18, 21, 18], "#e63946", tint=True),
        P("cylinder", [4, 43, 4], [18, 21, -18], "#e63946", tint=True),
        P("cylinder", [4, 43, 4], [-18, 21, -18], "#e63946", tint=True)],
        colors=["#e63946", "#3a86ff", "#f8f9fa"], fill=0.15, flavor="辦桌也會用的塑膠椅，可以疊很高。")
    item("hm_bucket", "水桶", "Bucket", "庭院", [28, 30, 28], parts=[
        P("cylinder", [28, 28, 28], [0, 14, 0], "#3a86ff", tint=True),
        P("cylinder", [26, 1, 26], [0, 29, 0], "#adb5bd", collide=False)],
        colors=["#3a86ff", "#e63946", "#ffd60a", "#2a9d8f"], fill=0.3)
    item("hm_cardboard_box", "紙箱", "Cardboard Box", "生活", [50, 40, 40], parts=[
        P("box", [50, 40, 40], [0, 20, 0], "#c9a26b"),
        P("box", [50.4, 6, 0.4], [0, 34, -20.1], "#e9c46a", collide=False)], fill=0.22,
        flavor="網購寄來的大紙箱，貓咪最喜歡躲進去。")
    item("hm_tire", "舊輪胎", "Old Tire", "庭院", [60, 20, 60], parts=[
        P("cylinder", [60, 20, 60], [0, 10, 0], "#2b2d42"),
        P("cylinder", [32, 20.4, 32], [0, 10, 0], "#6c757d", collide=False)], fill=0.2,
        flavor="阿公拿來種花的舊輪胎。")
    item("hm_hose_reel", "水管捲", "Hose Reel", "庭院", [40, 40, 20], parts=[
        P("cylinder", [40, 18, 40], [0, 20, 0], "#06d6a0", rot=[90, 0, 0]),
        P("cylinder", [22, 19, 22], [0, 20, 0], "#2a9d8f", rot=[90, 0, 0], collide=False)], fill=0.35)
    item("hm_trowel", "小鏟子", "Garden Trowel", "庭院", [8, 4, 30], parts=[
        P("box", [8, 1, 12], [0, 1, 8], "#adb5bd"),
        P("cylinder", [3, 16, 3], [0, 2, -7], "#2a9d8f", rot=[90, 0, 0])], fill=0.4)
    item("hm_cabbage", "高麗菜", "Cabbage", "蔬菜", [20, 18, 20], "#a7c957", "sphere", fill=0.6,
         flavor="菜園裡圓滾滾的高麗菜。")
    item("hm_green_onion", "青蔥", "Green Onion", "蔬菜", [3, 40, 3], parts=[
        P("cylinder", [2.5, 12, 2.5], [0, 6, 0], "#f8f9fa"),
        P("cylinder", [2.5, 28, 2.5], [0, 26, 0], "#55a630", collide=False)], fill=0.5,
        flavor="菜園裡的青蔥，阿嬤煮湯要用。")
    item("hm_sunflower", "向日葵", "Sunflower", "植物", [25, 110, 25], parts=[
        P("cylinder", [3, 90, 3], [0, 45, 0], "#55a630"),
        P("cylinder", [25, 4, 25], [0, 95, 0], "#ffd60a", rot=[70, 0, 0]),
        P("cylinder", [11, 5, 11], [0, 95, -1], "#6f4518", rot=[70, 0, 0], collide=False)], fill=0.25)
    item("hm_flower", "小花", "Garden Flower", "植物", [8, 25, 8], parts=[
        P("cylinder", [1, 20, 1], [0, 10, 0], "#55a630"),
        P("sphere", [8, 4, 8], [0, 21, 0], "#ff70a6", tint=True),
        P("sphere", [3, 3, 3], [0, 22.5, 0], "#ffd60a", collide=False)],
        colors=["#ff70a6", "#ffd60a", "#bdb2ff", "#ffffff", "#ff9f1c"], fill=0.4,
        flavor="花園裡開得好熱鬧的小花。")
    item("hm_water_jar", "大水缸", "Water Jar", "庭院", [60, 55, 60], parts=[
        P("cylinder", [60, 55, 60], [0, 27.5, 0], "#6f4518"),
        P("cylinder", [54, 0.6, 54], [0, 52, 0], "#4ea8de", collide=False),
        P("sphere", [12, 2, 12], [10, 52.5, 6], "#55a630", collide=False)], fill=0.2,
        flavor="接雨水的大水缸，裡面有小魚和浮萍。")
    item("hm_frog", "小青蛙", "Little Frog", "動物", [5, 3, 6], parts=[
        P("sphere", [5, 3, 6], [0, 1.5, 0], "#80b918"),
        P("sphere", [1.2, 1.2, 1.2], [-1.2, 3, -1.8], "#ffffff", collide=False),
        P("sphere", [1.2, 1.2, 1.2], [1.2, 3, -1.8], "#ffffff", collide=False)],
        fill=0.7, sfx="frog", flavor="住在水缸旁邊的小青蛙，呱呱！")
    item("hm_snail", "蝸牛", "Snail", "動物", [3, 3, 5], parts=[
        P("sphere", [3, 3, 3], [0, 1.8, 0.6], "#b5835a"),
        P("capsule", [1.4, 5, 1.4], [0, 0.7, 0], "#e9d8a6", rot=[90, 0, 0], collide=False)], fill=0.7,
        sfx="bug")
    item("hm_butterfly", "蝴蝶", "Butterfly", "昆蟲", [6, 1, 5], parts=[
        P("box", [6, 0.3, 5], [0, 0.5, 0], "#ffd60a", tint=True),
        P("capsule", [0.6, 4, 0.6], [0, 0.6, 0], "#2b2d42", rot=[90, 0, 0], collide=False)],
        colors=["#ffd60a", "#9bf6ff", "#ffadad"], fill=0.5, sfx="bug")
    item("hm_chicken", "母雞", "Hen", "動物", [22, 36, 40], parts=[
        P("sphere", [22, 24, 32], [0, 18, 2], "#f1e3c8")],
        model="hm_chicken", size=30, fill=0.4,
        critter={"kind": "chicken", "walk": 18, "run": 70, "sight": 150, "paw_cooldown": 6.0, "sound": "chicken"},
        flavor="阿嬤養的母雞，會跑來啄你一下。")
    item("hm_bamboo_basket", "竹編籃", "Bamboo Basket", "生活", [40, 20, 30], parts=[
        P("cylinder", [40, 16, 30], [0, 8, 0], "#c9a26b"),
        P("box", [3, 14, 30], [0, 22, 0], "#a47148", collide=False)], fill=0.3,
        flavor="阿嬤用竹子編的籃子。")
    item("hm_mailbox", "信箱", "Mailbox", "庭院", [30, 110, 25], parts=[
        P("cylinder", [6, 80, 6], [0, 40, 0], "#495057"),
        P("box", [30, 28, 25], [0, 94, 0], "#2a9d8f")], fill=0.2)
    item("hm_laundry_rack", "曬衣架", "Clothes Drying Rack", "生活", [150, 160, 50], parts=[
        P("box", [6, 160, 6], [-72, 80, 0], "#adb5bd"),
        P("box", [6, 160, 6], [72, 80, 0], "#adb5bd"),
        P("box", [150, 4, 4], [0, 155, 0], "#adb5bd", collide=False),
        P("box", [40, 50, 1], [-40, 125, 0], "#a0c4ff", collide=False),
        P("box", [35, 45, 1], [5, 128, 0], "#ffd6a5", collide=False),
        P("box", [30, 40, 1], [48, 130, 0], "#caffbf", collide=False)], pickable=False, fill=0.2)
    item("hm_tshirt", "T恤", "T-shirt", "衣服", [45, 1, 55], parts=[
        P("box", [45, 1, 50], [0, 0.5, 2], "#a0c4ff", tint=True),
        P("box", [60, 1, 14], [0, 0.6, -18], "#a0c4ff", tint=True, collide=False)],
        colors=["#a0c4ff", "#ffd6a5", "#caffbf", "#ffadad"], size=22, fill=0.3)
    item("hm_sock", "襪子", "Sock", "衣服", [8, 2, 20], "#ffffff", colors=["#ffffff", "#ffadad", "#a0c4ff"], fill=0.5)
    item("hm_tricycle", "兒童三輪車", "Kids Tricycle", "交通", [50, 50, 70], parts=[
        P("cylinder", [30, 6, 30], [0, 15, -22], "#e63946", rot=[0, 0, 90]),
        P("cylinder", [18, 5, 18], [-20, 9, 22], "#212529", rot=[0, 0, 90]),
        P("cylinder", [18, 5, 18], [20, 9, 22], "#212529", rot=[0, 0, 90]),
        P("box", [8, 6, 50], [0, 22, 0], "#e63946"),
        P("box", [18, 5, 16], [0, 30, 10], "#ffd60a"),
        P("box", [34, 3, 3], [0, 46, -20], "#495057", collide=False)], fill=0.18,
        flavor="妹妹騎的三輪車，叭叭！", sfx="bike_bell")
    item("hm_watermelon", "西瓜", "Watermelon", "水果", [30, 26, 30], parts=[
        P("sphere", [30, 26, 30], [0, 13, 0], "#2d6a4f"),
        P("box", [2, 26.5, 30.5], [0, 13, 0], "#95d5b2", collide=False),
        P("box", [30.5, 26.5, 2], [0, 13, 0], "#95d5b2", collide=False)], fill=0.6,
        flavor="夏天的大西瓜，阿公說要冰起來。")
    item("hm_cooler", "冰桶", "Cooler Box", "生活", [40, 35, 28], parts=[
        P("box", [40, 30, 28], [0, 15, 0], "#3a86ff"),
        P("box", [41, 5, 29], [0, 32.5, 0], "#f8f9fa")], fill=0.35)
    item("hm_quilt", "曬太陽的棉被", "Quilt", "生活", [90, 6, 70], parts=[
        P("box", [90, 6, 70], [0, 3, 0], "#ffd6a5", tint=True),
        P("box", [70, 0.4, 10], [0, 6.2, -15], "#ff70a6", collide=False),
        P("box", [70, 0.4, 10], [0, 6.2, 15], "#ff70a6", collide=False)],
        colors=["#ffd6a5", "#bde0fe", "#caffbf"], size=45, fill=0.2, flavor="阿嬤拿出來曬太陽的棉被，香香的。")
    item("hm_crate", "塑膠籃", "Plastic Crate", "生活", [50, 25, 35], parts=[
        P("box", [50, 25, 35], [0, 12.5, 0], "#2a9d8f", tint=True),
        P("box", [46, 0.5, 31], [0, 25.2, 0], "#264653", collide=False)],
        colors=["#2a9d8f", "#ffd60a", "#e63946"], fill=0.3, flavor="市場買菜用的塑膠籃。")
    item("hm_soil_bag", "培養土", "Bag of Potting Soil", "庭院", [40, 12, 60], parts=[
        P("box", [40, 12, 60], [0, 6, 0], "#6f4518"),
        P("box", [26, 0.4, 20], [0, 12.2, -8], "#80b918", collide=False)], fill=0.3)
    item("hm_tea_table", "泡茶桌", "Tea Table", "家具", [60, 45, 60], parts=[
        P("box", [60, 4, 60], [0, 43, 0], "#7f5539"),
        P("box", [50, 39, 50], [0, 20.5, 0], "#9c6644"),
        P("cylinder", [12, 10, 10], [0, 50, 0], "#8d5a3b", collide=False),
        P("cylinder", [5, 4, 5], [15, 47, 10], "#f8f4ec", collide=False)], fill=0.15,
        flavor="阿公在院子泡茶的小桌子。")
    item("hm_big_pot", "大花盆", "Large Planter Pot", "植物", [48, 55, 48], parts=[
        P("cylinder", [48, 34, 48], [0, 17, 0], "#e07a5f"),
        P("sphere", [44, 30, 44], [0, 42, 0], "#55a630", collide=False),
        P("sphere", [10, 8, 10], [8, 54, 4], "#ff70a6", collide=False)], fill=0.25)
    item("hm_garden_lamp", "庭園燈", "Garden Lamp", "庭院", [15, 60, 15], parts=[
        P("cylinder", [5, 50, 5], [0, 25, 0], "#343a40"),
        P("sphere", [15, 15, 15], [0, 54, 0], "#fff3b0")], fill=0.25)
    item("hm_kite", "風箏", "Kite", "玩具", [50, 2, 60], parts=[
        P("box", [42, 1, 42], [0, 1, 0], "#e63946", rot=[0, 45, 0], tint=True),
        P("box", [2, 1, 40], [0, 1.5, 30], "#ffd60a", collide=False)],
        colors=["#e63946", "#3a86ff", "#ffd60a"], size=26, fill=0.3)
    item("hm_coin_1", "一元硬幣", "NT$1 Coin", "錢", [2.0, 0.15, 2.0], "#c9a227", "cylinder", fill=0.9)
    item("hm_coin_5", "五元硬幣", "NT$5 Coin", "錢", [2.2, 0.17, 2.2], "#ced4da", "cylinder", fill=0.9)
    item("hm_coin_10", "十元硬幣", "NT$10 Coin", "錢", [2.6, 0.2, 2.6], "#dee2e6", "cylinder", fill=0.9)
    item("hm_coin_50", "五十元硬幣", "NT$50 Coin", "錢", [2.8, 0.25, 2.8], "#e9c46a", "cylinder", fill=0.9)
    item("hm_zhuyin_book", "注音作業簿", "Zhuyin Workbook", "學校", [18, 0.6, 26], parts=[
        P("box", [18, 0.6, 26], [0, 0.3, 0], "#8ecae6"),
        P("box", [12, 0.2, 4], [0, 0.7, -8], "#ffffff", collide=False)], size=12, fill=0.4,
        flavor="ㄅㄆㄇ寫得好整齊的作業簿。")
    item("hm_bento", "便當盒", "Lunch Box", "學校", [20, 7, 13], parts=[
        P("box", [20, 6, 13], [0, 3, 0], "#adb5bd"),
        P("box", [21, 2, 14], [0, 6.5, 0], "#e63946", collide=False)], fill=0.45)
    item("hm_water_bottle", "水壺", "Water Bottle", "學校", [8, 22, 8], parts=[
        P("cylinder", [8, 19, 8], [0, 9.5, 0], "#90e0ef", tint=True),
        P("cylinder", [6, 3, 6], [0, 20.5, 0], "#ffffff", collide=False)],
        colors=["#90e0ef", "#ffafcc", "#caffbf"], fill=0.5)


def write_items():
    define()
    ids = [d["id"] for d in ITEMS]
    assert len(ids) == len(set(ids)), "物件 id 重複"
    ITEMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "_note": "第 1 關「槿寶的家」（宜蘭冬山鄉的單層平房）專用物件，由 tools/levels/home_items.py 產生，"
                 "請改腳本後重新執行 tools/levels/build_dongshan_home.py，不要直接改這個檔案。",
        "items": ITEMS,
    }
    ITEMS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")
    print(f"[home_items] {ITEMS_PATH.name}：{len(ITEMS)} 種物件")
    return {d["id"]: d for d in ITEMS}


if __name__ == "__main__":
    write_items()
