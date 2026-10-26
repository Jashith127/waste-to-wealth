"""Market goods and the handcart that carries them (art-bible §4: procedural materials only, so no
photo textures and no brands). Everything is built in world metres at a point, like geo.py.

    mats = goods.materials()
    goods.thela("CART", (6.1, 2.25, 0), mats, col)       # a loaded wooden handcart, handle toward -X

Goods that read at 175 px/m: red tomatoes heaped in ribbed red crates, onions in orange net sacks,
striped watermelons, a hand of bananas, taped cardboard cartons, a blue tarp rolled and tied with rope. Each is a function, so other stations can load their own carts.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import geo
import materials as M


# ---------------------------------------------------------------- materials
def _lines(n, scale, width=0.16):
    """1 on a grid of lines (in object space, all three axes), 0 between: a net."""
    sep = n.add("ShaderNodeSeparateXYZ")
    n.link(n.coords("Object"), sep.inputs[0])
    masks = []
    for axis in ("X", "Y", "Z"):
        mul = n.add("ShaderNodeMath", operation="MULTIPLY")
        n.link(sep.outputs[axis], mul.inputs[0])
        mul.inputs[1].default_value = scale
        frac = n.add("ShaderNodeMath", operation="FRACT")
        n.link(mul.outputs[0], frac.inputs[0])
        lo = n.add("ShaderNodeMath", operation="LESS_THAN")
        n.link(frac.outputs[0], lo.inputs[0])
        lo.inputs[1].default_value = width
        masks.append(lo.outputs[0])
    acc = masks[0]
    for other in masks[1:]:
        mx = n.add("ShaderNodeMath", operation="MAXIMUM")
        n.link(acc, mx.inputs[0])
        n.link(other, mx.inputs[1])
        acc = mx.outputs[0]
    return acc


def net(name, colour="#C8602E", scale=22.0):
    """Orange polypropylene net: strands in `colour`, clear between them, so the onions show."""
    n = M.Nodes(name)
    clear = n.add("ShaderNodeBsdfTransparent")
    mix = n.add("ShaderNodeMixShader")
    n.link(_lines(n, scale), mix.inputs[0])
    n.link(clear.outputs[0], mix.inputs[1])
    n.link(n.bsdf.outputs[0], mix.inputs[2])
    n.link(mix.outputs[0], n.out.inputs["Surface"])
    n.set("Base Color", M.rgb(colour))
    n.set("Roughness", 0.55)
    return n.mat


def tomato(name):
    n = M.Nodes(name)
    col = n.ramp(n.noise(14.0, 3, 0.5), [(0.25, "#A82A1E"), (0.6, "#C73A26"), (0.85, "#D9552F")])
    n.link(col, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.32)
    n.set("Coat Weight", 0.35)
    return n.mat


def onion(name):
    n = M.Nodes(name)
    col = n.ramp(n.noise(30.0, 4, 0.55), [(0.3, "#8C4A3A"), (0.55, "#B0623F"), (0.8, "#CE8A5C")])
    n.link(col, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.42)
    n.bump(n.noise(60.0, 3), 0.25, 0.004)
    return n.mat


def watermelon(name):
    """Dark green rind with paler, wandering stripes from pole to pole."""
    n = M.Nodes(name)
    wave = n.add("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    wave.inputs["Scale"].default_value = 7.0
    wave.inputs["Distortion"].default_value = 5.0
    wave.inputs["Detail"].default_value = 3.0
    n.link(n.coords("Object"), wave.inputs["Vector"])
    col = n.ramp(wave.outputs["Fac"], [(0.35, "#1E4A26"), (0.62, "#5E8A3C")])
    n.link(col, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.38)
    return n.mat


def banana(name):
    n = M.Nodes(name)
    col = n.ramp(n.noise(18.0, 3, 0.5), [(0.3, "#D6B02C"), (0.7, "#E8C838")])
    n.link(n.mix(n.maprange(n.noise(40.0, 4), 0.55, 0.75, 0.0, 0.5), col, M.rgb("#7A5A28")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.5)
    return n.mat


def carton(name):
    """Corrugated cardboard: brown, with fine ridges in the bump and some scuffing."""
    n = M.Nodes(name)
    wave = n.add("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    wave.inputs["Scale"].default_value = 90.0
    n.link(n.coords("Object"), wave.inputs["Vector"])
    base = M.rgb("#A07E55")
    scuff = n.mix(n.maprange(n.noise(6.0, 5, 0.65), 0.45, 0.8, 0.0, 0.45), base, M.rgb("#5E4A33"))
    n.link(n.mix(n.maprange(wave.outputs["Fac"], 0.0, 1.0, 0.0, 0.12), scuff, M.rgb("#8A6A45")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.85)
    n.bump(wave.outputs["Fac"], 0.2, 0.003)
    return n.mat


def tape(name):
    n = M.Nodes(name)
    n.set("Base Color", M.rgb("#C9A66B"))
    n.set("Roughness", 0.22)
    n.set("Coat Weight", 0.3)
    return n.mat


def tyre(name):
    n = M.Nodes(name)
    n.link(n.mix(n.maprange(n.noise(12.0, 3), 0.4, 0.7, 0.0, 0.35), M.rgb("#1B1918"), M.rgb("#4A423C")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.8)
    n.bump(n.noise(70.0, 2), 0.3, 0.004)
    return n.mat


def rust_paint(name, colour="#4E6B5A"):
    """Hand-painted steel gone shabby: faded green, rust blooming through the edges."""
    n = M.Nodes(name)
    rust = n.maprange(n.noise(7.0, 5, 0.65), 0.5, 0.75, 0.0, 1.0)
    n.link(n.mix(rust, M.rgb(colour), M.rgb("#6B3A1E")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.6)
    n.set("Metallic", 0.4)
    n.bump(n.noise(35.0, 4), 0.2, 0.003)
    return n.mat


def plank(name, colour="#8A6644"):
    """Seasoned timber: long grain, dark where it is oiled and worn."""
    n = M.Nodes(name)
    wave = n.add("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    wave.inputs["Scale"].default_value = 26.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    n.link(n.coords("Object"), wave.inputs["Vector"])
    base = M.rgb(colour)
    dark = tuple(c * 0.55 for c in base[:3]) + (1.0,)
    grain = n.mix(n.maprange(wave.outputs["Fac"], 0.0, 1.0, 0.0, 0.5), base, dark)
    n.link(n.mix(n.maprange(n.noise(5.0, 4, 0.6), 0.45, 0.75, 0.0, 0.5), grain, M.rgb("#33261A")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.75)
    n.bump(wave.outputs["Fac"], 0.15, 0.003)
    return n.mat


def rope(name):
    n = M.Nodes(name)
    wave = n.add("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
    wave.inputs["Scale"].default_value = 160.0
    n.link(n.coords("Object"), wave.inputs["Vector"])
    n.link(n.mix(n.maprange(wave.outputs["Fac"], 0.0, 1.0, 0.0, 0.4), M.rgb("#C2A878"), M.rgb("#7D6A48")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.9)
    return n.mat


def woven_pp(name, colour="#CDC5B0"):
    """Woven polypropylene sacking (the white market sack): a coarse flat-tape weave you can just see, matte,
    dirty."""
    return M.cloth(name, colour, rough=0.8, weave=0.4, scale=70.0)


def bin_plastic(name):
    """Black garbage-bag film: near black, a soft sheen broken up by fine crinkles (no grey fade)."""
    n = M.Nodes(name)
    n.link(n.mix(n.noise(6.0, 3), M.rgb("#0E0E0F"), M.rgb("#1C1B1A")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.32)
    n.bump(n.noise(40.0, 4), 0.35, 0.004)
    return n.mat


def materials():
    """The goods palette, by name. Station materials (tarp, wood_block) are added by the caller."""
    return dict(
        net=net("MAT_net_onion"), tomato=tomato("MAT_tomato"), onion=onion("MAT_onion"),
        melon=watermelon("MAT_watermelon"), banana=banana("MAT_banana"), carton=carton("MAT_carton"),
        tape=tape("MAT_tape"), tyre=tyre("MAT_tyre_thela"), paint=rust_paint("MAT_thela_paint"),
        rope=rope("MAT_rope"),
        crate=M.plastic("MAT_crate_red", "#9A261F", 0.45),
        plank=plank("MAT_thela_plank"),
        stem=M.matte("MAT_stem", "#4E6B2E", 0.6),
        steel=M.steel("MAT_thela_steel", "env.steel", 0.4),
        grip=M.matte("MAT_thela_grip", "#2B2623", 0.7),
    )


# ---------------------------------------------------------------- helpers
def turn(o, pivot, deg):
    """Turn a baked object about the vertical axis through `pivot` (world metres)."""
    p = Vector(pivot)
    o.matrix_world = Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, "Z") @ Matrix.Translation(-p) @ o.matrix_world
    return o


def strand(name, pts, r, mat, col, segments=6):
    """A rope or strap along a polyline."""
    return [geo.limb(f"{name}{i}", pts[i], pts[i + 1], r, r, mat, col, segments=segments) for i in range(len(pts) - 1)]


# ---------------------------------------------------------------- goods
def crate(name, at, mats, col, heap=True, size=(0.5, 0.34, 0.25), rot=0.0, seed=0):
    """A ribbed red plastic crate: a base, rims, ribs with slots between them and cut-out handholds;
    heaped with tomatoes. `at` is the middle of its base."""
    x, y, z = at
    w, d, h = size
    t = 0.014
    parts = [geo.box(f"{name}_base", (x - w / 2, y - d / 2, z), (x + w / 2, y + d / 2, z + 0.02), mats["crate"], col, 0.004)]
    for sy, ny in ((-1, 0), (1, 1)):                       # long walls: top and bottom rims, five ribs
        yy0 = y + sy * d / 2 - (0 if sy < 0 else t)
        parts.append(geo.box(f"{name}_rim_a{ny}", (x - w / 2, yy0, z + h - 0.035), (x + w / 2, yy0 + t, z + h), mats["crate"], col, 0.004))
        parts.append(geo.box(f"{name}_rim_b{ny}", (x - w / 2, yy0, z), (x + w / 2, yy0 + t, z + 0.05), mats["crate"], col, 0.004))
        for k in range(6):
            xx = x - w / 2 + k * (w - 0.03) / 5
            parts.append(geo.box(f"{name}_rib{ny}{k}", (xx, yy0, z), (xx + 0.03, yy0 + t, z + h), mats["crate"], col, 0.003))
    for sx, nx in ((-1, 0), (1, 1)):                       # short walls: solid, with a handhold
        xx0 = x + sx * w / 2 - (0 if sx < 0 else t)
        parts.append(geo.box(f"{name}_end_a{nx}", (xx0, y - d / 2, z), (xx0 + t, y + d / 2, z + 0.06), mats["crate"], col, 0.003))
        parts.append(geo.box(f"{name}_end_b{nx}", (xx0, y - d / 2, z + h - 0.06), (xx0 + t, y + d / 2, z + h), mats["crate"], col, 0.003))
        for dy in (-1, 1):
            parts.append(geo.box(f"{name}_end_c{nx}{dy}", (xx0, y + dy * d * 0.28 - 0.06, z + 0.06), (xx0 + t, y + dy * d * 0.28 + 0.06, z + h - 0.06), mats["crate"], col, 0.003))
    if heap:
        r = 0.052
        k = 0
        for row, yy in enumerate((-0.105, 0.0, 0.105)):
            for j in range(5):
                xx = x - w / 2 + 0.07 + j * (w - 0.14) / 4 + (0.02 if row % 2 else 0)
                zz = z + h - 0.045 + 0.012 * ((j + row + seed) % 2)
                parts.append(geo.sphere(f"{name}_tom{k}", (xx, y + yy, zz), r, (1.0, 1.0, 0.88), mats["tomato"], col, segments=10, rings=7))
                k += 1
        for j in range(4):                                  # a second course nestled in the first
            xx = x - w / 2 + 0.14 + j * (w - 0.28) / 3
            parts.append(geo.sphere(f"{name}_tom{k}", (xx, y + (-0.05 if j % 2 else 0.05), z + h + 0.01), r, (1.0, 1.0, 0.88), mats["tomato"], col, segments=10, rings=7))
            geo.sphere(f"{name}_cap{k}", (xx, y + (-0.05 if j % 2 else 0.05), z + h + 0.05), 0.016, (1.6, 1.6, 0.4), mats["stem"], col, segments=6, rings=4)
            k += 1
    if rot:
        for o in parts:
            turn(o, at, rot)
    return parts


def onion_sack(name, at, mats, col, size=(0.3, 0.19, 0.15), rot=0.0):
    """An orange net sack of onions lying on its side: onions packed under the net, a knotted neck
    and a tie. `at` is the middle of its base."""
    x, y, z = at
    a, b, c = size
    cz = z + c
    parts = []
    k = 0
    for u in range(-3, 4):
        for v in (-1, 0, 1):
            if abs(u) == 3 and v:
                continue
            px = u / 3.4
            py = v / 1.35
            if px * px + py * py > 1.0:
                continue
            pz = math.sqrt(max(0.0, 1.0 - 0.8 * (px * px + py * py)))
            parts.append(geo.sphere(f"{name}_on{k}", (x + px * a * 0.9, y + py * b * 0.88, cz + pz * c * 0.78 - c * 0.2),
                                    0.062, (1.0, 1.0, 0.86), mats["onion"], col, segments=9, rings=6, rot=(0, 0, k * 0.7)))
            k += 1
    parts.append(geo.sphere(f"{name}_core", (x, y, cz - c * 0.15), 1.0, (a * 0.92, b * 0.9, c * 0.75), mats["onion"], col, segments=14, rings=8))
    parts.append(geo.sphere(f"{name}_net", (x, y, cz), 1.0, (a * 1.0, b * 1.0, c * 0.95), mats["net"], col, segments=24, rings=14))
    parts.append(geo.limb(f"{name}_neck", (x + a * 0.92, y, cz), (x + a * 1.28, y + 0.01, cz + 0.03), 0.07, 0.025, mats["net"], col, segments=10))
    parts.append(geo.limb(f"{name}_tie", (x + a * 1.2, y, cz + 0.005), (x + a * 1.28, y + 0.01, cz + 0.035), 0.034, 0.034, mats["rope"], col, segments=8))
    if rot:
        for o in parts:
            turn(o, at, rot)
    return parts


def melon(name, centre, mats, col, r=0.14, rot=0.0):
    o = geo.sphere(name, centre, r, (1.15, 1.0, 1.0), mats["melon"], col, segments=18, rings=12, rot=(0, 0, math.radians(rot)))
    geo.cylinder(f"{name}_stalk", (centre[0] + 0.01, centre[1], centre[2] + r * 0.92), 0.012, 0.035, mats["stem"], col, segments=6, bevel=0)
    return o


def banana_hand(name, root, mats, col, heading=0.0, fingers=6, length=0.24):
    """A hand of bananas fanned from a crown, each finger a curved chain with a dark tip."""
    root = Vector(root)
    out = []
    for i in range(fingers):
        spread = math.radians(-30 + 60 * i / (fingers - 1) + heading)
        ang = math.radians(heading)
        pts = []
        for s in range(6):
            t = s / 5
            a = spread * (0.4 + 0.6 * t)
            fwd = Vector((math.cos(a), math.sin(a), 0))
            pts.append(root + fwd * (length * t) + Vector((0, 0, 0.05 * math.sin(t * math.pi) + 0.02 * t)) + Vector((0, 0, 0.0)))
        for s in range(5):
            r = 0.034 - 0.005 * abs(s - 2)
            out.append(geo.limb(f"{name}_f{i}_{s}", pts[s], pts[s + 1], r, r * 0.95 if s < 4 else r * 0.7, mats["banana"], col, segments=8))
        out.append(geo.sphere(f"{name}_tip{i}", pts[5], 0.018, (1, 1, 1), mats["grip"], col, segments=6, rings=4))
    out.append(geo.limb(f"{name}_stem", root - Vector((0.03, 0, 0)), root + Vector((0.02, 0, 0.0)), 0.03, 0.026, mats["stem"], col, segments=8))
    return out


def cartons(name, at, mats, col, size=(0.46, 0.34, 0.3), rot=0.0):
    """A cardboard carton, flaps taped shut with a strip along the lid seam and down the sides."""
    x, y, z = at
    w, d, h = size
    body = geo.box(f"{name}_box", (x - w / 2, y - d / 2, z), (x + w / 2, y + d / 2, z + h), mats["carton"], col, 0.006)
    t1 = geo.box(f"{name}_tape_top", (x - w / 2 - 0.002, y - 0.025, z + h - 0.003), (x + w / 2 + 0.002, y + 0.025, z + h + 0.004), mats["tape"], col, 0.002)
    t2 = geo.box(f"{name}_tape_f", (x - w / 2 - 0.004, y - 0.025, z + h * 0.58), (x - w / 2 + 0.0, y + 0.025, z + h + 0.004), mats["tape"], col, 0.002)
    t3 = geo.box(f"{name}_tape_b", (x + w / 2, y - 0.025, z + h * 0.58), (x + w / 2 + 0.004, y + 0.025, z + h + 0.004), mats["tape"], col, 0.002)
    seam = geo.box(f"{name}_seam", (x - w / 2 - 0.001, y - d / 2 - 0.001, z + h * 0.55), (x + w / 2 + 0.001, y + d / 2 + 0.001, z + h * 0.552), mats["grip"], col, 0)
    parts = [body, t1, t2, t3, seam]
    if rot:
        for o in parts:
            turn(o, at, rot)
    return parts


def tarp_roll(name, at, mats, col, tarp, length=0.5, r=0.075):
    """A blue tarpaulin rolled up and tied with rope, lying across the cart (along Y)."""
    x, y, z = at
    parts = [geo.cylinder(f"{name}_roll", (x, y - length / 2, z), r, length, tarp, col, axis="Y", segments=16, bevel=0.008)]
    for k, yy in enumerate((-0.15, 0.15)):
        parts.append(geo.cylinder(f"{name}_tie{k}", (x, y + yy - 0.012, z), r + 0.007, 0.024, mats["rope"], col, axis="Y", segments=14, bevel=0))
    parts.append(geo.limb(f"{name}_tail", (x, y + 0.15, z + r), (x + 0.05, y + 0.16, z + r + 0.07), 0.008, 0.008, mats["rope"], col, segments=5))
    return parts


# ---------------------------------------------------------------- the handcart
def thela(name, c, mats, col, tarp, length=1.7, width=0.86, bed_z=0.62):
    """A loaded thela: a wooden-planked steel handcart on two spoked, tyred wheels, handles toward -X,
    a prop leg at the front. `c` is the middle of its footprint; `tarp` is the station's blue tarp."""
    cx, cy, _ = c
    hl, hw = length / 2, width / 2
    # frame: two long angles under the planks, three cross members, planks on top
    for s, side in ((-1, "a"), (1, "b")):
        geo.box(f"{name}_rail{side}", (cx - hl, cy + s * (hw - 0.07) - 0.025, bed_z - 0.1), (cx + hl, cy + s * (hw - 0.07) + 0.025, bed_z - 0.045), mats["paint"], col, 0.006)
    for i, xx in enumerate((-hl + 0.1, 0.0, hl - 0.1)):
        geo.box(f"{name}_cross{i}", (cx + xx - 0.03, cy - hw + 0.02, bed_z - 0.1), (cx + xx + 0.03, cy + hw - 0.02, bed_z - 0.05), mats["paint"], col, 0.006)
    planks = 7
    pw = (width - 0.02) / planks
    for i in range(planks):
        y0 = cy - hw + 0.01 + i * pw
        geo.box(f"{name}_plank{i}", (cx - hl, y0 + 0.004, bed_z - 0.045), (cx + hl, y0 + pw - 0.004, bed_z), mats["plank"], col, 0.004)
    # low side stakes and a front board hold the load in
    for i, xx in enumerate((-hl + 0.04, -0.3, 0.3, hl - 0.04)):
        for s in (-1, 1):
            geo.limb(f"{name}_stake{i}{s}", (cx + xx, cy + s * (hw - 0.02), bed_z), (cx + xx, cy + s * (hw - 0.02), bed_z + 0.34), 0.016, 0.016, mats["paint"], col, segments=8)
    geo.box(f"{name}_front_board", (cx + hl - 0.03, cy - hw, bed_z), (cx + hl, cy + hw, bed_z + 0.2), mats["plank"], col, 0.004)
    for s in (-1, 1):
        geo.limb(f"{name}_siderail{s}", (cx - hl + 0.04, cy + s * (hw - 0.02), bed_z + 0.32), (cx + hl - 0.04, cy + s * (hw - 0.02), bed_z + 0.32), 0.012, 0.012, mats["paint"], col, segments=8)
    # axle and two wheels outboard of the bed, a little aft of the middle
    ax = cx + 0.18
    geo.limb(f"{name}_axle", (ax, cy - hw - 0.08, 0.34), (ax, cy + hw + 0.08, 0.34), 0.03, 0.03, mats["steel"], col, segments=10)
    for s in (-1, 1):
        wy = cy + s * (hw + 0.06)
        geo.cylinder(f"{name}_tyre{s}", (ax, wy - 0.045, 0.34), 0.34, 0.09, mats["tyre"], col, axis="Y", segments=36, bevel=0.025)
        geo.cylinder(f"{name}_rim{s}", (ax, wy - 0.05, 0.34), 0.245, 0.1, mats["steel"], col, axis="Y", segments=30, bevel=0.01)
        geo.cylinder(f"{name}_dish{s}", (ax, wy - 0.052, 0.34), 0.22, 0.01, mats["paint"], col, axis="Y", segments=30, bevel=0)
        geo.cylinder(f"{name}_hub{s}", (ax, wy - 0.06, 0.34), 0.06, 0.12, mats["steel"], col, axis="Y", segments=14, bevel=0.005)
        for k in range(10):                                 # spokes
            a = 2 * math.pi * k / 10
            geo.limb(f"{name}_spoke{s}{k}", (ax + 0.05 * math.cos(a), wy + s * 0.055, 0.34 + 0.05 * math.sin(a)),
                     (ax + 0.225 * math.cos(a), wy + s * 0.055, 0.34 + 0.225 * math.sin(a)), 0.006, 0.006, mats["steel"], col, segments=5)
        geo.box(f"{name}_mudguard{s}", (ax - 0.36, wy - 0.07, 0.69), (ax + 0.36, wy + 0.07, 0.705), mats["paint"], col, 0.004)
    # push handles aft, a cloth-wrapped crossbar, and a prop leg at the front
    for s in (-1, 1):
        a, b = (cx - hl, cy + s * (hw - 0.14), bed_z - 0.07), (cx - hl - 0.62, cy + s * (hw - 0.14), bed_z + 0.34)
        geo.limb(f"{name}_handle{s}", a, b, 0.022, 0.02, mats["plank"], col, segments=10)
        geo.limb(f"{name}_handle_grip{s}", Vector(b) - Vector((0.1, 0, 0.055)), b, 0.027, 0.027, mats["grip"], col, segments=10)
    geo.limb(f"{name}_handle_bar", (cx - hl - 0.62, cy - hw + 0.14, bed_z + 0.34), (cx - hl - 0.62, cy + hw - 0.14, bed_z + 0.34), 0.02, 0.02, mats["plank"], col, segments=10)
    geo.limb(f"{name}_prop", (cx + hl - 0.12, cy, bed_z - 0.08), (cx + hl - 0.12, cy, 0.0), 0.022, 0.02, mats["steel"], col, segments=8)
    geo.box(f"{name}_prop_foot", (cx + hl - 0.2, cy - 0.08, 0.0), (cx + hl - 0.04, cy + 0.08, 0.025), mats["steel"], col, 0.004)

    # --- the load, aft to front ---
    zb = bed_z
    for i, (dx, dy, rot) in enumerate(((-0.6, -0.19, 3), (-0.6, 0.19, -4))):               # tomato crates, two stacks of two
        crate(f"{name}_crateL{i}", (cx + dx, cy + dy, zb), mats, col, heap=False, rot=rot)
        crate(f"{name}_crateU{i}", (cx + dx, cy + dy, zb + 0.25), mats, col, heap=True, rot=rot + 6, seed=i)
    onion_sack(f"{name}_sackA", (cx - 0.12, cy - 0.2, zb), mats, col, rot=-8)
    onion_sack(f"{name}_sackB", (cx - 0.12, cy + 0.2, zb), mats, col, rot=7)
    onion_sack(f"{name}_sackC", (cx - 0.1, cy + 0.0, zb + 0.27), mats, col, size=(0.3, 0.19, 0.13), rot=-2)
    cartons(f"{name}_cartonA", (cx + 0.36, cy - 0.2, zb), mats, col, rot=4)
    cartons(f"{name}_cartonB", (cx + 0.36, cy - 0.2, zb + 0.3), mats, col, size=(0.42, 0.32, 0.26), rot=-6)
    for i, (dx, dy, dz, r) in enumerate(((0.3, 0.2, 0.14, 10), (0.52, 0.22, 0.14, 40), (0.43, 0.04, 0.14, 70), (0.4, 0.2, 0.37, 20))):
        melon(f"{name}_melon{i}", (cx + dx, cy + dy, zb + dz), mats, col, rot=r)
    banana_hand(f"{name}_bananas", (cx + 0.52, cy - 0.12, zb + 0.58), mats, col, heading=-35, length=0.3)
    tarp_roll(f"{name}_tarp", (cx + 0.2, cy - 0.2, zb + 0.56 + 0.075), mats, col, tarp)


