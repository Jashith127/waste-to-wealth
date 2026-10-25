"""Render any station's layers (art-bible §6.2) from its .blend, by collection name.

Run:  blender -b art/blender/<file>.blend --python art/scripts/render_station.py [-- options]
Options:
  --draft            quarter samples (quick looks; never ship)
  --fast             half samples (denoised; for big plates against a deadline)
  --only a,b         render only these outputs (names as below)
  --preset night     re-light with another rig preset; outputs get a _night suffix
  --power-cut        hide everything tagged ["practical"] (shop lights and lamps): the grid is down
Outputs to art/build/renders/<station>/ (never saves the .blend):
  bg.png                     SET + PROPS; every FX off; the idle pose of each character casts its shadow
  bg_fx_<name>.png           the same with FX_<name> on (pack_layers.py turns the difference into fx_<name>)
  <char>_<pose>.png          each CHAR_<char>_<pose>; every other object is a holdout
  <prop>.png                 each PROP_<prop>, lit by the set, cut by what is in front
  <prop>_shadow.png          its contact shadow on the catcher tagged ["shadow_catcher"]
  anchors.json               screen anchors written by the build script
Then: python tools/pack_layers.py <station>
"""
import sys
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
    """Render only the screen rectangle these objects cover (a sprite layer is mostly empty frame).
    The image keeps its full size, so packing and anchors are unchanged."""
    cam, pts = scene.camera, []
    for o in objs:
        if o.type in GEOMETRY:
            pts += [world_to_camera_view(scene, cam, o.matrix_world @ Vector(c)) for c in o.bound_box]
    r = scene.render
    if not pts:
        r.use_border = False
        return
    r.use_border, r.use_crop_to_border = True, False
    r.border_min_x = max(0.0, min(p.x for p in pts) - pad)
    r.border_max_x = min(1.0, max(p.x for p in pts) + pad)
    r.border_min_y = max(0.0, min(p.y for p in pts) - pad)
    r.border_max_y = min(1.0, max(p.y for p in pts) + pad)


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

    def idle_shadows(role="hidden"):
        for name, c in chars.items():
            if name.endswith("_idle"):
                show(c, role)

    def render(name, samples, only=None):
        name = name + SUFFIX
        if ONLY and name not in ONLY:
            return
        if only:
            border(scene, only)
        else:
            scene.render.use_border = False
        scene.cycles.samples = max(16, samples // 4) if DRAFT else max(32, samples // 2) if FAST else samples
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"[render] {name}", flush=True)

    reset(); idle_shadows(); render("bg", 128)
    for name, c in fx.items():
        reset(); idle_shadows(); show(c); render(f"bg_fx_{name}", 128)

    for name, c in chars.items():
        reset(); show(c); holdout(env)
        for other, oc in chars.items():
            if other.endswith("_idle") and other.split("_")[0] != name.split("_")[0]:
                show(oc, "holdout")
        render(name, 96, list(c.all_objects))

    for name, c in props.items():
        geometry = objects(c)
        catcher = [o for o in geometry if o.get("shadow_catcher")]
        body = [o for o in geometry if not o.get("shadow_catcher")]
        reset(); show(c); holdout(env); idle_shadows("holdout")
        for o in catcher:
            o.hide_render = True
        render(name, 96, body)
        if catcher:
            reset(); show(c); holdout(env); idle_shadows("holdout")
            for o in body:
                geo.set_render_role(o, "hidden")
            for o in catcher:
                geo.set_render_role(o, "catcher")
            for o in env:
                o.visible_shadow = False
            render(f"{name}_shadow", 96, catcher)

    (out / "anchors.json").write_text(scene["anchors"], encoding="utf-8")
    print("[anchors]", scene["anchors"], flush=True)


if __name__ == "__main__":
    main()
