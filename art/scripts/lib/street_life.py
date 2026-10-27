"""Shivajinagar street life: the density the field photos and Street View show, as kit pieces every
street station can call (art bible §0: V01-V05 look-only, F01-F05). Nothing here stands in a lane a
station keeps clear; each call takes its own x range and y band.

    street_life.wires(st, x0, x1)              # cable bundles along the facade and sagging pole drops (V01, V03)
    street_life.ac_units(st, xs)               # wall AC units with drip stains below (V01)
    street_life.crows(st, xs, z)               # house crows on a ledge
    street_life.marigolds(st, x0, x1)          # a marigold string over a doorway
    street_life.dog(st, at, heading)           # a street dog asleep in the shade
    street_life.vendors(st, xs, y)             # pavement vendors: red steel stands, pink umbrellas, white sacks (V05)
    street_life.people(st, specs)              # passers-by on the low-poly bodies: kurta, lungi, porter, rider
"""
import math
import random

from mathutils import Vector

import geo
import kit
import materials as M
import people as wood


def _mats(m):
    m.setdefault("drip", M.matte("MAT_drip_stain", "#4A4440", 0.4))
    m.setdefault("marigold", M.matte("MAT_marigold", "#E08A1E", 0.7))
    m.setdefault("marigold_red", M.matte("MAT_marigold_red", "#B8401E", 0.7))
    m.setdefault("crow", M.matte("MAT_crow", "#25221F", 0.5))
    m.setdefault("dog", M.matte("MAT_dog", "#9A7650", 0.85))
    m.setdefault("stand_red", M.steel("MAT_stand_red", "#9C3428", 0.5))
    m.setdefault("umbrella_pink", M.matte("MAT_umbrella_pink", "#D9708A", 0.7))
    m.setdefault("sack_white", M.plastic("MAT_sack_dirty_white", "#BDB5A6", 0.5))
    return m


def wires(st, x0, x1, seed=3):
    """Bundles of cable along the facade at the first-floor line, and drops sagging to the shops."""
    s, m, col = st.street, _mats(st.m), st.set
    rnd = random.Random(seed)
    for i in range(6):
        z = 4.55 + i * 0.07
        kit.wire(f"WIRES_run{i}", (x0, s.wall_y - 0.08 - 0.02 * i, z), (x1, s.wall_y - 0.1 - 0.02 * i, z + rnd.uniform(-0.05, 0.05)),
                 0.12 + 0.06 * (i % 3), m["cable"], col, r=0.008 + 0.003 * (i % 2))
    x = x0 + 1.0
    while x < x1 - 1.0:                                   # drops down to meter boxes over the shutters
        kit.wire(f"WIRES_drop{x:.1f}", (x, s.wall_y - 0.12, 4.6), (x + rnd.uniform(0.4, 1.2), s.wall_y - 0.06, 3.0), 0.15, m["cable"], col, r=0.007)
        geo.box(f"WIRES_meter{x:.1f}", (x + 0.5, s.wall_y - 0.12, 2.75), (x + 0.75, s.wall_y - 0.02, 3.05), m["shutter_box"], col, 0.01)
        x += rnd.uniform(1.8, 3.0)


def ac_units(st, xs, z=4.4):
    """Wall AC units on the upper storey, each with the dark drip stain it leaves down the wall."""
    s, m, col = st.street, _mats(st.m), st.set
    for i, x in enumerate(xs):
        geo.box(f"AC{i}", (x, s.wall_y - 0.36, z), (x + 0.75, s.wall_y - 0.04, z + 0.5), m["ac"], col)
        geo.box(f"AC{i}_grille", (x + 0.07, s.wall_y - 0.365, z + 0.08), (x + 0.5, s.wall_y - 0.35, z + 0.42), m["shutter_box"], col, 0.004)
        geo.box(f"AC{i}_drip", (x + 0.55, s.wall_y - 0.012, z - 1.1), (x + 0.64, s.wall_y - 0.005, z), m["drip"], col, 0)
        geo.limb(f"AC{i}_pipe", (x + 0.7, s.wall_y - 0.1, z), (x + 0.72, s.wall_y - 0.06, z - 0.5), 0.012, 0.012, m["cable"], col, segments=6)


def crows(st, xs, z, y=None, seed=5):
    """House crows sitting on a ledge (the chajja), facing about."""
    s, m, col = st.street, _mats(st.m), st.set
    y = s.wall_y - 0.3 if y is None else y
    rnd = random.Random(seed)
    for i, x in enumerate(xs):
        r = math.radians(rnd.uniform(0, 360))
        at = Vector((x, y, z))
        fwd = Vector((math.cos(r), math.sin(r), 0))
        geo.sphere(f"CROW{i}_body", at + Vector((0, 0, 0.1)), 0.08, (1.5, 0.9, 0.9), m["crow"], col, rot=(0, -0.3, r))
        geo.sphere(f"CROW{i}_head", at + fwd * 0.11 + Vector((0, 0, 0.19)), 0.05, (1, 1, 1), m["crow"], col)
        geo.limb(f"CROW{i}_beak", at + fwd * 0.15 + Vector((0, 0, 0.19)), at + fwd * 0.22 + Vector((0, 0, 0.175)), 0.014, 0.003, m["cable"], col, segments=6)
        geo.limb(f"CROW{i}_tail", at - fwd * 0.1 + Vector((0, 0, 0.1)), at - fwd * 0.25 + Vector((0, 0, 0.05)), 0.03, 0.012, m["crow"], col, segments=6)


