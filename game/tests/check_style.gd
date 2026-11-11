## The style check (docs/style.md): whatever is off the game's one style is a failure here.
##
##   godot --headless --path . res://game/tests/style_check.tscn        (npm run check:style)
##   ... -- --verbose     lists every material the game moves onto a ramp, not only the count
##
## It checks the style's own numbers (data/style.json), every material in the game's art, what
## the game makes of each of them, the typefaces, the ink line, and the light of every place.
## A FAIL is something off-style that the game cannot put right by itself; a NOTE is counted
## and passes (a colour the game moves onto its ramp when the material is made).
extends Node

const FOLDERS := ["academy", "wild", "weapons", "beasts", "people", "kaykit_dungeon", "quaternius", "genius/bodies", "genius/forms", "genius/parts", "genius/keepsakes", "genius/trappings"]
## A colour this far from every ramp of its class is not a shade of anything in the palette:
## the art is wrong, whatever the game does with it afterwards.
const FAR := 0.16

var failures := 0
var notes := 0
var verbose := false
var world: World

func fail(what: String) -> void:
	failures += 1
	print("  FAIL: ", what)

func note(what: String) -> void:
	notes += 1
	if verbose:
		print("  note: ", what)

func _ready() -> void:
	verbose = OS.get_cmdline_user_args().has("--verbose")
	call_deferred("_run")

func _run() -> void:
	world = World.new()
	add_child(world)
	print("The style's own numbers")
	check_data()
	print("The typefaces")
	check_type()
	print("The art's materials")
	check_art()
	print("The ink line")
	check_ink()
	print("Where the grain is laid")
	check_laid()
	print("The light of every place")
	check_places()
	print("\nstyle: %d failed, %d moved onto a ramp by the game" % [failures, notes])
	print("style: all good" if failures == 0 else "style: OFF-STYLE")
	get_tree().quit(1 if failures > 0 else 0)

# --- data/style.json ------------------------------------------------------------------------

static func warm(c: Color) -> bool:
	return Style.saturation(c) > 0.08 and (c.h < 0.2 or c.h > 0.9)

static func cool(c: Color) -> bool:
	return Style.saturation(c) > 0.05 and c.h > 0.45 and c.h < 0.78

