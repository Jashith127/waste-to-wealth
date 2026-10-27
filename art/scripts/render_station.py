"""Render any station's layers (art-bible §6.2) from its .blend, by collection name.

Run:  blender -b art/blender/<file>.blend --python art/scripts/render_station.py [-- options]
Options:
  --draft            quarter samples (quick looks; never ship)
  --fast             half samples (denoised; for big plates against a deadline)
  --only a,b         render only these outputs (names as below; wildcards work: --only "riyaz_*,ped*")
  --preset night     re-light with another rig preset; outputs get a _night suffix
  --power-cut        hide everything tagged ["practical"] (shop lights and lamps): the grid is down
Outputs to art/build/renders/<station>/ (never saves the .blend):
  bg.png                     SET + PROPS; every FX off; the idle pose of each character casts its shadow
  bg_fx_<name>.png           the same with FX_<name> on (pack_layers.py turns the difference into fx_<name>)
  <char>_<pose>.png          each CHAR_<char>_<pose>; every other object is a holdout
  <prop>.png                 each PROP_<prop>, lit by the set, cut by what is in front
  <prop>_shadow.png          its contact shadow on the catcher tagged ["shadow_catcher"]
  occ_<name>.png             set objects tagged ["occ"] = name, alone and cut by what is in front: drawn
                             over a walker that passes behind them (they stay in bg.png too)
  anchors.json               screen anchors written by the build script
  world.json                 world-space data the build script stored in scene["world"], if any
  _offsets/<name>.json       a sprite layer is saved cropped to its border; this is where its top-left
                             sits in the frame (pack_layers.py puts it back)
  atlas_free.png             every free CHAR_ frame in one render (see _atlas/<name>.json)
A CHAR_ or PROP_ collection tagged ["free"] moves anywhere in the game, so it is rendered with no set in
front of it and no other figure, only a hidden paving floor for its bounce light. They render last, in
their own view layer (just them, that floor and the lights), and free CHAR_ frames all go into one atlas
render: each frame is moved (in whole pixels) to its own cell of a tight grid and to its own depth along
the view (so no shadow reaches a neighbour), and _atlas/<name>.json says where pack_layers.py cuts it out
and puts it back. One render of ~100 s02 frames replaces ~100 renders of ~3 s each.
Then: python tools/pack_layers.py <station>
"""
import fnmatch
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

import geo  # noqa: E402
import rig  # noqa: E402
import safety  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DRAFT = "--draft" in ARGS
FAST = "--fast" in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
PRESET = ARGS[ARGS.index("--preset") + 1] if "--preset" in ARGS else None
SUFFIX = f"_{PRESET}" if PRESET else ""
POWER_CUT = "--power-cut" in ARGS
GEOMETRY = {"MESH", "CURVE"}


def objects(col, kinds=GEOMETRY):
    return [o for o in col.all_objects if o.type in kinds]


def speed_up(scene):
    """Render settings that cost no visible quality here: keep the BVH between layers, stop sampling
    pixels that have settled, fewer bounces than Cycles' defaults, denoise on the GPU."""
    scene.render.use_persistent_data = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 6
    scene.cycles.transparent_max_bounces = 8
    scene.cycles.caustics_reflective = scene.cycles.caustics_refractive = False
    if hasattr(scene.cycles, "denoising_use_gpu"):
        scene.cycles.denoising_use_gpu = True


def border(scene, objs, pad=0.02):
    """Render only the screen rectangle these objects cover (a sprite layer is mostly empty frame),
    snapped to whole pixels, and save only that rectangle. Returns its top-left in frame pixels."""
    cam, pts = scene.camera, []
    for o in objs:
        if o.type in GEOMETRY:
            pts += [world_to_camera_view(scene, cam, o.matrix_world @ Vector(c)) for c in o.bound_box]
    r = scene.render
    if not pts:
        r.use_border = False
        return None
    w, h = r.resolution_x, r.resolution_y
    x0 = max(0, math.floor((min(p.x for p in pts) - pad) * w))
    x1 = min(w, math.ceil((max(p.x for p in pts) + pad) * w))
    y0 = max(0, math.floor((min(p.y for p in pts) - pad) * h))
    y1 = min(h, math.ceil((max(p.y for p in pts) + pad) * h))
    r.use_border, r.use_crop_to_border = True, True
    # a quarter pixel inside each edge, then where Blender puts the crop (it truncates to whole pixels;
    # y runs up from the bottom), so the saved crop's top-left is exact
    r.border_min_x, r.border_max_x = (x0 + 0.25) / w, (x1 - 0.25) / w
    r.border_min_y, r.border_max_y = (y0 + 0.25) / h, (y1 - 0.25) / h
    return int(r.border_min_x * w), h - int(r.border_max_y * h)


