"""The s03 sort mini-game's items, as real models: an item studio. Builds art/blender/s03_items.blend.

Run:  blender -b --python art/scripts/items_build.py
Then: blender -b art/blender/s03_items.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s03items

Re-runnable. Destructive only to art/blender/s03_items.blend (backed up by lib/safety).

What actually comes out of a kilo of stall waste, and what gets swept in with it (SPEC-journey; the
hub only takes meat waste, sorted earns more). Each item is a ["free"] PROP_<id> layer with no set
around it, lit by the same rig as every station, but with the camera zoomed in (2.2 m across the
frame instead of 11) so a 15 cm bone is a crisp sprite. The ids are the `kind`s in s03.json:
  meat waste   bone (a bone-in offcut) and ribs (Kenney Food Kit, CC0),  liver, gut, fat, skin
  not for it   bag (a carry bag), cup (a paper tea cup), string (jute twine), paper (newspaper
               wrap), tray (a foam tray)
  and the bin  (the dustbin the rejects go into; CC0 model)
"""
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import food  # noqa: E402  (Kenney Food Kit cuts, CC0)
import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import rig  # noqa: E402
import s03_art_build as s03  # noqa: E402
import s06_build as s06  # noqa: E402  (the wet meat materials and lumpy pieces)
from mathutils import Vector  # noqa: E402

SET_DATA = {"id": "s03items", "set": {"blend": "art/blender/s03_items.blend", "lighting": "midday", "street": {"x0": -1.0, "x1": 1.0}}, "signs": []}
ORTHO = 2.2                                         # metres across the frame: close-up, not the street scale
ROW = (("bone", "ribs", "liver", "gut", "fat", "skin"), ("bag", "cup", "string", "paper", "tray", "bin"))


def slot(r, k):
    """Items sit along screen rows: (t, t) runs straight across the frame on this camera."""
    t = -0.55 + k * 0.22
    d = 0.42 * r
    return Vector((t + d, t - d, 0.0))


def materials(m):
    s06.form_materials(m)
    m.update(
        paper_cup=M.matte("MAT_paper_cup", "#F2EFE8", 0.75),
        cup_band=M.matte("MAT_cup_band", "#B5452E", 0.7),
        tea=M.plastic("MAT_tea_stain", "#7A4A24", 0.2),
        jute=M.matte("MAT_jute", "#B7A17E", 0.9),
        foam=M.matte("MAT_foam", "#F4F2EC", 0.95),
        skin_pale=s06.wet("MAT_chicken_skin", [(0.3, "#D9B49C"), (0.7, "#EED6C2")], 0.35, 0.4, 0.2, 10.0, 0.5),
        newsprint=newsprint("MAT_newsprint"),
    )


def newsprint(name):
    """Grey newsprint: columns of fine text as stripes, a faded photo block."""
    n = M.Nodes(name)
    lines = n.stripes("Z", 0.0025)
    n.link(n.mix(lines, M.rgb("#DAD5CA"), M.rgb("#B4AEA4")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.9)
    return n.mat


def bone(st, c):
    """A bone-in offcut (Kenney Food Kit, CC0, re-read as raw meat by lib/food)."""
    food.cut("BONE", "meat-raw", c, st.prop("bone", free=True), size=0.2, look="raw", rot=20)


def ribs(st, c):
    """A rib offcut (Kenney Food Kit, CC0)."""
    food.cut("RIBS", "meat-ribs", c, st.prop("ribs", free=True), size=0.2, look="raw", rot=-15)


def liver(st, c):
    m, col = st.m, st.prop("liver", free=True)
    s06.lumpy("LIVER_a", c + Vector((-0.02, 0, 0.02)), 0.075, (1.4, 1.0, 0.35), m["liver"], col, 0.25, 2)
    s06.lumpy("LIVER_b", c + Vector((0.06, 0.03, 0.02)), 0.05, (1.3, 1.0, 0.35), m["liver"], col, 0.25, 4)


def gut(st, c):
    m, col = st.m, st.prop("gut", free=True)
    pts = []
    for k in range(22):
        a, r = k * 0.55, 0.012 + k * 0.0032
        pts.append(c + Vector((math.cos(a) * r, math.sin(a) * r, 0.018 + 0.004 * math.sin(k))))
    for k in range(len(pts) - 1):
        geo.limb(f"GUT_{k}", pts[k], pts[k + 1], 0.014, 0.014, m["gut"], col, segments=10)
        geo.sphere(f"GUT_j{k}", pts[k + 1], 0.0142, (1, 1, 1), m["gut"], col, segments=10, rings=6)


def fat(st, c):
    m, col = st.m, st.prop("fat", free=True)
    rnd = random.Random(3)
    for k in range(4):
        s06.lumpy(f"FAT_{k}", c + Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.04, 0.04), 0.022)), rnd.uniform(0.028, 0.04),
                  (1.4, 1.0, 0.6), m["fat"], col, 0.5, k)


def skin(st, c):
    m, col = st.m, st.prop("skin", free=True)
    for k, (dx, dy, r) in enumerate(((-0.03, 0.0, 0.055), (0.035, 0.02, 0.045), (0.0, -0.035, 0.04))):
        s06.lumpy(f"SKIN_{k}", c + Vector((dx, dy, 0.012)), r, (1.5, 1.1, 0.18), m["skin_pale"], col, 0.9, k + 1, 20)