## The grains (materials.grains and each class's own): every one named is a texture that is
## there (tools/textures.py makes them), mid-grey on the whole so that it changes no colour's
## place on its ramp; no grain is laid on strongly enough to fight the cel bands; and the
## table still says what the bodies are covered in.
func check_grains(d: Dictionary, classes: Dictionary) -> void:
	for g in Style.grain_names():
		var path := "res://game/assets/textures/detail/%s.png" % g
		if not ResourceLoader.exists(path):
			fail("a grain is named that has no texture: %s (tools/textures.py makes them)" % g)
			continue
		var img := (load(path) as Texture2D).get_image()
		if img == null or img.is_empty():
			continue
		if img.is_compressed():
			img.decompress()
		var sum := 0.0
		for y in range(0, img.get_height(), 4):
			for x in range(0, img.get_width(), 4):
				sum += img.get_pixel(x, y).r
		var mean := sum / float((img.get_width() / 4) * (img.get_height() / 4))
		# (the first seven were made a little off it, leather the furthest at 0.56, and are left as
		# the places have worn them; the grains made since are mid-grey to the hundredth)
		if absf(mean - 0.5) > 0.07:
			fail("the grain %s is not mid-grey on the whole (%.2f): it would darken or lighten everything it is laid on" % [g, mean])
	var limit := 0.7
	for cn in classes:
		if float(classes[cn].get("wear", 0.0)) > limit:
			fail("class %s wears its grain at %.2f: over %.2f it fights the cel bands" % [cn, float(classes[cn]["wear"]), limit])
	var show := float(d["materials"].get("grainFit", {}).get("show", 1.0))
	for row in d["materials"].get("grains", []):
		var what := String(row[0])
		if what.begins_with("#") and not classes.has(what.substr(1).get_slice(":", 0)):
			fail("the grain row '%s' names a class that is not there" % what)
		if float(row[3]) * show > limit + 0.0001:
			fail("the grain row '%s' lays its grain on at %.2f (with grainFit.show): over %.2f it fights the cel bands" % [what, float(row[3]) * show, limit])
		if String(row[1]) != "" and float(row[3]) > 0.0 and float(row[2]) <= 0.0:
			fail("the grain row '%s' has a grain and no scale" % what)
	for g in d["materials"].get("grainFit", {}).get("along", []):
		if not Style.grain_names().has(String(g)):
			fail("grainFit.along names a grain that nothing is covered in: %s" % g)
	# what the table is for: a body is covered in what it is, whatever its material was named
	# (and a word inside another word is not that word: steel is not an eel's hide)
	var wants := [
		["fur_dark", "wolf", "fur"], ["fur_dark", "drake", "scales"], ["feather_wing", "hawk", "feathers"],
		["stone_plate", "tortoise", "horn"], ["horn_ridge", "tortoise", "horn"], ["stone_hide", "shield", "pebble"],
		["metal_plate", "", "hammered"], ["metal_iron", "shield", "hammered"], ["metal_steel_edge", "blade", "brushed"],
		["metal_brass", "", "brushed"], ["wood_oak", "bow", "timber"], ["bark_light", "stag", "bark"],
		["leather_strap", "", "creased"], ["cloth_rag", "", "linen"], ["robe_black", "imp", "twill"], ["hair", "", "fur"],
		["mist_pale", "fog", "fog"], ["shade_smoke", "wolf", "fog"], ["void", "lurker", "fog"], ["slate_light", "", "rock"],
		["bone", "", "rock"], ["moss", "", "wool"], ["eye_gold", "wolf", ""], ["field_glow", "wolf", ""], ["nose", "wolf", ""],
		["accent_dark", "wolf", "wool"], ["stone_smooth", "", "rock"] ]
	for beside in ["accent", "accent_dark", "mark_saddle"]:
		if not Style.grain_for(beside, World.surface_of(beside), "wolf").get("beside", false):
			fail("%s should take the grain of what lies beside it, as a marking and a Path's colour do (materials.grains: beside:)" % beside)
	for w in wants:
		var cls := World.surface_of(String(w[0]))
		var got := String(Style.grain_for(String(w[0]), cls, String(w[1])).get("grain", ""))
		if got != String(w[2]):
			fail("a %s's %s should be covered in '%s' and is covered in '%s' (materials.grains: the first row that fits wins)" % [w[1] if w[1] != "" else "thing", w[0], w[2], got])

