extends Node
## 音效與配樂播放器。
## 音檔放在 assets/audio，預設由 tools/audio/generate_audio.py 合成（原創暫代音），可直接以同名檔案替換。

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
}
const MUSIC := {
	"title": "res://assets/audio/music_title.wav",
	"home": "res://assets/audio/music_home.wav",
}
const POOL_SIZE := 12

var _streams: Dictionary = {}
var _pool: Array[AudioStreamPlayer] = []
var _music: AudioStreamPlayer
var _music_key := ""


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


func play(key: String, pitch := 1.0, volume_db := 0.0) -> void:
	if not _streams.has(key):
		return
	for p in _pool:
		if not p.playing:
			p.stream = _streams[key]
			p.pitch_scale = clampf(pitch, 0.25, 4.0)
			p.volume_db = volume_db + linear_to_db(maxf(float(Game.settings["sfx_volume"]), 0.001))
			p.play()
			return


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