def bag(st, c):
    m, col = st.m, st.prop("bag", free=True)
    s06.lumpy("BAG_body", c + Vector((0, 0, 0.05)), 0.07, (1.2, 0.9, 0.75), m["bag"], col, 1.1, 2, 24)
    for k, sx in enumerate((-1, 1)):
        a = c + Vector((sx * 0.035, -0.01, 0.1))
        top = c + Vector((sx * 0.04, -0.005, 0.15))
        b = c + Vector((sx * 0.05, 0.01, 0.1))
        geo.limb(f"BAG_handle{k}a", a, top, 0.008, 0.008, m["bag"], col, segments=8)
        geo.limb(f"BAG_handle{k}b", top, b, 0.008, 0.008, m["bag"], col, segments=8)


def cup(st, c):
    m, col = st.m, st.prop("cup", free=True)
    geo.cylinder("CUP", c, 0.028, 0.075, m["paper_cup"], col, segments=24, radius2=0.038, bevel=0.003)
    geo.cylinder("CUP_band", c + Vector((0, 0, 0.03)), 0.0335, 0.016, m["cup_band"], col, segments=24, radius2=0.0352, bevel=0)
    geo.cylinder("CUP_rim", c + Vector((0, 0, 0.073)), 0.039, 0.004, m["paper_cup"], col, segments=24, bevel=0.001)
    geo.cylinder("CUP_tea", c + Vector((0, 0, 0.055)), 0.034, 0.002, m["tea"], col, segments=24, bevel=0)


def string(st, c):
    m, col = st.m, st.prop("string", free=True)
    rnd = random.Random(5)
    # a loose tangle: three overlapping loops of twine and a tail
    p = c + Vector((-0.07, 0.0, 0.006))
    for k in range(60):
        a = k * 0.42
        r = 0.035 + 0.01 * math.sin(k * 0.9)
        q = c + Vector((math.cos(a) * r + k * 0.0012 - 0.03, math.sin(a) * r * 0.8, 0.006 + 0.003 * (k % 3)))
        geo.limb(f"STRING_{k}", p, q, 0.0055, 0.0055, m["jute"], col, segments=6)
        p = q
    geo.limb("STRING_tail", p, p + Vector((0.07, -0.03, 0)), 0.0055, 0.0055, m["jute"], col, segments=6)


def paper(st, c):
    m, col = st.m, st.prop("paper", free=True)
    s06.lumpy("PAPER_ball", c + Vector((0, 0, 0.045)), 0.06, (1.3, 1.0, 0.8), m["newsprint"], col, 1.4, 3, 22)
    s06.lumpy("PAPER_flap", c + Vector((0.06, -0.02, 0.012)), 0.05, (1.4, 1.0, 0.15), m["newsprint"], col, 1.0, 1, 18)


def tray(st, c):
    m, col = st.m, st.prop("tray", free=True)
    w, d = 0.11, 0.075
    geo.box("TRAY_base", c + Vector((-w, -d, 0)), c + Vector((w, d, 0.006)), m["foam"], col, 0.003)
    for name, lo, hi in (("f", (-w, -d, 0), (w, -d + 0.008, 0.022)), ("b", (-w, d - 0.008, 0), (w, d, 0.022)),
                         ("l", (-w, -d, 0), (-w + 0.008, d, 0.022)), ("r", (w - 0.008, -d, 0), (w, d, 0.022))):
        geo.box(f"TRAY_rim{name}", c + Vector(lo), c + Vector(hi), m["foam"], col, 0.003)
    s06.lumpy("TRAY_stain", c + Vector((-0.01, 0.0, 0.006)), 0.04, (1.4, 1.0, 0.03), m["marrow"], col, 0.8, 2, 16)


def binmodel(st, c):
    """The CC0 file holds two cans: keep the plain one, nearest the model's origin."""
    import bpy
    col = st.prop("bin", free=True)
    root = kit.ph("BIN", "metal_trash_can", tuple(c), 20, 0.32, col)
    if root is None:
        return
    bpy.context.view_layer.update()
    meshes = [o for o in col.all_objects if o.type == "MESH"]
    def centre(o):
        pts = [o.matrix_world @ Vector(b) for b in o.bound_box]
        return sum(pts, Vector()) / 8
    xs = sorted(centre(o).x for o in meshes)
    keep_x = xs[0]                                   # the nearer can; the other sits ~0.3 m along +X
    for o in meshes:
        if centre(o).x - keep_x > 0.15:
            bpy.data.objects.remove(o)


def build():
    st = s03.ArtStation(SET_DATA)
    s03.set_materials(st.m)
    kit.kit_materials(st.m)
    materials(st.m)
    makers = dict(bone=bone, ribs=ribs, liver=liver, gut=gut, fat=fat, skin=skin, bag=bag, cup=cup, string=string,
                  paper=paper, tray=tray, bin=binmodel)
    for r, row in enumerate(ROW):
        for k, name in enumerate(row):
            makers[name](st, slot(r, k))
            st.anchor(f"{name}_centre", slot(r, k) + Vector((0, 0, 0.04)))
    rig.ORTHO_SCALE = ORTHO
    st.finish((0.0, 0.0, 0.05))


if __name__ == "__main__":
    build()
