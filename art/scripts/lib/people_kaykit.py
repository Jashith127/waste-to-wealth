"""PARKED, not imported by any build: people.py on the rigged KayKit template (kaykit.py). Swap it in
for people.py once the final human models are decided.

Characters (art-bible §2, §7): a rigged low-poly template (kaykit.py), 1.6 m, 1.3x hands, a
simplified face, no likenesses. Costumes come from photo *types*, never from a real person.

A figure is built in local space (feet at the origin, facing -Y, so its right hand is at -X)
and parented to an empty placed in the world. Poses are just hand targets in local space.
"""
from mathutils import Matrix, Vector

import geo
import kaykit
import materials as M


def costume_materials(name, shirt=("#4E6275", "#B9B3A3", 0.022), skin="#7A4E38", trousers="#2E2B2A",
                      apron=None, cap="#E6E2D8", wet_hands=False, look=None, hair=None, grey=0.0, towel="#B8553C"):
    """Materials for one character. shirt is (checker colour a, b, size) or a single hex. `look` is a
    key of kaykit.LOOKS and picks the dress; by default 'butcher' with an apron, else 'neutral'."""
    look = look or ("butcher" if apron else "neutral")
    spec = kaykit.LOOKS[look]
    shirt_mat = (M.checker_cloth(f"MAT_{name}_shirt", *shirt) if isinstance(shirt, tuple)
                 else M.cloth(f"MAT_{name}_shirt", shirt))
    return dict(
        look=look,
        shirt=shirt_mat,
        trousers=M.cloth(f"MAT_{name}_trousers", trousers, rough=0.85),
        dhoti=M.cloth(f"MAT_{name}_dhoti", "#D9D2C0", weave=0.3, stripe="#9A8F78"),
        skin=M.skin(f"MAT_{name}_skin", skin),
        hands=M.skin(f"MAT_{name}_hands", skin, wet=wet_hands),
        apron=M.cloth(f"MAT_{name}_apron", apron, rough=0.8, weave=0.25) if apron else None,
        cap=M.cloth(f"MAT_{name}_cap", cap, rough=0.85, weave=0.4) if cap else None,
        towel=M.cloth(f"MAT_{name}_towel", towel, weave=0.5, stripe="#E3D9C2"),
        hair=M.hair(f"MAT_{name}_hair", hair or spec["hair"], grey),
        belt=M.leather(f"MAT_{name}_belt"),
        eye=M.matte(f"MAT_{name}_eye", "#1F1A17", 0.5),
        steel=M.steel(f"MAT_{name}_tool"),
        blade=M.steel(f"MAT_{name}_blade", "#9C958C", 0.3),
        wood=M.wood_block(f"MAT_{name}_handle"),
        shoe=M.leather(f"MAT_{name}_shoe", "#2A2624"),
        sandal=M.leather(f"MAT_{name}_sandal", "#6B4F3A"),
        gumboot=M.matte(f"MAT_{name}_gumboot", "#E4E0D4", 0.4),
        frame=M.matte(f"MAT_{name}_frame", "#1C1A19", 0.4),
        glass=M.glass(f"MAT_{name}_lens"),
        mask=M.cloth(f"MAT_{name}_mask", "#C9D3D6", weave=0.3),
        lanyard=M.cloth(f"MAT_{name}_lanyard", "#2F5F8A", weave=0.2),
        card=M.matte(f"MAT_{name}_card", "#E9E4DA", 0.4),
        gloves=M.cloth(f"MAT_{name}_gloves", "#D9C27A", rough=0.8, weave=0.4),
    )


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


def figure(name, origin, heading, mats, right_hand, left_hand, col, tool=None, moustache=None, floor=0.0,
           grip=("loose", "loose"), edge=(0, 0, -1), aim=None, stride=0.0):
    """Build one pose of a figure. Hands are local wrist targets (metres from the feet, facing -Y).
    `grip` is kept for the call sites: the template's hands are mitts. `tool`: None or "cleaver"
    (held in the right fist, its edge facing `edge`, local). `aim`: where the right hand and its tool
    point (local), when the wrist is cocked away from the forearm line. `stride`: metres the right
    foot is ahead (+) or behind (-) in a walk frame; the left foot mirrors it. `moustache`: None
    keeps the look's own. Returns the root empty."""
    root, info = kaykit.build(name, mats["look"], mats, origin, heading, right_hand, left_hand, col,
                              floor=floor, aim=aim, stride=stride, moustache=moustache)
    if tool == "cleaver":
        for o in cleaver(f"{name}_cleaver", Vector(right_hand), Vector(info["fwd"]), edge, mats, col):
            o.parent = root
    return root


def local(world_point, origin):
    """World point -> local hand target for an unrotated figure standing at `origin`."""
    return tuple(Vector(world_point) - Vector(origin))
