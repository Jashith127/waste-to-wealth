"""Build a fast-review, final-quality sheet of the five rigged human archetypes.

Run:
  blender -b --python art/scripts/character_sheet.py

The resulting .blend keeps one independently named armature per character.  It is the reusable
source for the station figures; the PNG is a presentation render, not a game sprite.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import bpy
from mathutils import Vector

import geo
import materials as M
import people
import safety


OUT_BLEND = safety.ART / "blender" / "human_model_collection.blend"
OUT_RENDER = safety.ART / "build" / "renders" / "humans" / "human_model_collection.png"


def label(text, at, mat):
    curve = bpy.data.curves.new(f"LABEL_{text}", "FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.size = 0.18
    curve.extrude = 0.002
    obj = bpy.data.objects.new(f"LABEL_{text}", curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at
    obj.rotation_euler = (1.5708, 0, 0)
    obj.data.materials.append(mat)


def camera():
    data = bpy.data.cameras.new("CAM_character_sheet")
    data.type = "ORTHO"
    data.ortho_scale = 5.9
    cam = bpy.data.objects.new("CAM_character_sheet", data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, -16, 2.25)
    cam.rotation_euler = (Vector((0, 0, 1.15)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam


def lights():
    def area(name, loc, energy, size, colour):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.shape, d.size, d.color = energy, "DISK", size, colour
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 1.0)) - o.location).to_track_quat("-Z", "Y").to_euler()
    area("KEY_soft", (-4, -6, 6), 900, 5, (1.0, 0.82, 0.66))
    area("FILL_soft", (4, -4, 4), 600, 4, (0.67, 0.81, 1.0))
    area("RIM_soft", (0, 3, 6), 850, 3, (1.0, 0.96, 0.86))


def build():
    safety.fresh_scene()
    scene = bpy.context.scene
    # EEVEE gives the fast iteration pass; the same collection remains ready for Cycles finals.
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = (2400, 1350)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.world = bpy.data.worlds.new("WORLD_character_sheet")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.035, 0.045, 0.060, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    scene.view_settings.look = "AgX - Medium High Contrast"

    floor = M.matte("MAT_sheet_floor", "#253046", 0.6)
    ink = M.matte("MAT_sheet_ink", "#E9E1D1", 0.55)
    geo.box("STAGE", (-3.35, -0.15, -0.10), (3.35, 0.85, 0.0), floor, None, 0.03)
    specs = [
        ("Vendor", "vendor", dict(apron="#E8DFCA", cap="#EFE8D7", shirt=("#7FA08D", "#B7C7B8", 0.028), trousers="#30333A")),
        ("Industrial worker", "worker", dict(shirt="#334D78", trousers="#2A3B60", cap="#EAE8E0")),
        ("Loader", "loader", dict(shirt="#53677F", trousers="#343942", towel="#C84B43")),
        ("Butcher", "butcher", dict(apron="#E8DFCA", cap="#F0EBDE", shirt=("#317AA1", "#E9E4D2", 0.028), trousers="#303238")),
        ("Office attendant", "attendant", dict(shirt="#8B8C91", trousers="#30323A")),
    ]
    xs = (-2.55, -1.27, 0, 1.27, 2.55)
    for (title, look, kwargs), x in zip(specs, xs):
        col = geo.collection(f"CHAR_{look.upper()}")
        mats = people.costume_materials(look, look=look, **kwargs)
        # relaxed A-pose reads better than a perfectly horizontal T-pose while preserving rig access.
        people.figure(look.upper(), (x, 0, 0), 0, mats, (-0.56, 0.0, 1.18), (0.56, 0.0, 1.18), col)
        label(title, (x, -0.32, -0.02), ink)
    camera()
    lights()
    OUT_RENDER.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(safety.guard(OUT_RENDER))
    bpy.ops.wm.save_as_mainfile(filepath=str(safety.guard(OUT_BLEND)), compress=True)
    bpy.ops.render.render(write_still=True)
    print(f"[render] {OUT_RENDER}")


if __name__ == "__main__":
    build()
