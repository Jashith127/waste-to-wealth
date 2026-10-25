"""Characters (art-bible §2, §7): one chunky figure, 1.6 m, 6 heads, 1.3x hands, simplified
faces, no likenesses. Costumes come from photo *types*, never from a real person.

A figure is built in local space (feet at the origin, facing -Y, so its right hand is at -X)
and parented to an empty placed in the world. Poses are just hand targets in local space.
"""
import math

from mathutils import Matrix, Vector

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
        blade=M.steel(f"MAT_{name}_blade", "#9C958C", 0.3),
        wood=M.wood_block(f"MAT_{name}_handle"),
        shoe=M.matte(f"MAT_{name}_shoe", "#2A2624", 0.6),
        sclera=M.matte(f"MAT_{name}_sclera", "#E9E4DA", 0.4),
        lip=M.matte(f"MAT_{name}_lip", "#5A3424", 0.6),
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


def _basis(fwd, hint=(0, 0, -1)):
    """Orthonormal frame for a hand: f along the forearm, n the palm normal (toward `hint` where
    possible), s across the knuckles."""
    f = Vector(fwd).normalized()
    h = Vector(hint)
    n = h - f * h.dot(f)
    if n.length < 1e-3:
        n = Vector((0, -1, 0)) - f * f.y
    n.normalize()
    return f, f.cross(n).normalized(), n


def _oriented_box(name, centre, f, s, n, size, mat, col, subsurf=1):
    """Box of `size` (along f, s, n) at `centre`, turned into the (f, s, n) frame."""
    o = geo.box(name, (-size[0] / 2, -size[1] / 2, -size[2] / 2), (size[0] / 2, size[1] / 2, size[2] / 2), mat, col, 0, subsurf=subsurf)
    o.matrix_world = Matrix.Translation(centre) @ Matrix((f, s, n)).transposed().to_4x4()
    return o


def hand(name, wrist, fwd, kind, mat, col, palm_hint=(0, 0, -1)):
    """A 1.3x hand at the wrist (art bible §2): 'fist' (closed round a handle), 'flat' (fingers
    out, palm down on something) or 'loose' (relaxed, fingers half curled). Returns its objects."""
    f, s, n = _basis(fwd, palm_hint)
    w = Vector(wrist)
    out = [_oriented_box(f"{name}_palm", w + f * 0.05, f, s, n, (0.1, 0.095, 0.042), mat, col)]
    if kind == "fist":
        out.append(_oriented_box(f"{name}_fingers", w + f * 0.1 + n * 0.022, f, s, n, (0.05, 0.1, 0.07), mat, col))
        out.append(geo.limb(f"{name}_thumb", w + f * 0.03 - s * 0.045, w + f * 0.1 - s * 0.03 - n * 0.02, 0.019, 0.016, mat, col))
    elif kind == "flat":
        for k, off in enumerate((-0.036, -0.012, 0.012, 0.036)):
            base = w + f * 0.1 + s * off
            out.append(geo.limb(f"{name}_finger{k}", base, base + f * (0.07 + 0.012 * (k in (1, 2))) + s * off * 0.25, 0.012, 0.01, mat, col, segments=8))
        out.append(geo.limb(f"{name}_thumb", w + f * 0.03 - s * 0.05, w + f * 0.08 - s * 0.085, 0.017, 0.014, mat, col, segments=8))
    else:
        for k, off in enumerate((-0.036, -0.012, 0.012, 0.036)):
            base = w + f * 0.1 + s * off
            out.append(geo.limb(f"{name}_finger{k}", base, base + f * 0.045 + n * 0.035, 0.012, 0.011, mat, col, segments=8))
        out.append(geo.limb(f"{name}_thumb", w + f * 0.03 - s * 0.05, w + f * 0.075 - s * 0.07 + n * 0.02, 0.017, 0.014, mat, col, segments=8))
    return out


def cleaver(name, wrist, fwd, edge, mats, col):
    """An Indian butcher's chopper at 1.3x: wooden handle through the fist, a heavy rectangular
    blade running on from the index finger, its edge facing `edge` (the strike direction)."""
    f, s, n = _basis(fwd, edge)
    grip = Vector(wrist) + f * 0.1
    return [
        geo.limb(f"{name}_handle", grip - f * 0.06, grip + f * 0.09, 0.017, 0.019, mats["wood"], col, segments=10),
        geo.limb(f"{name}_ferrule", grip + f * 0.09, grip + f * 0.11, 0.02, 0.02, mats["steel"], col, segments=10),
        _oriented_box(f"{name}_blade", grip + f * 0.24 + n * 0.055, f, s, n, (0.27, 0.006, 0.13), mats["blade"], col, subsurf=0),
        _oriented_box(f"{name}_spine", grip + f * 0.24 - n * 0.008, f, s, n, (0.27, 0.01, 0.012), mats["steel"], col, subsurf=0),
    ]


