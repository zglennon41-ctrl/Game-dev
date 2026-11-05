## Per-player settings kept between sessions: timing calibration and the beat window.
extends Node

const PATH := "user://settings.cfg"
var cfg := ConfigFile.new()

func _init() -> void:
	cfg.load(PATH)

func calibration() -> float:
	return float(cfg.get_value("timing", "calibration_ms", 0.0))

func save_calibration(ms: float) -> void:
	cfg.set_value("timing", "calibration_ms", ms)
	cfg.save(PATH)

func window_ms() -> float:
	return float(cfg.get_value("timing", "window_ms", Data.beat_window_ms(Data.room["line"])))

func save_window(ms: float) -> void:
	cfg.set_value("timing", "window_ms", ms)
	cfg.save(PATH)
