"""Characters (art-bible §2, §7): the five rigged human models (humans.py), about 1.58 m, chunky,
simplified faces, no likenesses. Costumes come from photo *types*, never from a real person.

A figure is built in local space (feet at the origin, facing -Y, so its right hand is at -X)
and parented to an empty placed in the world. Poses are just hand targets in local space.
"""
from mathutils import Matrix, Vector

import geo
import humans
import materials as M


def costume_materials(name, wet_hands=False, look=None, **costume):
    """What a figure needs besides its model: which model (`look`, else by the figure's name: see
    humans.MODEL_FOR), wet skin, and the cleaver's materials. `costume` keeps the old call sites working
    (shirt, apron, cap and so on): the models carry their own clothes now."""
    return dict(
        model=look or humans.model_for(name),
        wet=wet_hands,
        steel=M.steel(f"MAT_{name}_tool"),
        blade=M.steel(f"MAT_{name}_blade", "#9C958C", 0.3),
        wood=M.wood_block(f"MAT_{name}_handle"),
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
    `grip`: (right, left) hand shape, "flat", "loose" or "fist" (humans.GRIPS). `moustache` is kept for the
    call sites: the model's face is what it is.
    `tool`: None or "cleaver" (held in the right hand, its edge facing `edge`, local). `aim`: where the
    right hand and its tool point (local), when the wrist is cocked away from the forearm line.
    `stride`: metres the right foot is ahead (+) or behind (-) in a walk frame; the left foot mirrors
    it. Returns the root empty."""
    root, info = humans.build(name, mats["model"], origin, heading, right_hand, left_hand, col, floor=floor,
                              aim=aim, stride=stride, wet=mats["wet"], grip=grip)
    if tool == "cleaver":
        f, hand = Vector(info["aim"]), Vector(info["fwd"])
        for o in cleaver(f"{name}_cleaver", Vector(info["wrist"]) + (hand - f) * 0.1, f, edge, mats, col):   # the grip stays in the palm
            o.parent = root
    return root


def local(world_point, origin):
    """World point -> local hand target for an unrotated figure standing at `origin`."""
    return tuple(Vector(world_point) - Vector(origin))