def figure(name, origin, heading, mats, right_hand, left_hand, col, tool=None, moustache=True, floor=0.0,
           grip=("loose", "loose"), edge=(0, 0, -1), aim=None, stride=0.0):
    """Build one pose of a figure. Hands are local wrist targets (metres from the feet, facing -Y).
    `grip`: (right, left) hand shapes, each 'loose', 'fist' or 'flat'. `tool`: None or "cleaver"
    (held in a right fist, its edge facing `edge`, local). `aim`: where the right hand and its tool
    point (local), when the wrist is cocked away from the forearm line. `stride`: metres the right
    foot is ahead (+) or behind (-) in a walk frame; the left foot mirrors it. Returns the root empty."""
    root = geo.empty(f"{name}_root", (0, 0, 0), col)
    objs = []
    add = objs.append
    fz = floor
    for i, dx in enumerate((-0.1, 0.1)):
        dy = -stride if i == 0 else stride                  # local -Y is forward
        lift = 0.04 if (stride and dy > 0) else 0.0         # the trailing heel comes up
        add(geo.limb(f"{name}_leg{i}", (dx, 0, fz + 0.82), (dx, dy, fz + 0.07 + lift), 0.082, 0.072, mats["trousers"], col))
        add(geo.box(f"{name}_shoe{i}", (dx - 0.06, dy - 0.12, fz + lift), (dx + 0.06, dy + 0.07, fz + 0.07 + lift), mats["shoe"], col, 0, subsurf=1))
    add(geo.box(f"{name}_torso", (-0.25, -0.15, fz + 0.78), (0.25, 0.15, fz + 1.36), mats["shirt"], col, 0, subsurf=2))
    if mats.get("apron"):
        # a bib apron: front panel, neck strap, waist tie round the body, a pocket (s01 costume, F04)
        add(geo.box(f"{name}_apron", (-0.2, -0.18, fz + 0.42), (0.2, -0.15, fz + 1.24), mats["apron"], col, 0, subsurf=1))
        add(geo.box(f"{name}_apron_pocket", (-0.12, -0.188, fz + 0.86), (0.12, -0.176, fz + 1.0), mats["apron"], col, 0, subsurf=1))
        for i, sx in enumerate((-1, 1)):
            add(geo.limb(f"{name}_apron_strap{i}", (sx * 0.14, -0.17, fz + 1.22), (sx * 0.07, -0.1, fz + 1.36), 0.008, 0.008, mats["apron"], col, segments=8))
        add(geo.box(f"{name}_apron_tie", (-0.262, -0.16, fz + 0.96), (0.262, 0.16, fz + 0.99), mats["apron"], col, 0))
    add(geo.cylinder(f"{name}_neck", (0, 0, fz + 1.3), 0.06, 0.14, mats["skin"], col, bevel=0))
    hz = fz + 1.56
    add(geo.sphere(f"{name}_head", (0, 0, hz), 0.145, (0.93, 0.92, 1.05), mats["skin"], col))
    add(geo.sphere(f"{name}_jaw", (0, -0.03, hz - 0.075), 0.1, (1.0, 0.95, 0.7), mats["skin"], col))
    if mats.get("cap"):
        add(geo.cylinder(f"{name}_cap", (0, 0, hz + 0.085), 0.13, 0.08, mats["cap"], col, bevel=0.012))
    for i, sx in enumerate((-1, 1)):
        add(geo.sphere(f"{name}_eyewhite{i}", (sx * 0.05, -0.124, hz + 0.02), 0.016, (1.2, 0.45, 0.75), mats["sclera"], col))
        add(geo.sphere(f"{name}_eye{i}", (sx * 0.05, -0.131, hz + 0.018), 0.01, (1, 0.6, 1.1), mats["eye"], col))
        add(geo.sphere(f"{name}_ear{i}", (sx * 0.14, 0, hz), 0.03, (0.5, 1, 1.2), mats["skin"], col))
        add(geo.sphere(f"{name}_brow{i}", (sx * 0.05, -0.13, hz + 0.058), 0.022, (1.25, 0.4, 0.35), mats["eye"], col))
    add(geo.sphere(f"{name}_nose", (0, -0.148, hz - 0.012), 0.027, (0.75, 0.9, 1.15), mats["skin"], col))
    add(geo.sphere(f"{name}_mouth", (0, -0.128, hz - 0.085), 0.02, (1.5, 0.4, 0.3), mats["lip"], col))
    if moustache:
        add(geo.sphere(f"{name}_moustache", (0, -0.14, hz - 0.055), 0.03, (1.6, 0.5, 0.4), mats["eye"], col))
    for side, sx, target, kind in (("R", -1, right_hand, "fist" if tool else grip[0]), ("L", 1, left_hand, grip[1])):
        sh = Vector((sx * 0.25, 0, fz + 1.26))
        wrist = Vector(target)
        el = arm_points(sh, wrist, bend=(sx * 0.6, 0.4, -1))
        fwd = (wrist - el).normalized()
        add(geo.sphere(f"{name}_shoulder_{side}", sh, 0.085, (1, 1, 1), mats["shirt"], col))
        add(geo.limb(f"{name}_upper_{side}", sh, sh.lerp(el, 0.82), 0.075, 0.07, mats["shirt"], col))      # half sleeve
        add(geo.limb(f"{name}_cuff_{side}", sh.lerp(el, 0.76), sh.lerp(el, 0.86), 0.078, 0.078, mats["shirt"], col))
        add(geo.limb(f"{name}_arm_{side}", sh.lerp(el, 0.8), el, 0.05, 0.048, mats["hands"], col))
        add(geo.sphere(f"{name}_elbow_{side}", el, 0.049, (1, 1, 1), mats["hands"], col))
        add(geo.limb(f"{name}_fore_{side}", el, wrist, 0.048, 0.036, mats["hands"], col))
        hf = Vector(aim).normalized() if (aim and side == "R") else fwd
        for o in hand(f"{name}_hand_{side}", wrist, hf, kind, mats["hands"], col, palm_hint=edge if side == "R" else (0, 0, -1)):
            add(o)
        if side == "R" and tool == "cleaver":
            for o in cleaver(f"{name}_cleaver", wrist, hf, edge, mats, col):
                add(o)
    for o in objs:
        o.parent = root
    root.location = origin
    root.rotation_euler = (0, 0, math.radians(heading))
    return root


def local(world_point, origin):
    """World point -> local hand target for an unrotated figure standing at `origin`."""
    return tuple(Vector(world_point) - Vector(origin))
