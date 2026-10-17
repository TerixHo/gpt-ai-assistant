extends Node
## 音效與配樂播放器。
## 音檔放在 assets/audio，由 tools/audio/generate_music.py（配樂）與 generate_sfx.py（音效、歡呼語音）合成，
## 全部原創；可直接以同名檔案替換。

const SOUNDS := {
	"pickup": "res://assets/audio/pickup.wav",
	"pickup_big": "res://assets/audio/pickup_big.wav",
	"bump": "res://assets/audio/bump.wav",
	"drop": "res://assets/audio/drop.wav",
	"tick": "res://assets/audio/tick.wav",
	"goal": "res://assets/audio/goal.wav",
	"timeup": "res://assets/audio/timeup.wav",
	"dash": "res://assets/audio/dash.wav",
	"ui": "res://assets/audio/ui.wav",
	"gate": "res://assets/audio/gate.wav",
	"meow": "res://assets/audio/meow.wav",
	"woof": "res://assets/audio/woof.wav",
	"cheer": "res://assets/audio/cheer.wav",
	"pop": "res://assets/audio/pop.wav",
	"ding": "res://assets/audio/ding.wav",
	"chirp": "res://assets/audio/chirp.wav",
	"jump": "res://assets/audio/jump.wav",
	"turn": "res://assets/audio/turn.wav",
	"charge_level": "res://assets/audio/charge_level.wav",
	"flame": "res://assets/audio/flame.wav",
	"launch": "res://assets/audio/launch.wav",
	"double_jump": "res://assets/audio/double_jump.wav",
	"flip": "res://assets/audio/flip.wav",
	"rescue": "res://assets/audio/rescue.wav",
	"impact_big": "res://assets/audio/impact_big.wav",
	"burst_drop": "res://assets/audio/burst_drop.wav",
	"milestone": "res://assets/audio/milestone.wav",
	"petal": "res://assets/audio/petal.wav",
	"splash": "res://assets/audio/splash.wav",
	"cheer_gin_1": "res://assets/audio/cheer_gin_1.wav",
	"cheer_gin_2": "res://assets/audio/cheer_gin_2.wav",
	"cheer_gin_3": "res://assets/audio/cheer_gin_3.wav",
	# 物件專屬音：items.json 的 "sfx" 欄位指定，黏到時由 play_item() 播放
	"orange": "res://assets/audio/orange.wav",
	"curry": "res://assets/audio/curry.wav",
	"snack": "res://assets/audio/snack.wav",
	"crayon": "res://assets/audio/crayon.wav",
	"yarn": "res://assets/audio/yarn.wav",
	"bug": "res://assets/audio/bug.wav",
	"duck": "res://assets/audio/duck.wav",
	"chicken": "res://assets/audio/chicken.wav",
	"frog": "res://assets/audio/frog.wav",
	"bike_bell": "res://assets/audio/bike_bell.wav",
	"car_horn": "res://assets/audio/car_horn.wav",
	"train_horn": "res://assets/audio/train_horn.wav",
	"school_bell": "res://assets/audio/school_bell.wav",
	"bubble": "res://assets/audio/bubble.wav",
	"squeak": "res://assets/audio/squeak.wav",
	"bell": "res://assets/audio/bell.wav",
}
## 需要持續循環的音效（集氣的旋轉聲）
const LOOPS := {
	"charge_loop": "res://assets/audio/charge_loop.wav",
}
## 配樂：紅白機晶片音樂風格（tools/audio/generate_music.py 合成，原創）
const MUSIC := {
	"title": "res://assets/audio/music_title.wav",
	"home": "res://assets/audio/music_home.wav",
	"street": "res://assets/audio/music_street.wav",
	"school": "res://assets/audio/music_school.wav",
	"station": "res://assets/audio/music_station.wav",
}
## 成長里程碑的歡呼「Yooo～ GIN Gin～」三個版本，隨機挑一個
const CHEERS := ["cheer_gin_1", "cheer_gin_2", "cheer_gin_3"]
const POOL_SIZE := 16