# ---------------------------------------------------------------- waste
def _blob(name, at, size, col, mats, seed, shape, lumps=8, lump_amp=(0.06, 0.16), lump_w=0.3):
    """A filled sack as one smooth mesh: a sphere pushed out by `shape(p, h, theta, bulge)` (p the unit
    direction, h 0..1 up the sack, bulge the lumps of whatever is inside it), flat where it sits.
    `mats` is a list of (material, h0, h1): faces whose h lies in [h0, h1) take that material."""
    rng = random.Random(seed)
    lumps = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.7, 0.7))).normalized(), rng.uniform(*lump_amp))
             for _ in range(lumps)]
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
    w, d, hgt = size
    for v in bm.verts:
        p = v.co.normalized()
        h = (p.z + 1) / 2
        theta = math.atan2(p.y, p.x)
        bulge = sum(a * math.exp(-(p - c).length_squared / lump_w) for c, a in lumps)
        x, y, z = shape(p, h, theta, bulge)
        v.co = Vector((x * w / 2, y * d / 2, max(z, 0.0) * hgt))
    hc_v = {v.index: v.co.z / hgt for v in bm.verts}                      # material bands, before moving into place
    bmesh.ops.translate(bm, vec=Vector(at), verts=bm.verts)             # baked in world metres, like geo.py
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    for m, _, _ in mats:
        me.materials.append(m)
    for poly in me.polygons:
        poly.use_smooth = True
        hc = sum(hc_v[i] for i in poly.vertices) / len(poly.vertices)
        poly.material_index = next((i for i, (_, h0, h1) in enumerate(mats) if h0 <= hc < h1), 0)
    sub = o.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    return o