func check_data() -> void:
	var d := Style.data()
	var cap := float(d["cap"])
	for rn in d["ramps"]:
		var limit := float(d["accentCap"]) if (d["accents"] as Array).has(rn) else cap
		if (d.get("paths", []) as Array).has(rn):
			limit = float(d["pathCap"])
		var last := -1.0
		for c in Style.ramp(rn):
			if Style.saturation(c) > limit + 0.005:
				fail("ramp %s: %s is more saturated (%.2f) than its cap (%.2f)" % [rn, (c as Color).to_html(false), Style.saturation(c), limit])
			if (c as Color).v <= last:
				fail("ramp %s does not run from shadow to light at %s" % [rn, (c as Color).to_html(false)])
			last = (c as Color).v
	var classes: Dictionary = d["materials"]["classes"]
	for cn in classes:
		for rn in classes[cn]["ramps"]:
			if not d["ramps"].has(rn):
				fail("class %s names a ramp that is not there: %s" % [cn, rn])
	for pair in d["materials"]["words"]:
		for cn in String(pair[1]).split("|"):
			if not classes.has(cn):
				fail("the word '%s' names a class that is not there: %s" % [pair[0], cn])
	check_grains(d, classes)
	# the loud are loud, and the telegraph is the telegraph everywhere
	for sh in d["loud"]["shapes"]:
		if Style.saturation(Style.shape_color(sh)) < 0.1:
			fail("the %s Shape's colour is not a colour" % sh)
	if not Style.fx("telegraph").is_equal_approx(Style.telegraph()):
		fail("the telegraph's colour in effects is not the telegraph's")
	for sh in d["loud"]["shapes"]:
		if Style.fx("telegraph").is_equal_approx(Style.shape_color(sh)):
			fail("the telegraph is a Shape's colour: danger must not read as a partner's")
	if not World.C_WINDUP.is_equal_approx(Style.telegraph()):
		fail("the fight's wind-up colour is not the telegraph's")
	# light: what the moon throws on a surface is pale; every kind of place has a warm and a cool
	if Style.saturation(Style.light("moon")) > 0.24:
		fail("the moon's cast is too blue (%.2f): a wall in moonlight would be blue paint" % Style.saturation(Style.light("moon")))
	if not warm(Style.light("lamp")) or not warm(Style.light("fire")) or not cool(Style.light("moon")):
		fail("the lamp and the fire must be warm and the moon cool")
	for kind in d["lights"]["kinds"]:
		var L: Dictionary = d["lights"]["kinds"][kind]
		var temps := [String(L["key"]) == "moon", String(L["fill"]) == "moon"]
		if temps[0] == temps[1]:
			fail("the %s is keyed and filled by lights of one temperature: every place has a warm light and a cool one" % kind)
	# motion: the shares of a motion are the whole of it; the fight's own feel is inside the bounds
	var sh: Dictionary = d["motion"]["shares"]
	if absf(float(sh["anticipation"]) + float(sh["strike"]) + float(sh["settle"]) - 1.0) > 0.001:
		fail("the shares of a motion (anticipation, strike, settle) do not add to the whole")
	var feel: Dictionary = Data.room["feel"]
	var hit: Dictionary = d["motion"]["hit"]
	for k in ["hitstop", "heavyHitstop", "parryHitstop"]:
		if float(feel[k]) < float(hit["stopMin"]) or float(feel[k]) > float(hit["stopMax"]):
			fail("the fight's %s (%.2f s) is outside the style's hit-stop (%.2f to %.2f)" % [k, float(feel[k]), float(hit["stopMin"]), float(hit["stopMax"])])
	for k in ["shakeOnHit", "shakeOnHurt"]:
		if float(feel[k]) < float(hit["shakeMin"]) or float(feel[k]) > float(hit["shakeMax"]):
			fail("the fight's %s (%.2f) is outside the style's shake (%.2f to %.2f)" % [k, float(feel[k]), float(hit["shakeMin"]), float(hit["shakeMax"])])
	# the interface's own colours: text reads on a plate
	if Style.FG.get_luminance() - Style.PLATE.get_luminance() < 0.6:
		fail("the interface's text does not stand off its plate")
	# what else in data names a colour: hair, a zone's night, the creator's lights
	for hc in Data.creation.get("look", {}).get("hairColors", {}):
		var c: Array = Data.creation["look"]["hairColors"][hc]
		if not Style.on_style(Color(c[0], c[1], c[2]), "coat"):
			fail("hair colour %s is off the coat's ramps" % hc)
	for st in Data.creation.get("look", {}).get("skinTones", {}):
		var c2: Array = Data.creation["look"]["skinTones"][st]
		if not Style.on_style(Color(c2[0], c2[1], c2[2]), "skin"):
			fail("skin tone %s is more saturated than skin may be" % st)
	for z in Data.zones():
		var zl: Dictionary = z.get("light", {})
		if zl.is_empty():
			continue
		var amb := Color(zl["ambient"][0], zl["ambient"][1], zl["ambient"][2])
		var moon := Color(zl["moonColor"][0], zl["moonColor"][1], zl["moonColor"][2]) if zl.has("moonColor") else Style.light("moon")
		if cool(moon) and Style.saturation(moon) > 0.24:
			fail("zone %s: its moon is too blue (%.2f)" % [z["id"], Style.saturation(moon)])
		if Style.saturation(amb) > 0.32:
			fail("zone %s: its ambient is too coloured (%.2f)" % [z["id"], Style.saturation(amb)])

# --- the typefaces ------------------------------------------------------------------------

