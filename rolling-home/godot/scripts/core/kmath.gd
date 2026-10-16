class_name KMath
## 塊球相關的純函式（無狀態，方便單元測試與調參）。
## 單位一律為公分；世界座標 1 單位 = 1 公分。

const LAYER_WORLD := 1      ## 地板、牆、門檻等不可吸附的建物
const LAYER_ITEM := 2       ## 所有可吸附或可推擠的物件（含家具）
const LAYER_KATAMARI := 4   ## 塊球本體
const LAYER_GATE := 8       ## 尺寸門檻（達到尺寸後消失的阻擋物）


static func sphere_volume(diameter: float) -> float:
	return PI / 6.0 * diameter * diameter * diameter


static func diameter_from_volume(volume: float) -> float:
	return pow(maxf(volume, 0.0) * 6.0 / PI, 1.0 / 3.0)


## 物件併入塊球後增加的體積：以物件尺寸為直徑的球體 × 填充係數。
static func item_volume(size_cm: float, fill: float) -> float:
	return sphere_volume(size_cm) * fill


## 吸附判定：物件尺寸小於「塊球直徑 × 比例」才黏得起來。
static func can_pick(item_size_cm: float, diameter_cm: float, ratio: float) -> bool:
	return item_size_cm <= diameter_cm * ratio


## 原作風格的尺寸字串：未滿 1 公尺顯示「12cm3mm」（整數公分顯示「10cm」），滿 1 公尺顯示「1m24cm」。
static func format_size(cm: float) -> String:
	var mm_total := int(round(cm * 10.0))
	if mm_total < 10:
		return "%dmm" % mm_total
	if mm_total < 1000:
		if mm_total % 10 == 0:
			return "%dcm" % (mm_total / 10)
		return "%dcm%dmm" % [mm_total / 10, mm_total % 10]
	var m := mm_total / 1000
	var rest_cm := (mm_total % 1000) / 10
	if rest_cm == 0:
		return "%dm" % m
	return "%dm%dcm" % [m, rest_cm]


static func format_time(seconds: float) -> String:
	var s := maxi(int(ceil(seconds)), 0)
	return "%d:%02d" % [s / 60, s % 60]


static func color(hex: String, fallback := Color(0.8, 0.8, 0.8)) -> Color:
	if hex.is_empty() or not Color.html_is_valid(hex):
		return fallback
	return Color.html(hex)


static func vec3(arr: Variant, fallback := Vector3.ZERO) -> Vector3:
	if arr is Array and arr.size() >= 3:
		return Vector3(float(arr[0]), float(arr[1]), float(arr[2]))
	return fallback
