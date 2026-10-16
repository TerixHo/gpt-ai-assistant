extends Node
## 在暫停狀態下仍會執行，負責偵測暫停鍵。

signal toggled


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		toggled.emit()
		get_viewport().set_input_as_handled()
