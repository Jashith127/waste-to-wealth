"""Station 6 · Renderer (example), Run 2: the kilo becomes a product. Builds art/blender/s06_renderer.blend.

Run:  blender -b --python art/scripts/s06_build.py
Then: blender -b art/blender/s06_renderer.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s06

Re-runnable. Destructive only to art/blender/s06_renderer.blend (backed up by lib/safety).

The point of the station is the conversion, so the material is the hero: it rides a conveyor along
the FRONT of the set, where nothing can hide it, and each machine behind the belt drops its result
onto the belt below it. Five forms of the same kilo, left to right, each its own PROP layer the game
swaps in turn:
  form_0  the sealed blue crate from the hub, lid off: bone and offal       (intake hopper)
  form_1  crushed small, raw                                                (size reduction)
  form_2  cooked, brown and crumbly, the fat let go                         (cooker)
  form_3  a dry pressed cake, oil run off into a jug                        (screw press)
  form_4  a fine tan meal                                                   (dryer and mill)
and PROP_product: the meal in woven sacks on a pallet, the oil in a drum, at the end of the line.
A fictional plant, labelled "Renderer (example)" and "Typical process" in the game; no real
company, logo or place (truth rules).
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
import human  # noqa: E402  (low-poly rigged people, s02 on; s01 keeps lib/people)
import people  # noqa: E402
import rig  # noqa: E402
import s03_art_build as s03  # noqa: E402

SET_DATA = {"id": "s06", "set": {"blend": "art/blender/s06_renderer.blend", "lighting": "midday", "street": {"x0": -5.0, "x1": 5.0}}, "signs": []}
TARGET = (-0.5, 2.2, 1.0)
STAGE_X = (-3.55, -1.85, -0.15, 1.55, 3.2)      # one machine and one form of the kilo per stage
BELT_Y = 1.25                                    # the conveyor runs along the front
BELT_Z = 0.86                                    # its top
MACH_Y = 2.75                                    # machines stand behind it
WALL_Y = 4.4


def materials(m):
    m.update(
        plant_floor=M.plaster("MAT_plant_floor", "#7F8A80", 0.15),
        machine=M.steel("MAT_machine", "#8E989B", 0.4),
        machine_dark=M.steel("MAT_machine_dark", "#4E5558", 0.5),
        machine_paint=M.plastic("MAT_machine_paint", "#5F7A6E", 0.5),       # muted plant green
        stripe=M.plastic("MAT_offsite_stripe", "#1F5BA8", 0.5),            # the off-site blue, sparingly
        corrugated=M.shutter("MAT_corrugated", "#8C9296"),
        belt=M.matte("MAT_belt", "#2A2826", 0.7),
        tray=M.steel("MAT_tray", "#B9BDBC", 0.25),
        crate_blue=M.plastic("MAT_hub_crate", "#1F5BA8", 0.45),
        raw=M.meat("MAT_raw"),
        bone=M.matte("MAT_bone", "#E3D2BE", 0.55),
        mince=M.matte("MAT_mince", "#A2584C", 0.5),
        cooked=M.matte("MAT_cooked", "#7A5236", 0.8),
        cake=M.matte("MAT_cake", "#9A7650", 0.9),
        meal=M.matte("MAT_meal", "#B89A6E", 0.95),
        oil=M.plastic("MAT_oil", "#C98E2A", 0.1),
        sack=M.matte("MAT_meal_sack", "#D8CFB6", 0.9),
        sack_band=M.matte("MAT_sack_band", "#2E6B34", 0.8),
        pallet=M.matte("MAT_pallet", "#9C7A52", 0.8),
        oil_drum=M.steel("MAT_oil_drum", "#5E6670", 0.45),
        drum_band=M.matte("MAT_drum_band", "#D9A23A", 0.6),
        coverall=M.matte("MAT_coverall", "#4F5E6E", 0.8),
        stain=M.matte("MAT_stain", "#3E352F", 0.25),
    )


def plant(st):
    """A clean shed floor, a corrugated back wall with a window band, columns and pipe runs."""
    s, m, col = st.street, st.m, st.set
    geo.box("FLOOR", (s.x0, -0.6, -0.25), (s.x1, WALL_Y + 0.2, 0), m["plant_floor"], col, geo.BEVEL_ARCH)
    geo.box("WALL_back", (s.x0, WALL_Y, 0), (s.x1, WALL_Y + 0.2, 4.6), m["corrugated"], col, 0)
    geo.box("WALL_kick", (s.x0, WALL_Y - 0.05, 0), (s.x1, WALL_Y, 0.5), m["concrete"], col, 0.01)
    geo.box("WALL_windows", (s.x0 + 0.4, WALL_Y - 0.03, 3.3), (s.x1 - 0.4, WALL_Y, 4.1), m["window_glass"], col, 0)
    for i, x in enumerate((-4.7, -1.0, 2.6)):
        geo.box(f"COLUMN_{i}", (x - 0.12, WALL_Y - 0.25, 0), (x + 0.12, WALL_Y, 4.6), m["steel_dark"], col, 0.01)
    for i, z in enumerate((2.9, 3.1)):
        geo.cylinder(f"PIPE_{i}", (s.x0, WALL_Y - 0.15, z), 0.06, s.x1 - s.x0, m["machine_dark"], col, axis="X", bevel=0)
    # a painted walkway line along the front, and a few honest stains
    geo.box("FLOOR_line", (s.x0 + 0.2, 0.42, 0.0), (s.x1 - 0.2, 0.5, 0.003), m["flex_yellow"] if "flex_yellow" in m else m["drum_band"], col, 0)
    for i, (x, y, r) in enumerate(((-2.6, 2.0, 0.5), (0.9, 1.9, 0.4))):
        p = geo.cylinder(f"STAIN_{i}", (x, y, 0.0), r, 0.004, m["stain"], col, segments=24, bevel=0)
        p.scale = (1.6, 0.8, 1)


def belt(st):
    """The conveyor along the front: a dark belt on a steel frame, legs, a roller at each end."""
    m, col = st.m, st.set
    x0, x1 = STAGE_X[0] - 0.75, STAGE_X[-1] + 0.6
    geo.box("BELT_frame", (x0, BELT_Y - 0.36, BELT_Z - 0.12), (x1, BELT_Y + 0.36, BELT_Z - 0.03), m["machine"], col, 0.01)
    geo.box("BELT", (x0 + 0.05, BELT_Y - 0.3, BELT_Z - 0.03), (x1 - 0.05, BELT_Y + 0.3, BELT_Z), m["belt"], col, 0.005)
    for i, x in enumerate((x0, x1)):
        geo.cylinder(f"BELT_roller{i}", (x, BELT_Y - 0.33, BELT_Z - 0.07), 0.07, 0.66, m["machine_dark"], col, axis="Y", bevel=0)
    x = x0 + 0.15
    while x < x1:
        for k, dy in enumerate((-0.3, 0.3)):
            geo.box(f"BELT_leg{x:.1f}_{k}", (x - 0.03, BELT_Y + dy - 0.03, 0), (x + 0.03, BELT_Y + dy + 0.03, BELT_Z - 0.12), m["steel_dark"], col, 0)
        x += 1.4


def chute(st, name, x, z_top):
    """A steel chute from a machine's outlet to the back edge of the belt (never over it: the
    forms on the belt must stay in full view)."""
    m, col = st.m, st.set
    geo.box(f"{name}_chute", (x - 0.16, BELT_Y + 0.32, z_top - 0.05), (x + 0.16, MACH_Y - 0.38, z_top), m["machine"], col, 0.01)
    geo.box(f"{name}_lip", (x - 0.16, BELT_Y + 0.32, z_top - 0.18), (x + 0.16, BELT_Y + 0.36, z_top), m["machine"], col, 0.005)


def stripe(st, name, lo, hi):
    geo.box(name, lo, hi, st.m["stripe"], st.set, 0)


def machines(st):
    """Five machines behind the belt, each a clear silhouette of what it does (typical process)."""
    m, col = st.m, st.set
    y = MACH_Y
    # 0 intake: a tipping frame with a big square hopper, where the hub's crates are emptied
    x = STAGE_X[0]
    for k, (dx, dy) in enumerate(((-0.45, -0.4), (0.45, -0.4), (-0.45, 0.4), (0.45, 0.4))):
        geo.box(f"INTAKE_leg{k}", (x + dx - 0.05, y + dy - 0.05, 0), (x + dx + 0.05, y + dy + 0.05, 1.3), m["steel_dark"], col, 0.01)
    geo.cylinder("INTAKE_hopper", (x, y, 1.15), 0.32, 0.75, m["machine_paint"], col, radius2=0.78, segments=4)
    stripe(st, "INTAKE_stripe", (x - 0.45, y - 0.52, 1.65), (x + 0.45, y - 0.5, 1.72))
    chute(st, "INTAKE", x, 1.2)
    # 1 size reduction: a crusher box with two toothed rollers showing in its open top
    x = STAGE_X[1]
    geo.box("CRUSH_body", (x - 0.5, y - 0.45, 0), (x + 0.5, y + 0.45, 1.25), m["machine_paint"], col, 0.03)
    for k, dy in enumerate((-0.13, 0.13)):
        geo.cylinder(f"CRUSH_roller{k}", (x - 0.4, y + dy, 1.2), 0.11, 0.8, m["machine_dark"], col, axis="X", segments=12, bevel=0)
    geo.box("CRUSH_motor", (x + 0.5, y - 0.22, 0.25), (x + 0.82, y + 0.22, 0.7), m["machine_dark"], col, 0.03)
    stripe(st, "CRUSH_stripe", (x - 0.5, y - 0.47, 1.05), (x + 0.5, y - 0.45, 1.12))
    chute(st, "CRUSH", x, 0.75)
    # 2 cooking: a big jacketed drum on legs, a steam stack and a gauge
    x = STAGE_X[2]
    geo.cylinder("COOK_drum", (x - 0.7, y, 1.2), 0.62, 1.4, m["machine"], col, axis="X", segments=36)
    for k in (-0.55, 0.55):
        geo.cylinder(f"COOK_band{k}", (x + k - 0.04, y, 1.2), 0.64, 0.08, m["machine_dark"], col, axis="X", segments=36, bevel=0)
        geo.box(f"COOK_leg{k}", (x + k - 0.07, y - 0.4, 0), (x + k + 0.07, y + 0.4, 0.62), m["machine_dark"], col, 0.01)
    geo.cylinder("COOK_stack", (x + 0.25, y + 0.1, 1.75), 0.09, 1.6, m["machine"], col, segments=16)
    geo.cylinder("COOK_gauge", (x - 0.25, y - 0.63, 1.45), 0.07, 0.03, m["glass"], col, axis="Y", bevel=0)
    chute(st, "COOK", x, 0.7)
    # 3 pressing: a long screw press on a base, oil running to a drum beside it
    x = STAGE_X[3]
    geo.box("PRESS_base", (x - 0.6, y - 0.35, 0), (x + 0.6, y + 0.35, 0.75), m["machine_paint"], col, 0.03)
    geo.cylinder("PRESS_barrel", (x - 0.6, y, 0.98), 0.2, 1.2, m["machine"], col, axis="X", segments=24)
    geo.cylinder("PRESS_motor", (x + 0.6, y, 0.98), 0.24, 0.35, m["machine_dark"], col, axis="X", segments=24)
    geo.box("PRESS_trough", (x - 0.45, y - 0.5, 0.7), (x + 0.45, y - 0.36, 0.78), m["machine_dark"], col, 0.01)
    stripe(st, "PRESS_stripe", (x - 0.6, y - 0.37, 0.55), (x + 0.6, y - 0.35, 0.62))
    chute(st, "PRESS", x, 0.8)
    # 4 drying and milling: a rotary dryer feeding a hammer mill under its cyclone
    x = STAGE_X[4]
    geo.cylinder("DRY_drum", (x - 0.65, y + 0.15, 1.45), 0.42, 0.9, m["machine"], col, axis="X", segments=32)
    for k in (-0.4, 0.15):
        geo.box(f"DRY_stand{k}", (x + k - 0.06, y - 0.15, 0), (x + k + 0.06, y + 0.45, 1.05), m["steel_dark"], col, 0.01)
    geo.box("MILL_body", (x - 0.3, y - 0.35, 0), (x + 0.3, y + 0.15, 0.85), m["machine_paint"], col, 0.03)
    geo.cylinder("MILL_cyclone", (x + 0.55, y + 0.4, 1.9), 0.3, 0.75, m["machine"], col, segments=24)
    geo.cylinder("MILL_cone", (x + 0.55, y + 0.4, 1.3), 0.07, 0.6, m["machine"], col, segments=24, radius2=0.3)
    geo.limb("MILL_duct", (x, y, 0.85), (x + 0.55, y + 0.4, 2.55), 0.08, 0.08, m["machine_dark"], col)
    stripe(st, "MILL_stripe", (x - 0.3, y - 0.37, 0.6), (x + 0.3, y - 0.35, 0.67))
    chute(st, "MILL", x, 0.6)
    for i, x in enumerate(STAGE_X):
        st.anchor(f"machine_{i}", (x, MACH_Y - 0.5, 1.6))


FORM_SCALE = 1.5                                 # the forms are the hero: larger than life on the belt


def grow(col, x):
    """Scale one form about its spot on the belt (as s02 scales its sacks about their base)."""
    from mathutils import Matrix
    root = geo.empty(f"{col.name}_root", (x, BELT_Y, BELT_Z), col)
    for o in list(col.objects):
        if o is not root and o.parent is None:
            o.parent = root
            o.matrix_parent_inverse = Matrix.Translation(-root.location)
    root.scale = (FORM_SCALE,) * 3


def wet(name, stops, rough=0.35, coat=0.4, sss=0.08, grain=9.0, bump=0.25):
    """A moist organic surface: mottled colour from a noise ramp, a clear wet coat, a little
    subsurface, a fine bump. Meat, offal, fat and the cooked and pressed forms all use it."""
    n = M.Nodes(name)
    n.link(n.ramp(n.noise(grain, 6, 0.62), stops), n.bsdf.inputs["Base Color"])
    n.set("Roughness", rough)
    n.set("Coat Weight", coat)
    n.set("Subsurface Weight", sss)
    n.bump(n.noise(grain * 4, 5, 0.7), bump, 0.004)
    return n.mat


def form_materials(m):
    m.update(
        lean=wet("MAT_lean", [(0.25, "#5E1F1A"), (0.5, "#8E2F27"), (0.75, "#B4544A")], 0.32, 0.5, 0.12),
        fat=wet("MAT_fat", [(0.3, "#D9C7A4"), (0.7, "#EDE1C8")], 0.4, 0.3, 0.2, 6.0),
        liver=wet("MAT_liver", [(0.3, "#2E0E10"), (0.7, "#5A1E22")], 0.18, 0.8, 0.05, 5.0, 0.1),
        gut=wet("MAT_gut", [(0.3, "#B87F78"), (0.7, "#D9A69A")], 0.25, 0.7, 0.2, 7.0),
        bone_raw=wet("MAT_bone_raw", [(0.35, "#D8C6A6"), (0.7, "#F0E6D2")], 0.5, 0.15, 0.05, 12.0, 0.15),
        marrow=wet("MAT_marrow", [(0.3, "#7A2A24"), (0.8, "#C2685A")], 0.3, 0.5),
        mince_mix=wet("MAT_mince_mix", [(0.2, "#5E1F1A"), (0.45, "#A2443A"), (0.62, "#C9705F"), (0.78, "#E6D5BC")], 0.3, 0.55, 0.1, 22.0, 0.4),
        browned=wet("MAT_browned", [(0.2, "#3E2414"), (0.5, "#6E4122"), (0.8, "#9A6A3C")], 0.45, 0.35, 0.02, 14.0, 0.5),
        fat_pool=M.plastic("MAT_fat_pool", "#C9922E", 0.08),
        cake=wet("MAT_cake", [(0.25, "#6E5034"), (0.55, "#8C6A44"), (0.8, "#A8865A")], 0.85, 0.0, 0.0, 26.0, 0.8),
        meal_fine=wet("MAT_meal_fine", [(0.3, "#A88A5E"), (0.6, "#BFA176"), (0.85, "#CDB28A")], 0.95, 0.0, 0.0, 60.0, 0.6),
    )


def lumpy(name, centre, r, scale, mat, col, amount=0.35, seed=0, segs=18):
    """An irregular organic piece: a sphere pushed about by cloud noise (no two alike)."""
    import bpy
    o = geo.sphere(name, centre, r, scale, mat, col, segments=segs, rings=max(8, segs * 2 // 3))
    key = f"TEX_lumps_{seed % 5}"
    tex = bpy.data.textures.get(key) or bpy.data.textures.new(key, "CLOUDS")
    tex.noise_scale = 0.05 + 0.02 * (seed % 5)
    tex.contrast = 1.6
    d = o.modifiers.new("lumps", "DISPLACE")
    d.texture, d.strength, d.mid_level = tex, r * amount, 0.5
    return o


def forms(st):
    """The same kilo in five forms, each sitting on the belt below the machine that made it. Real
    parts, not blobs: rib pieces, a marrow bone, liver, a coil of gut and fat trim in the crate;
    then a wet mixed mince; browned crumbs in their own fat; a cracked press cake beside a jug of
    oil; a fine meal with a scoop in it."""
    m = st.m
    form_materials(m)
    rnd = random.Random(6)
    top = BELT_Z

    def tray(name, x, col, w=0.62, d=0.42):
        geo.box(f"{name}_tray", (x - w / 2, BELT_Y - d / 2, top), (x + w / 2, BELT_Y + d / 2, top + 0.06), m["tray"], col, 0.01)
        return top + 0.05

    # 0 the hub's sealed crate, lid off, heaped with what a meat stall throws away
    col, x = st.prop("form_0"), STAGE_X[0]
    y, z = BELT_Y, top + 0.28
    geo.box("F0_crate", (x - 0.32, y - 0.24, top), (x + 0.32, y + 0.24, top + 0.3), m["crate_blue"], col, 0.02)
    # off-the-shelf cuts (Kenney Food Kit, CC0, re-read as raw meat): a bone-in offcut and a rib piece
    food.cut("F0_cut", "meat-raw", (x - 0.1, y - 0.04, z), col, size=0.22, look="raw", rot=15, tilt=(0, 8))
    food.cut("F0_ribs", "meat-ribs", (x + 0.1, y + 0.02, z + 0.01), col, size=0.22, look="raw", rot=-25, tilt=(6, 0))
    # liver lobes, glossy and dark
    for k, (dx, dy, rr) in enumerate(((-0.2, 0.08, 0.075), (-0.1, 0.13, 0.06))):
        lumpy(f"F0_liver{k}", (x + dx, y + dy, z + 0.04), rr, (1.4, 1.0, 0.4), m["liver"], col, 0.2, k + 2)
    # a coil of gut
    for k in range(10):
        a0, a1 = k * 0.62, (k + 1) * 0.62
        r0, r1 = 0.03 + k * 0.006, 0.03 + (k + 1) * 0.006
        c = (x + 0.17, y + 0.1)
        geo.limb(f"F0_gut{k}", (c[0] + math.cos(a0) * r0, c[1] + math.sin(a0) * r0, z + 0.05), (c[0] + math.cos(a1) * r1, c[1] + math.sin(a1) * r1, z + 0.05),
                 0.017, 0.017, m["gut"], col, segments=10)
    # fat trim
    for k in range(4):
        lumpy(f"F0_fat{k}", (x + rnd.uniform(-0.25, 0.25), y + rnd.uniform(-0.17, 0.17), z + 0.02), rnd.uniform(0.03, 0.05), (1.3, 1, 0.6), m["fat"], col, 0.4, k)
    grow(col, x)

    # 1 crushed small, still raw: a wet heap of mixed bits, flecks of bone through it
    col, x = st.prop("form_1"), STAGE_X[1]
    z = tray("F1", x, col)
    lumpy("F1_heap", (x, BELT_Y, z), 0.19, (1.25, 0.8, 0.7), m["mince_mix"], col, 0.8, 3, 28)
    for i in range(28):
        mat = (m["lean"], m["lean"], m["fat"], m["bone_raw"], m["liver"])[i % 5]
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.05, 0.25)
        lumpy(f"F1_bit{i}", (x + math.cos(a) * r, BELT_Y + math.sin(a) * r * 0.62, z + 0.03 + (0.25 - r) * 0.45),
              rnd.uniform(0.015, 0.03), (1.3, 1, 0.8), mat, col, 0.5, i, 10)
    grow(col, x)

    # 2 cooked: browned crumbs sitting in a little of their own fat (the steam is the game's)
    col, x = st.prop("form_2"), STAGE_X[2]
    z = tray("F2", x, col)
    geo.sphere("F2_fat", (x, BELT_Y, z), 0.26, (1.0, 0.62, 0.04), m["fat_pool"], col, segments=32, rings=8)
    lumpy("F2_heap", (x, BELT_Y, z + 0.01), 0.18, (1.25, 0.8, 0.68), m["browned"], col, 0.9, 4, 28)
    for i in range(30):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.05, 0.25)
        lumpy(f"F2_crumb{i}", (x + math.cos(a) * r, BELT_Y + math.sin(a) * r * 0.62, z + 0.03 + (0.25 - r) * 0.42),
              rnd.uniform(0.014, 0.026), (1.2, 1, 0.8), m["browned"], col, 0.6, i, 10)
    grow(col, x)

    # 3 pressed: a dry cake broken into cracked slabs; the oil that ran off, in a jug
    col, x = st.prop("form_3"), STAGE_X[3]
    z = tray("F3", x - 0.08, col, w=0.5)
    for i, (dx, dy, zz) in enumerate(((-0.11, -0.05, 0), (0.06, 0.05, 0), (-0.02, -0.07, 0.045))):
        o = geo.box(f"F3_slab{i}", (x - 0.08 + dx - 0.1, BELT_Y + dy - 0.075, z + zz), (x - 0.08 + dx + 0.1, BELT_Y + dy + 0.075, z + zz + 0.05), m["cake"], col, 0.006)
        sub = o.modifiers.new("dice", "SUBSURF")
        sub.levels = sub.render_levels = 3
        sub.subdivision_type = "SIMPLE"
        lumpy_tex = __import__("bpy").data.textures.get("TEX_lumps_1")
        d = o.modifiers.new("crumble", "DISPLACE")
        d.texture, d.strength, d.mid_level = lumpy_tex, 0.012, 0.5
    for i in range(10):
        lumpy(f"F3_crumb{i}", (x - 0.08 + rnd.uniform(-0.2, 0.2), BELT_Y + rnd.uniform(-0.15, 0.15), z + 0.01), rnd.uniform(0.01, 0.02), (1, 1, 0.8), m["cake"], col, 0.6, i, 8)
    geo.cylinder("F3_jug", (x + 0.3, BELT_Y, top), 0.1, 0.26, m["glass"], col, segments=20, bevel=0.005)
    geo.cylinder("F3_oil", (x + 0.3, BELT_Y, top + 0.01), 0.088, 0.17, m["oil"], col, segments=20, bevel=0)
    grow(col, x)

    # 4 meal: a fine, grainy heap with a steel scoop in it
    col, x = st.prop("form_4"), STAGE_X[4]
    z = tray("F4", x, col)
    meal = geo.cylinder("F4_meal", (x, BELT_Y, z), 0.25, 0.3, m["meal_fine"], col, segments=48, radius2=0.03, bevel=0.02)
    for poly in meal.data.polygons:
        poly.use_smooth = True
    geo.cylinder("F4_scoop", (x + 0.17, BELT_Y - 0.1, z + 0.04), 0.045, 0.06, m["tray"], col, segments=16, bevel=0.004)
    geo.limb("F4_scoop_handle", (x + 0.21, BELT_Y - 0.1, z + 0.08), (x + 0.33, BELT_Y - 0.13, z + 0.12), 0.01, 0.01, m["tray"], col, segments=8)
    grow(col, x)
    for i, x_ in enumerate(STAGE_X):
        st.anchor(f"form_{i}", (x_, BELT_Y, top + 0.5))


def product(st):
    """The product: meal in woven sacks with a green band, on a pallet; the oil in a banded drum."""
    m, col = st.m, st.prop("product")
    x, y = 4.25, 2.0
    geo.box("PRODUCT_pallet", (x - 0.55, y - 0.45, 0), (x + 0.55, y + 0.45, 0.13), m["pallet"], col, 0.01)
    for i, (dx, dy, z) in enumerate(((-0.25, -0.18, 0.13), (0.25, -0.18, 0.13), (0.0, 0.2, 0.13), (0.0, -0.05, 0.43))):
        geo.box(f"PRODUCT_sack{i}", (x + dx - 0.24, y + dy - 0.17, z), (x + dx + 0.24, y + dy + 0.17, z + 0.3), m["sack"], col, 0.05, subsurf=2)
        geo.box(f"PRODUCT_band{i}", (x + dx - 0.22, y + dy - 0.185, z + 0.12), (x + dx + 0.22, y + dy - 0.16, z + 0.19), m["sack_band"], col, 0)
    geo.cylinder("PRODUCT_drum", (x + 0.15, y + 1.05, 0), 0.29, 0.88, m["oil_drum"], col, segments=28)
    geo.cylinder("PRODUCT_drum_band", (x + 0.15, y + 1.05, 0.5), 0.295, 0.12, m["drum_band"], col, segments=28, bevel=0)
    st.anchor("product_meal", (x, y, 0.9))
    st.anchor("product_oil", (x + 0.15, y + 1.05, 1.0))


def people_and_kit(st):
    """One worker behind the belt at the cooker, a hand truck stacked with empty hub crates."""
    m, col = st.m, st.props
    mats = people.costume_materials("worker", shirt="#4F5E6E", trousers="#4F5E6E", cap="#C9C6BC")
    human.figure("WORKER", (-2.7, 2.0, 0), 10, mats, (-0.32, -0.22, 0.95), (0.3, -0.12, 0.85), col, moustache=False)
    kit.ph("HAND_truck", "hand_truck", (-4.45, 2.0, 0), 30, 1.0, col)
    for i in range(3):
        geo.box(f"EMPTY_crate{i}", (-4.75, 2.8 - 0.25, i * 0.3), (-4.15, 2.8 + 0.25, i * 0.3 + 0.28), m["crate_blue"], col, 0.02)
    light = rig.point_light("LIGHT_plant", (0.0, 2.2, 4.0), (0.96, 0.97, 0.93), 260, 1.2, col)
    light["practical"] = True


def build():
    st = s03.ArtStation(SET_DATA)
    s03.set_materials(st.m)
    kit.kit_materials(st.m)
    materials(st.m)
    plant(st)
    belt(st)
    machines(st)
    forms(st)
    product(st)
    people_and_kit(st)
    st.finish(TARGET)


if __name__ == "__main__":
    build()