ATLAS_DEPTH = 15.0             # m along the view between neighbouring frames: an orthographic camera does
                               # not see the move, but no shadow ray from one frame gets near another


def atlas(scene, cols, out, reset, show, floor):
    """Render every free CHAR_ collection in `cols` in one image. Each frame is slid (by whole pixels on
    screen) into its own cell of a tight grid, and pushed ATLAS_DEPTH further along the view than the
    last, standing on its own hidden patch of `floor`'s paving for bounce light. The camera keeps its
    centre and px/m; the frame grows to hold the grid. Writes atlas_free_<time>.png and
    _atlas/<name>.json: the frame's box in the atlas and where that box sits in the station frame."""
    cam, r = scene.camera, scene.render
    w0, h0, ortho0, clip0 = r.resolution_x, r.resolution_y, cam.data.ortho_scale, cam.data.clip_end
    ppm = w0 / ortho0
    boxes = {}
    for name, c in cols.items():
        pts = [world_to_camera_view(scene, cam, o.matrix_world @ Vector(v)) for o in c.all_objects
               if o.type in GEOMETRY for v in o.bound_box]
        x0, x1 = math.floor(min(p.x for p in pts) * w0) - 4, math.ceil(max(p.x for p in pts) * w0) + 4
        y0, y1 = math.floor((1 - max(p.y for p in pts)) * h0) - 4, math.ceil((1 - min(p.y for p in pts)) * h0) + 4
        boxes[name] = (x0, y0, x1, y1)
    cw = max(b[2] - b[0] for b in boxes.values())
    ch = max(b[3] - b[1] for b in boxes.values())
    ncol = max(1, round(math.sqrt(len(cols) * ch / cw)))
    w, h = ncol * cw, math.ceil(len(cols) / ncol) * ch
    w, h = w + (w - w0) % 2, h + (h - h0) % 2             # an even margin round the old frame: whole pixels
    dx, dy = (w - w0) // 2, (h - h0) // 2
    # screen right is world (1, 1)/sqrt 2 at ppm px/m; screen down is world (1, -1)/sqrt 2 at ppm/2 px/m
    right, down = Vector((1, 1, 0)).normalized(), Vector((1, -1, 0)).normalized()
    view = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    (out / "_atlas").mkdir(exist_ok=True)
    moved, cells, patches = [], {}, []
    reset()
    floor.hide_render = True
    for i, (name, c) in enumerate(cols.items()):
        x0, y0, x1, y1 = boxes[name]
        cx, cy = (i % ncol) * cw, (i // ncol) * ch
        sx, sy = cx - (x0 + dx), cy - (y0 + dy)            # whole pixels
        shift = right * (sx / ppm) + down * (sy / (ppm * 0.5)) + view * (ATLAS_DEPTH * (i + 1))
        show(c)
        for o in c.all_objects:
            if o.parent is None:
                moved.append((o, o.location.copy()))
                o.location += shift
        feet = next(o for o in c.all_objects if o.parent is None and o.type == "EMPTY").location
        patch = geo.panel(f"FLOOR_patch{i}", (feet.x, feet.y, feet.z), (2.4, 2.4), "+Z", floor.active_material, floor.users_collection[0])
        geo.set_render_role(patch, "hidden")
        patches.append(patch)
        cells[name] = {"box": [cx, cy, cx + x1 - x0, cy + y1 - y0], "at": [x0, y0]}
    r.resolution_x, r.resolution_y = w, h
    cam.data.ortho_scale = w / ppm
    cam.data.clip_end = clip0 + ATLAS_DEPTH * (len(cols) + 2)
    r.use_border = False
    scene.cycles.samples = 16 if DRAFT else 32 if FAST else 64
    # named per run: an --only re-render leaves the frames it did not touch in their older atlas
    file = f"atlas_free{SUFFIX}_{time.strftime('%Y%m%d-%H%M%S')}.png"
    scene.render.filepath = str(out / file)
    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    print(f"[render] {file}: {len(cols)} frames  {time.perf_counter() - t0:.1f}s", flush=True)
    for o, loc in moved:
        o.location = loc
    for patch in patches:
        bpy.data.objects.remove(patch)
    floor.hide_render = False
    r.resolution_x, r.resolution_y, cam.data.ortho_scale, cam.data.clip_end = w0, h0, ortho0, clip0
    for name, cell in cells.items():
        (out / "_atlas" / f"{name}{SUFFIX}.json").write_text(json.dumps({"atlas": file, **cell}), encoding="utf-8")
        stale = out / f"{name}{SUFFIX}.png"                 # an older one-layer render of the same frame
        if stale.exists():
            stale.unlink()
        (out / "_offsets" / f"{name}{SUFFIX}.json").unlink(missing_ok=True)
    used = {json.loads(f.read_text(encoding="utf-8"))["atlas"] for f in (out / "_atlas").glob("*.json")}
    for old in out.glob("atlas_free*.png"):                 # atlases no frame points at any more
        if old.name not in used:
            old.unlink()


def groups(prefix):
    return {c.name[len(prefix):]: c for c in bpy.data.collections if c.name.startswith(prefix)}


def main():
    scene = bpy.context.scene
    speed_up(scene)
    sid = scene["station"]
    out = safety.guard(safety.ART / "build" / "renders" / sid)
    out.mkdir(parents=True, exist_ok=True)
    if PRESET:
        for o in [o for o in scene.objects if o.type == "LIGHT" and o.data.type == "SUN"]:
            bpy.data.objects.remove(o)
        rig.lights(PRESET)

    env = objects(bpy.data.collections["SET"]) + objects(bpy.data.collections["PROPS"])
    fx = groups("FX_")
    chars = groups("CHAR_")                      # "riyaz_idle" -> collection
    props = groups("PROP_")
    every = env + [o for c in (*fx.values(), *chars.values(), *props.values()) for o in c.all_objects]

    practicals = [o for o in scene.objects if o.get("practical")]

    def reset():
        for o in every:
            o.hide_render = False
        for o in practicals:
            if o.type in GEOMETRY:
                geo.set_render_role(o, "normal")     # (this un-hides, so it comes before the cut)
                o.visible_shadow = True
            o.hide_render = POWER_CUT
        for c in (*fx.values(), *chars.values(), *props.values()):
            for o in c.all_objects:
                o.hide_render = True

    def show(col, role="normal"):
        for o in col.all_objects:
            o.hide_render = False
            if o.type in GEOMETRY:
                geo.set_render_role(o, role)

    def holdout(objs):
        for o in objs:
            geo.set_render_role(o, "holdout")

    def release(objs):
        """A prop that travels (the s02 handcart) is not cut by dressing tagged ["sprite_clear"]: it
        is drawn over the plate, so a pedestrian beside its start spot must not clip it. Still casts."""
        for o in objs:
            if o.get("sprite_clear"):
                geo.set_render_role(o, "hidden")

    def alone(objs):
        """A free layer: the set leaves the render except the ground, which still bounces light."""
        for o in objs:
            if o.get("ground"):
                geo.set_render_role(o, "hidden")
            else:
                o.hide_render = True

    def idle_shadows(role="hidden"):
        for name, c in chars.items():
            if name.endswith("_idle"):
                show(c, role)

    def wanted(name):
        return not ONLY or any(fnmatch.fnmatchcase(name, pat) for pat in ONLY)

    offsets = out / "_offsets"
    offsets.mkdir(exist_ok=True)

    def render(name, samples, only=None):
        name = name + SUFFIX
        if not wanted(name):
            return
        at = border(scene, only) if only else None
        if at is None:
            scene.render.use_border = False
        sidecar = offsets / f"{name}.json"
        if at:
            sidecar.write_text(json.dumps(at), encoding="utf-8")
        elif sidecar.exists():
            sidecar.unlink()
        scene.cycles.samples = max(16, samples // 4) if DRAFT else max(32, samples // 2) if FAST else samples
        scene.render.filepath = str(out / f"{name}.png")
        t0 = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        print(f"[render] {name}  {time.perf_counter() - t0:.1f}s", flush=True)

    reset(); idle_shadows(); render("bg", 128)
    for name, c in fx.items():
        reset(); idle_shadows(); show(c); render(f"bg_fx_{name}", 128)

    for name, c in chars.items():
        if c.get("free"):
            continue                                 # (below, in their own view layer)
        reset(); show(c); holdout(env)
        for other, oc in chars.items():
            if other.endswith("_idle") and other.split("_")[0] != name.split("_")[0] and not oc.get("free"):
                show(oc, "holdout")
        render(name, 64, list(c.all_objects))

    occ = {}
    for o in env:
        if o.get("occ"):
            occ.setdefault(o["occ"], []).append(o)
    for name, objs in occ.items():
        reset(); idle_shadows(); holdout(env)
        for o in objs:
            geo.set_render_role(o, "normal")
        render(f"occ_{name}", 64, objs)

    def prop(name, c):
        geometry = objects(c)
        catcher = [o for o in geometry if o.get("shadow_catcher")]
        body = [o for o in geometry if not o.get("shadow_catcher")]
        def setup():
            reset(); show(c)
            if c.get("free"):
                alone(env)
            else:
                holdout(env); release(env); idle_shadows("holdout")
        setup()
        for o in catcher:
            o.hide_render = True
        render(name, 96, body)
        if catcher:
            setup()
            for o in body:
                geo.set_render_role(o, "hidden")
            for o in catcher:
                geo.set_render_role(o, "catcher")
            for o in env:
                o.visible_shadow = False
            render(f"{name}_shadow", 96, catcher)
            for o in env:
                o.visible_shadow = True

    for name, c in props.items():
        if not c.get("free"):
            prop(name, c)

    # Free layers: a view layer holding only a hidden paving floor (the lights and camera sit in the
    # scene's own collection) and the free collection(s) being rendered.
    free_chars = {n: c for n, c in chars.items() if c.get("free") and wanted(n + SUFFIX)}
    free_props = {n: c for n, c in props.items() if c.get("free") and (wanted(n + SUFFIX) or wanted(f"{n}_shadow{SUFFIX}"))}
    if free_chars or free_props:
        main_layer = scene.view_layers[0]
        floor_col = bpy.data.collections.new("FLOOR_free")
        scene.collection.children.link(floor_col)
        paving = next((o.active_material for o in env if o.get("ground") and o.active_material), None)
        floor = geo.panel("FLOOR_free", (0, 0, 0), (400, 400), "+Z", paving, floor_col)
        geo.set_render_role(floor, "hidden")             # bounces light, never seen
        layer = scene.view_layers.new("FREE")
        main_layer.use, layer.use = False, True

        def isolate(cols):
            keep = {floor_col, *cols} | {p for p in bpy.data.collections if any(c in p.children_recursive[:] for c in cols)}

            def walk(lc):
                for child in lc.children:
                    child.exclude = child.collection not in keep
                    if not child.exclude:
                        walk(child)
            walk(layer.layer_collection)

        for name, c in free_props.items():
            isolate([c])
            prop(name, c)
        if free_chars:
            isolate(list(free_chars.values()))
            atlas(scene, free_chars, out, reset, show, floor)
        main_layer.use = True

    (out / "anchors.json").write_text(scene["anchors"], encoding="utf-8")
    if "world" in scene:
        (out / "world.json").write_text(scene["world"], encoding="utf-8")
    print("[anchors]", scene["anchors"], flush=True)


if __name__ == "__main__":
    main()