func check_type() -> void:
	var ty: Dictionary = Style.data()["type"]
	var allowed := [String(ty["title"]), String(ty["body"]), String(ty["ui"])]
	var dir := DirAccess.open("res://game/assets/fonts")
	for f in dir.get_files():
		if not (f.ends_with(".ttf") or f.ends_with(".otf")):
			continue
		var ok := false
		for a in allowed:
			if f.begins_with(a):
				ok = true
		if not ok:
			fail("a typeface that is not one of the three: " + f)
	# no script but the style's loads a font, or makes one of the system's
	for path in _scripts("res://game/scripts"):
		if path.ends_with("style.gd"):
			continue
		var src := FileAccess.get_file_as_string(path)
		for bad in [".ttf", ".otf", "SystemFont", "FontFile.new"]:
			if src.contains(bad):
				fail("%s reaches for a typeface of its own (%s): fonts come from Style.font()" % [path.get_file(), bad])
		# nor keeps a copy of the interface's palette
		var own := RegEx.new()
		own.compile("(?m)^const (BG|PANEL|FG|DIM|GOLD|EDGE|OFF|RED|BRASS|INK) := Color\\(")
		var hit := own.search(src)
		if hit:
			fail("%s keeps a palette of its own (%s...): the interface's colours are Style's" % [path.get_file(), hit.get_string().strip_edges()])

func _scripts(path: String) -> Array:
	var out: Array = []
	var dir := DirAccess.open(path)
	for d in dir.get_directories():
		out.append_array(_scripts(path + "/" + d))
	for f in dir.get_files():
		if f.ends_with(".gd"):
			out.append(path + "/" + f)
	return out

# --- the art ------------------------------------------------------------------------------

func check_art() -> void:
	var seen := {}
	var counts := {}
	for folder in FOLDERS:
		counts[folder] = [0, 0]
		_walk("res://game/assets/" + folder, folder, seen, counts)
	for folder in FOLDERS:
		print("  %-18s %4d materials, %3d moved onto a ramp" % [folder, counts[folder][0], counts[folder][1]])

func _walk(path: String, folder: String, seen: Dictionary, counts: Dictionary) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		return
	for d in dir.get_directories():
		_walk(path + "/" + d, folder, seen, counts)
	for f in dir.get_files():
		if not (f.ends_with(".glb") or f.ends_with(".gltf")):
			continue
		var res = load(path + "/" + f)
		if res == null or not (res is PackedScene):
			continue
		var n: Node = res.instantiate()
		add_child(n)
		var raw := {}      # mesh|surface -> the art's own material
		for m in _meshes(n):
			for i in m.mesh.get_surface_count():
				var mat: Material = m.get_active_material(i)
				if mat is StandardMaterial3D:
					raw["%d|%d" % [m.get_instance_id(), i]] = mat
		world.toonify(n)
		for m in _meshes(n):
			for i in m.mesh.get_surface_count():
				var key := "%d|%d" % [m.get_instance_id(), i]
				if not raw.has(key):
					continue
				var sm: StandardMaterial3D = raw[key]
				var made: Material = m.get_active_material(i)
				var c := sm.albedo_color
				var id := "%s|%s|%s|%s" % [folder, sm.resource_name, c.to_html(false), str(sm.albedo_texture != null)]
				if seen.has(id):
					continue
				seen[id] = true
				counts[folder][0] += 1
				_check_material(folder, f, sm, made, counts)
		remove_child(n)
		n.free()

func _meshes(n: Node) -> Array:
	var out := n.find_children("*", "MeshInstance3D", true, false)
	if n is MeshInstance3D:
		out.append(n)
	return out.filter(func(m): return (m as MeshInstance3D).mesh != null)

