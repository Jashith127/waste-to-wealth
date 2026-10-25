"""Station 1: render the layered PNGs (art-bible §6.2) from art/blender/s01_stall.blend.

Run:  blender -b art/blender/s01_stall.blend --python art/scripts/s01_render.py [-- --draft]
Writes art/build/renders/s01/<pass>.png and anchors.json. Never saves the .blend.
Then run `python tools/pack_layers.py s01` to crop them into public/assets/stations/s01/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import bpy  # noqa: E402

import geo  # noqa: E402
import rig  # noqa: E402
import safety  # noqa: E402

OUT = safety.guard(safety.ART / "build" / "renders" / "s01")
DRAFT = "--draft" in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
POSES = ("idle", "up", "down")


def objects_in(name):
    col = bpy.data.collections[name]
    return [o for o in col.all_objects if o.type in {"MESH", "CURVE"}]


def lights_in(name):
    return [o for o in bpy.data.collections[name].all_objects if o.type == "LIGHT"]


def reset(objs):
    for o in objs:
        o.hide_render = False
        geo.set_render_role(o, "normal")
        o.visible_shadow = True


def hide(objs):
    for o in objs:
        o.hide_render = True


def role(objs, r):
    for o in objs:
        geo.set_render_role(o, r)


def render(name, samples):
    if ONLY and name not in ONLY:
        return
    scene = bpy.context.scene
    scene.cycles.samples = max(16, samples // 4) if DRAFT else samples
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[render] {name}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = objects_in("SET") + objects_in("PROPS")
    kilo = [o for o in objects_in("KILO") if o.name != "KILO_shadow_catcher"]
    catcher = bpy.data.objects["KILO_shadow_catcher"]
    glow = objects_in("FRIDGE_GLOW") + lights_in("FRIDGE_GLOW")
    riyaz = {p: objects_in(f"RIYAZ_{p}") for p in POSES}
    everything = env + kilo + [catcher] + [o for g in riyaz.values() for o in g] + objects_in("FRIDGE_GLOW")

    def base():
        reset(everything)
        hide(kilo + [catcher])
        hide(glow)
        for p in POSES:
            hide(riyaz[p])

    # 1, 2. backgrounds: fridge light off / on. Riyaz casts his shadow but is not seen.
    for state in ("off", "on"):
        base()
        for o in riyaz["idle"]:
            o.hide_render = False
        role(riyaz["idle"], "hidden")
        if state == "on":
            for o in glow:
                o.hide_render = False
        render(f"bg_fridge_{state}", 128)

    # 3. Riyaz sprite frames: everything else is a holdout, so whatever is in front of him cuts him.
    for p in POSES:
        base()
        for o in riyaz[p]:
            o.hide_render = False
        role(env, "holdout")
        render(f"riyaz_{p}", 96)

    # 4. the kilo on its own, lit by the set
    base()
    for o in kilo:
        o.hide_render = False
    role(env, "holdout")
    for o in riyaz["idle"]:
        o.hide_render = False
    role(riyaz["idle"], "holdout")
    render("kilo", 96)

    # 5. the kilo's contact shadow only, on a catcher over the counter top
    base()
    for o in kilo + [catcher]:
        o.hide_render = False
    role(kilo, "hidden")
    geo.set_render_role(catcher, "catcher")
    role(env, "holdout")
    for o in env:
        o.visible_shadow = False
    render("kilo_shadow", 96)

    (OUT / "anchors.json").write_text(bpy.context.scene["anchors"], encoding="utf-8")
    print("[anchors]", bpy.context.scene["anchors"])


if __name__ == "__main__":
    main()
