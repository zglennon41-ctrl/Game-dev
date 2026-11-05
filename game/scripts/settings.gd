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

# --- The character's Pattern -------------------------------------------------

func pattern() -> Dictionary:
	var p: Variant = cfg.get_value("pattern", "spec", null)
	if p is Dictionary and Data.room["pattern"]["forms"].has(p.get("form", "")):
		return p
	return Data.room["pattern"]["default"].duplicate(true)

func save_pattern(spec: Dictionary) -> void:
	cfg.set_value("pattern", "spec", spec)
	cfg.save(PATH)

## Lost to a breach: until a date (unsworn: a season) or for good (sworn).
func pattern_lost() -> bool:
	if cfg.get_value("pattern", "lost_forever", false):
		return true
	return Time.get_unix_time_from_system() < float(cfg.get_value("pattern", "lost_until", 0.0))

func pattern_lost_text() -> String:
	if cfg.get_value("pattern", "lost_forever", false):
		return "You broke a sworn Term. This Pattern is gone for good."
	if pattern_lost():
		var d := Time.get_datetime_dict_from_unix_time(int(cfg.get_value("pattern", "lost_until", 0.0)))
		return "You broke a Term. This Pattern is lost for a season, until %04d-%02d-%02d." % [d["year"], d["month"], d["day"]]
	return ""

func lose_pattern(sworn: bool) -> void:
	if sworn:
		cfg.set_value("pattern", "lost_forever", true)
	else:
		cfg.set_value("pattern", "lost_until", Time.get_unix_time_from_system() + float(Data.room["pattern"]["seasonDays"]) * 86400.0)
	cfg.save(PATH)

func restore_pattern() -> void:
	cfg.set_value("pattern", "lost_forever", false)
	cfg.set_value("pattern", "lost_until", 0.0)
	cfg.save(PATH)