func _check_material(folder: String, file: String, sm: StandardMaterial3D, made: Material, counts: Dictionary) -> void:
	var name := String(sm.resource_name)
	var where := "%s/%s '%s'" % [folder, file, name]
	var c := sm.albedo_color
	var cls := Style.material_class(name, c)
	var see_through := sm.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or sm.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED or sm.blend_mode != BaseMaterial3D.BLEND_MODE_MIX
	if cls == "":
		fail("%s: its name says nothing of what it is made of (data/style.json, materials.words)" % where)
		return
	var light := cls in ["field", "lit"]
	if sm.emission_enabled and sm.emission_energy_multiplier > 0.0 and not Style.glows(cls):
		fail("%s glows and is not light: only the field and the lit may (name it field_* or *_lit)" % where)
	if see_through:
		return
	if not (made is ShaderMaterial):
		fail("%s: the game did not make a cel material of it" % where)
		return
	var t: ShaderMaterial = made
	if sm.albedo_texture != null:
		# a painted texture: the game's copy of it must be the one brought onto the ramps
		var tex: Texture2D = t.get_shader_parameter("albedo_tex")
		if t.get_shader_parameter("use_lut") == true and t.get_shader_parameter("ramp_lut") != null:
			pass      # brought over as it is drawn
		elif tex == sm.albedo_texture or not (tex is ImageTexture):
			fail("%s: its painted texture was not brought onto the ramps" % where)
		else:
			var img := (tex as ImageTexture).get_image()
			var off := 0
			for y in range(4, img.get_height(), 16):
				for x in range(4, img.get_width(), 16):
					if not Style.on_style(img.get_pixel(x, y), "mixed"):
						off += 1
			if off > 0:
				fail("%s: %d places in its painted texture are still off the ramps" % [where, off])
		return
	if light:
		return
	var limit := Style.cap_of(cls)
	var ramps: Array = Style.class_spec(cls).get("ramps", [])
	if ramps.is_empty():
		if Style.saturation(c) > limit + 0.005:
			fail("%s: %s is more saturated (%.2f) than %s may be (%.2f)" % [where, c.to_html(false), Style.saturation(c), cls, limit])
		return
	var d := Style.off_ramp(c, cls)
	if d > FAR:
		fail("%s: %s is not a shade of anything %s may be (%.2f from its nearest ramp)" % [where, c.to_html(false), cls, d])
	elif not Style.on_style(c, cls):
		counts[folder][1] += 1
		note("%s: %s moved to %s (%s)" % [where, c.to_html(false), Style.conform(c, cls).to_html(false), cls])
	# and what the game made of it is on a ramp, whatever the art said
	var made_c: Color = t.get_shader_parameter("albedo")
	if not Style.on_style(made_c, cls):
		fail("%s: the game's material is off the ramps (%s)" % [where, made_c.to_html(false)])
	if Style.saturation(made_c) > limit + 0.012:
		fail("%s: the game's material is louder than the cap (%.2f)" % [where, Style.saturation(made_c)])

# --- the ink line -------------------------------------------------------------------------

func _has_ink(n: Node) -> bool:
	for m in _meshes(n):
		var ov: Material = (m as MeshInstance3D).material_overlay
		while ov != null:
			if ov is ShaderMaterial and (ov as ShaderMaterial).shader != null and (ov as ShaderMaterial).shader.code.contains("Ink lines"):
				return true
			ov = ov.next_pass
	return false

