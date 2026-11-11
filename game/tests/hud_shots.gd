## Pictures of the play screen's words, to look at: the step's panel open, folded to its plate,
## with a note, and as a gamepad sees it. Only the interface is drawn (over a flat ground the
## colour of a lit yard), so it is quick even where the 3D is slow.
##   godot --path . res://game/tests/hud_shots.tscn -- --shots=DIR [--weapon=bow]
extends Node

var hud := Hud.new()
var dir := "user://hud_shots"

func _ready() -> void:
	Style.apply_global()
	for a in OS.get_cmdline_user_args():
		var kv := String(a).trim_prefix("--").split("=", true, 1)
		if kv[0] == "shots" and kv.size() > 1:
			dir = kv[1]
	DirAccess.make_dir_recursive_absolute(dir)
	var ground := ColorRect.new()
	ground.color = Color(0.36, 0.33, 0.29)
	ground.set_anchors_preset(Control.PRESET_FULL_RECT)
	var layer := CanvasLayer.new()
	layer.layer = -1
	add_child(layer)
	layer.add_child(ground)
	add_child(hud)
	var h := Fight.default_hero()
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--weapon="):
			h = h.duplicate(true)
			h["weapon"] = String(a).trim_prefix("--weapon=")
	var f := Fight.new({ "hero": h, "beast": "millstone", "passive": true })
	hud.configure(f, "Amos Tull")
	hud.screen.visible = false
	var lesson: Dictionary = Data.by_id(Data.academy["lessons"], "hold")
	var st: Dictionary = lesson["steps"][2]
	hud.set_prompt("3/4 · %s" % st["title"], String(st["text"]))
	hud.set_prompt_status("", "0 / 3")
	await _frames(f, 8)
	await _shot("1-step-open")
	# the first parry, and the time to read it: it folds
	hud.set_prompt_status("", "1 / 3")
	hud._prompt_min_until = 0.0
	await _frames(f, 30)
	await _shot("2-step-folded")
	hud.set_prompt_status("Blocked: you held the guard too early. Tap it just as the bite lands.", "1 / 3")
	await _frames(f, 4)
	await _shot("3-folded-with-note")
	hud.show_prompt_again()
	await _frames(f, 20)
	await _shot("4-step-again")
	hud.set_device(true)
	hud._play_time = 0.0
	await _frames(f, 4)
	await _shot("5-gamepad")
	get_tree().quit()

func _frames(f: Fight, n: int) -> void:
	for i in n:
		hud.update_play(f, "", "the practice yard  ·  warded", true)
		await get_tree().process_frame

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [dir, name])
	print("SHOT %s/%s.png" % [dir, name])