def _smooth(x, a, b):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def bin_bag(name, at, mat, col, size=(0.6, 0.5, 0.46), rot=0.0, seed=0):
    """A black garbage bag, full: slumped wider than it is tall, lumpy with what is inside, the film
    drawn up in sharp stretch creases to a short twisted neck, knotted, the two tied ears flopping.
    `at` is the middle of its base."""
    phase = seed * 1.7

    def shape(p, h, theta, bulge):
        r = 1.0 + bulge
        band = _smooth(h, 0.4, 0.7) * (1 - _smooth(h, 0.86, 0.95))
        r *= 1 - 0.07 * band * (abs(math.sin(5.5 * theta + phase)) - 0.4)   # stretch creases running up to the neck
        r *= 1 + 0.2 * (1 - h) ** 2                                          # slumps out at the base
        neck = _smooth(h, 0.8, 0.96)
        r *= 1 - 0.88 * neck                                                 # drawn in to the neck
        z = h * 0.86 + 0.1 * neck + 0.1 * bulge
        ring = math.sqrt(max(1 - p.z * p.z, 0)) * r                          # distance out from the axis
        return math.cos(theta) * ring, math.sin(theta) * ring, z
    x, y, z = at
    w, d, hgt = size
    parts = [_blob(name, at, size, col, [(mat, 0, 2)], seed, shape, lumps=14, lump_amp=(0.1, 0.3), lump_w=0.1)]
    top = z + hgt * 0.97
    lean = 0.04 * (1 if seed % 2 else -1)
    parts.append(geo.limb(f"{name}_neck", (x, y, top - 0.05), (x + lean, y, top + 0.04), 0.03, 0.02, mat, col, segments=10))
    parts.append(geo.sphere(f"{name}_knot", (x + lean, y, top + 0.05), 0.03, (1.25, 1.0, 0.8), mat, col, segments=12, rings=8))
    for i, s_ in enumerate((-1, 1)):                                         # the tied ears, thin film, drooping unevenly
        droop = 80 + 15 * i
        parts.append(geo.sphere(f"{name}_ear{i}", (x + lean + s_ * 0.06, y + 0.02 * s_, top + 0.03), 0.07 - 0.012 * i,
                                (0.45, 0.09, 0.75), mat, col, segments=12, rings=8, rot=(0.35 * s_, math.radians(-droop * s_), 0.5 * s_ + seed)))
    if rot:
        for o in parts:
            turn(o, at, rot)
    return parts


