"""Characters (art-bible §2, §7): one chunky figure, 1.6 m, 6 heads, 1.3x hands, simplified
faces, no likenesses. Costumes come from photo *types*, never from a real person.

A figure is built in local space (feet at the origin, facing -Y, so its right hand is at -X)
and parented to an empty placed in the world. Poses are just hand targets in local space.
"""
import math

from mathutils import Vector

import geo
import materials as M


def costume_materials(name, shirt=("#4E6275", "#B9B3A3", 0.022), skin="#7A4E38", trousers="#2E2B2A",
                      apron=None, cap="#E6E2D8", wet_hands=False):
    """Materials for one character. shirt is (checker colour a, b, size) or a single hex."""
    shirt_mat = (M.checker_cloth(f"MAT_{name}_shirt", *shirt) if isinstance(shirt, tuple)
                 else M.matte(f"MAT_{name}_shirt", shirt, 0.85))
    return dict(
        shirt=shirt_mat,
        trousers=M.matte(f"MAT_{name}_trousers", trousers, 0.8),
        skin=M.skin(f"MAT_{name}_skin", skin),
        hands=M.skin(f"MAT_{name}_hands", skin, wet=wet_hands),
        apron=M.matte(f"MAT_{name}_apron", apron, 0.85) if apron else None,
        cap=M.matte(f"MAT_{name}_cap", cap, 0.85) if cap else None,
        eye=M.matte(f"MAT_{name}_eye", "#1F1A17", 0.5),
        steel=M.steel(f"MAT_{name}_tool"),
    )


def arm_points(shoulder, hand, la=0.28, lb=0.27, bend=(0, 0.3, -1)):
    """Two-bone IK in the plane of (hand - shoulder) and `bend`: returns the elbow."""
    s, h = Vector(shoulder), Vector(hand)
    d = h - s
    dist = min(d.length, la + lb - 1e-3)
    a = (la * la - lb * lb + dist * dist) / (2 * dist)
    off = math.sqrt(max(la * la - a * a, 0))
    axis = d.normalized()
    bend_v = Vector(bend)
    perp = (bend_v - axis * bend_v.dot(axis)).normalized()
    return s + axis * a + perp * off


def figure(name, origin, heading, mats, right_hand, left_hand, col, tool=None, moustache=True, floor=0.0):
    """Build one pose of a figure. Hands are local targets (metres from the feet, facing -Y).
    `tool`: None or "cleaver" (held in the right hand). Returns the root empty."""
    root = geo.empty(f"{name}_root", (0, 0, 0), col)
    objs = []
    add = objs.append
    fz = floor
    for i, dx in enumerate((-0.1, 0.1)):
        add(geo.cylinder(f"{name}_leg{i}", (dx, 0, fz), 0.08, 0.8, mats["trousers"], col, bevel=0))
    add(geo.box(f"{name}_torso", (-0.25, -0.15, fz + 0.78), (0.25, 0.15, fz + 1.36), mats["shirt"], col, 0, subsurf=2))
    if mats.get("apron"):
        add(geo.box(f"{name}_apron", (-0.21, -0.175, fz + 0.45), (0.21, -0.14, fz + 1.26), mats["apron"], col, 0, subsurf=1))
    add(geo.cylinder(f"{name}_neck", (0, 0, fz + 1.3), 0.065, 0.14, mats["skin"], col, bevel=0))
    hz = fz + 1.56
    add(geo.sphere(f"{name}_head", (0, 0, hz), 0.145, (0.95, 0.92, 1.05), mats["skin"], col))
    if mats.get("cap"):
        add(geo.cylinder(f"{name}_cap", (0, 0, hz + 0.085), 0.13, 0.08, mats["cap"], col, bevel=0.012))
    for i, s in enumerate((-1, 1)):
        add(geo.sphere(f"{name}_eye{i}", (s * 0.05, -0.13, hz + 0.02), 0.016, (1, 0.6, 1.2), mats["eye"], col))
        add(geo.sphere(f"{name}_ear{i}", (s * 0.14, 0, hz), 0.03, (0.5, 1, 1.2), mats["skin"], col))
        add(geo.sphere(f"{name}_brow{i}", (s * 0.05, -0.128, hz + 0.055), 0.022, (1.2, 0.4, 0.35), mats["eye"], col))
    add(geo.sphere(f"{name}_nose", (0, -0.145, hz - 0.01), 0.026, (0.8, 0.9, 1.1), mats["skin"], col))
    if moustache:
        add(geo.sphere(f"{name}_moustache", (0, -0.138, hz - 0.055), 0.03, (1.6, 0.5, 0.4), mats["eye"], col))
    for side, sx, hand in (("R", -1, right_hand), ("L", 1, left_hand)):
        sh = Vector((sx * 0.25, 0, fz + 1.26))
        el = arm_points(sh, hand, bend=(sx * 0.6, 0.4, -1))
        add(geo.sphere(f"{name}_shoulder_{side}", sh, 0.085, (1, 1, 1), mats["shirt"], col))
        add(geo.limb(f"{name}_upper_{side}", sh, el, 0.075, 0.075, mats["shirt"], col))
        add(geo.sphere(f"{name}_elbow_{side}", el, 0.066, (1, 1, 1), mats["hands"], col))
        add(geo.limb(f"{name}_fore_{side}", el, hand, 0.064, 0.064, mats["hands"], col))
        add(geo.sphere(f"{name}_hand_{side}", hand, 0.08, (0.95, 1.1, 0.75), mats["hands"], col))   # 1.3x hands
        if side == "R" and tool == "cleaver":
            fwd = (Vector(hand) - el).normalized()
            blade = geo.box(f"{name}_cleaver", (-0.003, -0.05, -0.09), (0.003, 0.05, 0.09), mats["steel"], col, 0.002)
            blade.rotation_mode = "QUATERNION"
            blade.rotation_quaternion = fwd.to_track_quat("Z", "X")
            blade.location = Vector(hand) + fwd * 0.12
            add(blade)
    for o in objs:
        o.parent = root
    root.location = origin
    root.rotation_euler = (0, 0, math.radians(heading))
    return root


def local(world_point, origin):
    """World point -> local hand target for an unrotated figure standing at `origin`."""
    return tuple(Vector(world_point) - Vector(origin))