func check_ink() -> void:
	for cat in ["people", "beasts", "genii"]:
		if Style.ink_width(cat) <= 0.0:
			fail("the living carry ink: %s have none" % cat)
	if Style.ink_width("places") > 0.0:
		fail("places carry no ink line")
	var hero := Creation.generate([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
	world.build_hero(hero)
	if not _has_ink(world._player):
		fail("the hero carries no ink line")
	if world._wolf != null and not _has_ink(world._wolf):
		fail("the beast carries no ink line")
	var form: Dictionary = Data.form(String(Data.bases()[0]["settled"]["id"]))
	var gb := world.make_form({ "form": form["id"], "silhouette": form["silhouette"], "expression": form["expression"], "features": form["features"], "instar": 1 }, Style.shape_color("anchor"))
	add_child(gb)
	if not _has_ink(gb):
		fail("a genius carries no ink line")
	gb.queue_free()

# --- where the grain is laid ------------------------------------------------------------------

## The living and the carried wear their grain in their own space, and where they have bones
## from where they lie at rest, so that it stays on them as they move; a place wears its grain
## in the world's, so that neighbouring pieces match (docs/style.md, rule 3).
func check_laid() -> void:
	var form: Dictionary = Data.form(String(Data.bases()[0]["settled"]["id"]))
	var gb := world.make_form({ "form": form["id"], "silhouette": form["silhouette"], "expression": form["expression"], "features": form["features"], "instar": 1 }, Style.shape_color("anchor"))
	add_child(gb)
	var bodies := { "the hero": world._player, "the beast": world._wolf, "a genius": gb }
	for who in bodies:
		var n: Node = bodies[who]
		if n == null:
			continue
		var grained := 0
		for m in _meshes(n):
			var mi: MeshInstance3D = m
			for i in mi.mesh.get_surface_count():
				var t := mi.get_active_material(i) as ShaderMaterial
				if t == null or t.get_shader_parameter("detail_strength") == null or float(t.get_shader_parameter("detail_strength")) <= 0.0:
					continue
				grained += 1
				if t.get_shader_parameter("detail_local") != true:
					fail("%s: the grain of %s is laid in the world's space: it would swim as the body moves" % [who, t.resource_name])
				elif world._boned(mi) and t.get_shader_parameter("use_rest") != true:
					fail("%s: %s has bones and its grain is not laid where it rests: it would slide as a limb swings" % [who, t.resource_name])
		if grained == 0:
			fail("%s wears no grain at all" % who)
	gb.queue_free()
	var wall := MeshInstance3D.new()
	var box := BoxMesh.new()
	var stone := StandardMaterial3D.new()
	stone.resource_name = "stone_wall"
	stone.albedo_color = Style.conform(Color(0.5, 0.5, 0.5), "stone")
	box.material = stone
	wall.mesh = box
	add_child(wall)
	world.toonify(wall, true)
	var laid := wall.get_active_material(0) as ShaderMaterial
	if laid == null or laid.get_shader_parameter("detail_strength") == null or float(laid.get_shader_parameter("detail_strength")) <= 0.0:
		fail("a place of stone wears no grain")
	elif laid.get_shader_parameter("detail_local") == true:
		fail("a place's grain is laid in its own space: neighbouring pieces would not match")
	wall.queue_free()

# --- the light of every place ---------------------------------------------------------------

func check_places() -> void:
	# (a zone's night is its data's, checked above with the numbers)
	var places: Array = ["cut", "stage"]
	for pid in Data.academy["places"]:
		if Data.academy["places"][pid].has("style"):
			places.append(String(pid))
	for id in places:
		var spec: Dictionary = {}
		world.set_place(id, spec)
		if _has_ink(world._place_root):
			fail("%s: a place carries an ink line" % id)
		var has_warm := false
		var has_cool := world._moon.light_energy > 0.01 and cool(world._moon.light_color)
		for l in world._place_root.find_children("*", "Light3D", true, false):
			var light: Light3D = l
			if light == world._moon or light.light_energy <= 0.01 or not light.is_visible_in_tree():
				continue
			if warm(light.light_color):
				has_warm = true
			if cool(light.light_color):
				has_cool = true
		# a pane of night seen from indoors is a cool light too
		for m in _meshes(world._place_root):
			for i in (m as MeshInstance3D).mesh.get_surface_count():
				var mat: Material = (m as MeshInstance3D).get_active_material(i)
				if not (mat is ShaderMaterial):
					continue
				var ee = (mat as ShaderMaterial).get_shader_parameter("emission_energy")
				if ee != null and float(ee) > 0.0:
					var e: Color = (mat as ShaderMaterial).get_shader_parameter("emission")
					if cool(e):
						has_cool = true
					if warm(e):
						has_warm = true
		if not has_warm:
			fail("%s has no warm light" % id)
		if not has_cool:
			fail("%s has no cool light" % id)
		print("  %-10s warm %s, cool %s" % [id, "yes" if has_warm else "NO", "yes" if has_cool else "NO"])