def bone(name, a, b, mat, col, r=0.016):
    """A butchered bone: a shaft with knuckled ends (plain ellipsoids read as beans)."""
    a, b = Vector(a), Vector(b)
    side = (b - a).cross(Vector((0, 0, 1))).normalized() * r * 0.9
    return [geo.limb(f"{name}_shaft", a, b, r, r * 0.85, mat, col, segments=8),
            geo.sphere(f"{name}_ka", a + side, r * 1.5, (1, 1, 0.8), mat, col, segments=10, rings=6),
            geo.sphere(f"{name}_kb", a - side, r * 1.4, (1, 1, 0.8), mat, col, segments=10, rings=6),
            geo.sphere(f"{name}_kc", b, r * 1.6, (1.2, 1, 0.8), mat, col, segments=10, rings=6)]


def woven_sack(name, at, mats, col, size=(0.5, 0.36, 0.62), rot=0.0, tip=0.0, seed=0, split=False):
    """A white woven polypropylene sack (the market sack), stuffed: a squarish pillow with soft
    corners and lumps of what is inside, a printed band, its neck gathered and tied with twine and a
    tuft above the tie. `split`: the neck is torn open, flared, the dark inside showing (mats["inside"]).
    `tip` (degrees) lays it over toward -Y, so a split mouth faces the street. `mats`: sack, band, rope
    (and inside). `at` is the middle of its base. Returns (parts, mouth): where its neck ends up."""
    def shape(p, h, theta, bulge):
        c, s = math.cos(theta), math.sin(theta)
        sq = (abs(c) ** 4 + abs(s) ** 4) ** -0.25                            # a rounded square, not a circle
        r = (1.0 + bulge) * sq * math.sqrt(max(1 - p.z * p.z, 0)) ** 0.55
        r *= 1 + 0.12 * (1 - h) ** 2
        if split:                                                            # torn mouth: necks in, then flares
            mouth = _smooth(h, 0.82, 1.0)
            r *= 1 - 0.3 * _smooth(h, 0.68, 0.84) + 0.55 * mouth
            z = min(h, 0.88) * 0.95 + 0.06 * mouth * math.sin(3 * theta + seed)
        else:
            neck = _smooth(h, 0.74, 0.94)
            r *= 1 - 0.8 * neck
            z = h * 0.9 + 0.08 * neck
        return c * r, s * r, z
    x, y, z = at
    w, d, hgt = size
    parts = [_blob(name, at, size, col, [(mats["sack"], 0, 0.56), (mats["band"], 0.56, 0.63), (mats["sack"], 0.63, 2)],
                   seed, shape, lumps=12, lump_amp=(0.05, 0.14), lump_w=0.14)]
    top = z + hgt * 0.95
    if split:
        parts.append(geo.sphere(f"{name}_inside", (x, y, z + hgt * 0.9), 1.0, (w * 0.36, d * 0.36, 0.02), mats["inside"], col, segments=20, rings=8))
    else:
        parts.append(geo.limb(f"{name}_tie", (x, y, top - 0.03), (x, y, top + 0.0), 0.042, 0.042, mats["rope"], col, segments=10))
        parts.append(geo.limb(f"{name}_tuft", (x, y, top - 0.01), (x + 0.02, y - 0.01, top + 0.09), 0.03, 0.07, mats["sack"], col, segments=10))
    mouth = Vector((x, y, z + hgt * 0.9))
    if tip:
        piv = Vector(at) + Vector((0, -d / 2, 0))                            # it falls forward over its front edge
        R = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(-tip), 4, "X") @ Matrix.Translation(-piv)
        for o in parts:
            o.matrix_world = R @ o.matrix_world
        mouth = R @ mouth
    if rot:
        for o in parts:
            turn(o, at, rot)
        p = Vector(at)
        mouth = p + Matrix.Rotation(math.radians(rot), 3, "Z") @ (mouth - p)
    return parts, mouth