var _streams: Dictionary = {}
var _pool: Array[AudioStreamPlayer] = []
var _music: AudioStreamPlayer
var _music_key := ""
var _loop: AudioStreamPlayer
## 標題畫面的示範關卡在背景跑時，關掉場景裡的音效（貓叫、黏東西）
var world_muted := false
# 音高微調用自己的亂數，不影響遊戲邏輯共用的亂數（自動測試需要可重現）
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	for key in SOUNDS:
		if ResourceLoader.exists(SOUNDS[key]):
			_streams[key] = load(SOUNDS[key])
	for i in POOL_SIZE:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_pool.append(p)
	_music = AudioStreamPlayer.new()
	add_child(_music)
	_loop = AudioStreamPlayer.new()
	add_child(_loop)


## 結束遊戲時停掉所有聲音，避免還在播放的音檔在關閉時被回報為資源洩漏。
func _exit_tree() -> void:
	for p in _pool:
		p.stop()
		p.stream = null
	_music.stop()
	_music.stream = null
	_loop.stop()
	_loop.stream = null
	# 停止要等音訊執行緒下一次混音才真正釋放，結束前稍等一下
	OS.delay_msec(40)


func play(key: String, pitch := 1.0, volume_db := 0.0) -> void:
	if not _streams.has(key) or (world_muted and key != "ui"):
		return
	for p in _pool:
		if not p.playing:
			p.stream = _streams[key]
			p.pitch_scale = clampf(pitch, 0.25, 4.0)
			p.volume_db = volume_db + linear_to_db(maxf(float(Game.settings["sfx_volume"]), 0.001))
			p.play()
			return


## 每次音高稍微不同，連續黏東西時聽起來比較生動。
func play_varied(key: String, pitch := 1.0, spread := 0.05, volume_db := 0.0) -> void:
	play(key, pitch * (1.0 + _rng.randf_range(-spread, spread)), volume_db)


## 物件專屬音：def 有 "sfx" 欄位且有該音檔就播放（音高小幅變化）並回傳 true，否則回傳 false。
func play_item(def: Dictionary, pitch := 1.0) -> bool:
	var key := str(def.get("sfx", ""))
	if key.is_empty() or not _streams.has(key):
		return false
	play_varied(key, pitch, 0.04)
	return true


## 成長里程碑：槿寶歡呼（三個版本隨機挑一個），同時播放小號角。
func play_cheer() -> void:
	play(CHEERS[_rng.randi() % CHEERS.size()], 1.0, 1.0)
	play("milestone", 1.0, -5.0)


func start_loop(key: String, pitch := 1.0) -> void:
	var path: String = LOOPS.get(key, "")
	if path.is_empty() or not ResourceLoader.exists(path):
		return
	var stream: AudioStream = load(path)
	if stream is AudioStreamWAV:
		var wav := stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = int(wav.get_length() * wav.mix_rate)
	_loop.stream = stream
	_loop.pitch_scale = pitch
	_loop.volume_db = linear_to_db(maxf(float(Game.settings["sfx_volume"]), 0.001)) - 4.0
	_loop.play()


func set_loop_pitch(pitch: float) -> void:
	_loop.pitch_scale = clampf(pitch, 0.25, 4.0)


func stop_loop() -> void:
	_loop.stop()


func play_music(key: String) -> void:
	if key == _music_key and _music.playing:
		return
	_music_key = key
	var path: String = MUSIC.get(key, "")
	if path.is_empty() or not ResourceLoader.exists(path):
		_music.stop()
		return
	var stream: AudioStream = load(path)
	if stream is AudioStreamWAV:
		var wav := stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = int(wav.get_length() * wav.mix_rate)
	_music.stream = stream
	_music.volume_db = linear_to_db(maxf(float(Game.settings["music_volume"]), 0.001))
	_music.play()


func stop_music() -> void:
	_music_key = ""
	_music.stop()