def marigolds(st, x0, x1, z=2.62, seed=2):
    """A marigold string looped across a doorway lintel."""
    s, m, col = st.street, _mats(st.m), st.set
    n = int((x1 - x0) / 0.06)
    for k in range(n + 1):
        t = k / n
        x = x0 + (x1 - x0) * t
        sag = 0.22 * math.sin(math.pi * ((t * 3) % 1))   # three loops
        geo.sphere(f"MARIGOLD_{x0:.1f}_{k}", (x, s.wall_y - 0.05, z - sag), 0.032, (1, 1, 1), m["marigold"] if k % 4 else m["marigold_red"], col, segments=8, rings=6)


def dog(st, at, heading=0.0):
    """A street dog curled asleep in the shade."""
    m, col = _mats(st.m), st.props
    r = math.radians(heading)
    fwd = Vector((math.cos(r), math.sin(r), 0))
    at = Vector(at)
    geo.sphere("DOG_body", at + Vector((0, 0, 0.14)), 0.2, (1.7, 0.9, 0.7), m["dog"], col, rot=(0, 0, r))
    geo.sphere("DOG_head", at + fwd * 0.3 + Vector((0.0, 0.08, 0.1)), 0.09, (1.3, 1, 0.8), m["dog"], col, rot=(0, 0, r))
    geo.sphere("DOG_ear", at + fwd * 0.33 + Vector((0, 0.12, 0.17)), 0.035, (1, 0.5, 1), m["cable"], col)
    geo.limb("DOG_tail", at - fwd * 0.32 + Vector((0, 0, 0.1)), at - fwd * 0.2 + Vector((0, -0.2, 0.04)), 0.03, 0.015, m["dog"], col, segments=8)


def vendors(st, xs, y, seed=4, side=1):
    """Pavement vendors (V05): a red steel stand with white sacks under a pink umbrella, the seller beside it."""
    m, col = _mats(st.m), st.props
    rnd = random.Random(seed)
    for i, x in enumerate(xs):
        geo.box(f"VENDOR{i}_top", (x - 0.45, y - 0.3, 0.7), (x + 0.45, y + 0.3, 0.74), m["stand_red"], col, 0.01)
        for k, (dx, dy) in enumerate(((-0.42, -0.27), (0.42, -0.27), (-0.42, 0.27), (0.42, 0.27))):
            geo.box(f"VENDOR{i}_leg{k}", (x + dx - 0.02, y + dy - 0.02, 0), (x + dx + 0.02, y + dy + 0.02, 0.7), m["stand_red"], col, 0)
        for k in range(3):
            sx = x - 0.28 + k * 0.28
            geo.cylinder(f"VENDOR{i}_sack{k}", (sx, y, 0.74), 0.12, 0.24, m["sack_white"], col, segments=16, bevel=0.03)
            geo.sphere(f"VENDOR{i}_sack{k}_top", (sx, y, 0.98), 0.11, (1, 1, 0.35),
                       M.matte(f"MAT_vendor_goods{k}", ("#C9A66B", "#8C5A2E", "#D9A93A")[k], 0.85), col, segments=14, rings=8)
        geo.limb(f"VENDOR{i}_pole", (x + 0.4, y + 0.25, 0.7), (x + 0.3, y + 0.15, 2.2), 0.015, 0.015, m["steel_dark"], col, segments=6)
        geo.cylinder(f"VENDOR{i}_umbrella", (x + 0.3, y + 0.15, 2.05), 0.75, 0.25, m["umbrella_pink"], col, segments=10, radius2=0.04, bevel=0.01)
        mats = wood.costume_materials(f"vendor{i}", look="chef")
        wood.figure(f"VENDOR{i}_seller", (x + side * 0.75, y + 0.05, 0), rnd.uniform(-30, 30) + 180, mats, *REST, col)


REST = ((-0.3, 0.0, 0.6), (0.3, 0.0, 0.6))      # local wrist targets: both arms hanging relaxed
LOOKS = {"kurta": "chef", "lungi": "worker", "porter": "worker", "shirt": "office"}   # look -> rigged model


def people(st, specs, col=None):
    """Passers-by on the rigged models (lib/people). Each spec: (name, (x, y), heading, look, stride).
    Looks: 'kurta' (skullcap, V03), 'lungi', 'porter' (a sack carried on the head), 'shirt'."""
    col = col or st.props
    m = _mats(st.m)
    for name, (x, y), heading, look, stride in specs:
        mats = wood.costume_materials(name, look=LOOKS.get(look, "office"))
        right, left = REST
        if look == "porter":
            right, left = (-0.16, -0.04, 1.62), (0.18, 0.02, 1.62)        # both hands up, steadying the load
        wood.figure(name, (x, y, 0), heading, mats, right, left, col, stride=stride)
        if look == "porter":
            geo.box(f"{name}_load", (x - 0.28, y - 0.2, 1.84), (x + 0.28, y + 0.2, 2.12), m["sack_white"], col, 0.05, subsurf=2)
            geo.cylinder(f"{name}_pad", (x, y, 1.78), 0.09, 0.05, m["sack_white"], col, segments=12, bevel=0.01)

