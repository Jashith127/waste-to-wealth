"""The station people: five rigged, textured human models (art/scripts/humans_build.py makes
art/build/humans/humans_rigged.blend from the Tripo GLBs), appended once per scene and copied per figure.

A figure is built in local space (feet on the floor at the origin, facing -Y, so its right hand is at -X)
and parented to an empty placed in the world. Arms reach hand targets and the legs stride by aiming
bones (two-bone IK), so a pose is still just a few local points, as in the old procedural figures.
The models carry their own clothes, so which model a person uses is their costume: see MODEL_FOR.
"""
import math

import bpy
from mathutils import Matrix, Vector

import geo
import safety

BLEND = safety.ART / "build" / "humans" / "humans_rigged.blend"
TEMPLATES = "HUMAN_templates"

# Who wears which model. Names are the figure's name prefix; first match wins. Change a line to recast.
MODEL_FOR = (
    ("riyaz", "farmer"),          # checked shirt, bib apron, white skullcap, short beard: the persona (deck p. 22)
    ("attendant", "office"),      # grey shirt, lanyard, glasses
    ("loader", "worker"),         # vest, red-and-white gamchha, rolled trousers
    ("worker", "construction"),   # hard hat, mask, boiler suit, gloves, white boots
    ("vendor", "chef"),           # skullcap, apron
    ("farmer", "worker"),
    ("anthony", "chef"),
    ("arif", "construction"),
    ("ped0", "chef"), ("ped1", "office"), ("ped2", "worker"), ("ped3", "construction"),
    ("scale_person", "office"),
)
ARM_K = 1.18                      # the models' arms are short for the counters (shoulders at 62% of height): stretched
HAND_BEND = math.radians(55)       # a hand turns at most this far from its forearm
WET = ("farmer",)                 # models whose forearms and hands take the wet-skin variant when asked
ELBOW_HINT = 0.3                  # how far out (vs back and down) an elbow points; more reads as hands on hips
SHRUG = 0.35                      # share of an arm's rise above level taken by its clavicle
GRIPS = {                         # finger curl, thumb curl (radians): the T-pose hand is flat and spread
    "flat": (0.1, 0.05),
    "loose": (0.6, 0.25),
    "fist": (1.5, 0.7),
}


def model_for(name):
    n = name.lower()
    for prefix, model in MODEL_FOR:
        if n.startswith(prefix):
            return model
    return "office"


def _template(model):
    """(armature, mesh) of the model, appended into this file on first use and kept off the scene."""
    tcol = bpy.data.collections.get(TEMPLATES)
    if tcol is None:
        tcol = bpy.data.collections.new(TEMPLATES)
        tcol.use_fake_user = True
    arm, mesh = tcol.objects.get(f"HUMAN_{model}_rig"), tcol.objects.get(f"HUMAN_{model}")
    if arm and mesh:
        return arm, mesh
    if not BLEND.exists():
        raise FileNotFoundError(f"{BLEND}: run blender -b --python art/scripts/humans_build.py")
    with bpy.data.libraries.load(str(BLEND), link=False) as (src, dst):
        dst.collections = [f"HUMAN_{model}"]
        dst.materials = [f"MAT_human_{model}_wet"]
    got = dst.collections[0]
    for o in list(got.objects):
        got.objects.unlink(o)
        tcol.objects.link(o)
    bpy.data.collections.remove(got)
    return tcol.objects[f"HUMAN_{model}_rig"], tcol.objects[f"HUMAN_{model}"]


def two_bone(root, target, la, lb, bend):
    """Joint position for a two-bone limb from `root` reaching `target`, bending toward `bend`."""
    s, h = Vector(root), Vector(target)
    d = h - s
    dist = max(min(d.length, la + lb - 1e-3), abs(la - lb) + 1e-3)
    a = (la * la - lb * lb + dist * dist) / (2 * dist)
    off = math.sqrt(max(la * la - a * a, 0))
    axis = d.normalized()
    b = Vector(bend)
    perp = b - axis * b.dot(axis)
    if perp.length < 1e-4:
        perp = Vector((0, -1, 0)) - axis * axis.y
    return s + axis * a + perp.normalized() * off


def _aim(pb, direction):
    """Turn a pose bone about its head so it points along `direction` (armature space)."""
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    m = (q.to_matrix() @ pb.matrix.to_3x3()).to_4x4()
    m.translation = pb.head
    pb.matrix = m
    bpy.context.view_layer.update()


def _roll_palm(pb, desired):
    """Turn a hand about its own axis so its palm faces `desired` (as nearly as the axis allows): aiming
    bones takes the shortest turn, which can leave a hand with its palm out."""
    axis = (pb.tail - pb.head).normalized()
    palm = pb.matrix.to_3x3().normalized() @ (pb.bone.matrix_local.to_3x3().normalized().inverted() @ Vector((0, 0, -1)))
    a = palm - axis * palm.dot(axis)
    b = Vector(desired) - axis * Vector(desired).dot(axis)
    if a.length < 1e-4 or b.length < 1e-4:
        return
    a.normalize()
    b.normalize()
    angle = math.atan2(axis.dot(a.cross(b)), a.dot(b))
    m = (Matrix.Rotation(angle, 3, axis) @ pb.matrix.to_3x3()).to_4x4()
    m.translation = pb.head
    pb.matrix = m
    bpy.context.view_layer.update()


def _roll_angle(pb, ref):
    """Signed turn about `pb`'s own axis from bone `ref`'s local X to `pb`'s local X (both posed)."""
    axis = (pb.tail - pb.head).normalized()
    a = ref.matrix.to_3x3().col[0]
    b = pb.matrix.to_3x3().col[0]
    a, b = a - axis * a.dot(axis), b - axis * b.dot(axis)
    if a.length < 1e-4 or b.length < 1e-4:
        return 0.0
    a.normalize()
    b.normalize()
    return math.atan2(axis.dot(a.cross(b)), a.dot(b))


def _spin(pb, angle):
    """Turn a pose bone about its own axis."""
    axis = (pb.tail - pb.head).normalized()
    m = (Matrix.Rotation(angle, 3, axis) @ pb.matrix.to_3x3()).to_4x4()
    m.translation = pb.head
    pb.matrix = m
    bpy.context.view_layer.update()


def _bone(arm, name):
    b = arm.data.bones[name]
    return b.head_local.copy(), b.tail_local.copy()


def build(name, model, origin, heading, right_hand, left_hand, col, floor=0.0, aim=None, stride=0.0, wet=False,
          grip=("loose", "loose"), legs=None, bob=0.0, lean=0.0, head_turn=0.0):
    """One posed figure. Returns (root empty, info); info has the right wrist and forearm direction (local m).
    A walk frame (people.gait) passes `legs` ((forward, lift) of the right and left ankle, m) in place of
    `stride`, `bob` (the hips' rise, m: negative dips them, the feet stay planted) and `lean` (the spine
    forward, degrees). `head_turn` turns the head about the neck (degrees, + to the figure's left)."""
    t_arm, t_mesh = _template(model)
    arm = t_arm.copy()
    arm.name = f"{name}_rig"
    mesh = t_mesh.copy()
    mesh.name = f"{name}_body"
    col.objects.link(arm)
    col.objects.link(mesh)
    mesh.parent = arm
    for mod in mesh.modifiers:
        if mod.type == "ARMATURE":
            mod.object = arm
    if wet and model in WET:
        mesh.material_slots[0].link = "OBJECT"
        mesh.material_slots[0].material = bpy.data.materials[f"MAT_human_{model}_wet"]
    arm.location = (0, 0, floor + bob)
    bpy.context.view_layer.update()
    pbs = arm.pose.bones
    if lean:                                                            # before the arms, so they reach from the leaned shoulders
        sh, st = _bone(arm, "spine")
        _aim(pbs["spine"], Matrix.Rotation(math.radians(lean), 3, "X") @ (st - sh))
    info = {}
    for side, sx, target, is_right, g in (("R", -1, right_hand, True, grip[0]), ("L", 1, left_hand, False, grip[1])):
        t = Vector(target) - Vector((0, 0, floor))
        uh, ut = _bone(arm, f"upperarm.{side}")
        lh, _ = _bone(arm, f"lowerarm.{side}")
        _, wt = _bone(arm, f"twist.{side}")
        la, lb = (ut - uh).length * ARM_K, (wt - lh).length * ARM_K
        hint = (sx * ELBOW_HINT, 0.6, -1)
        # a raised arm lifts its shoulder: the clavicle takes part of the rise, then the arm reaches from there
        rise = math.asin(max(-1.0, min(1.0, (two_bone(uh, t, la, lb, hint) - uh).normalized().z)))
        if rise > 0:
            ch, ct = _bone(arm, f"clavicle.{side}")
            d = ct - ch
            _aim(pbs[f"clavicle.{side}"], Matrix.Rotation(-sx * rise * SHRUG, 3, "Y") @ d)
        uh = pbs[f"upperarm.{side}"].head.copy()
        elbow = two_bone(uh, t, la, lb, hint)
        _aim(pbs[f"upperarm.{side}"], elbow - uh)
        for b in ("upperarm", "lowerarm", "twist"):
            pbs[f"{b}.{side}"].scale = (1, ARM_K, 1)
        bpy.context.view_layer.update()
        wrist = elbow + (t - elbow).normalized() * min(lb, (t - elbow).length)   # where the hand really ends up
        fore = (wrist - elbow).normalized()
        _aim(pbs[f"lowerarm.{side}"], fore)
        want = Vector(aim).normalized() if (aim and is_right) else fore
        angle = fore.angle(want)
        hf = want if angle <= HAND_BEND else fore.slerp(want, HAND_BEND / angle)      # a wrist only bends so far
        _aim(pbs[f"hand.{side}"], hf)
        _roll_palm(pbs[f"hand.{side}"], Vector((-sx * 0.6, 0.0, -0.8)))              # palm toward the thigh / down
        # the forearm shares the roll: half of it moves into the twist bone, the hand keeps where it is
        hand_m = pbs[f"hand.{side}"].matrix.copy()
        _spin(pbs[f"twist.{side}"], 0.5 * _roll_angle(pbs[f"hand.{side}"], pbs[f"twist.{side}"]))
        pbs[f"hand.{side}"].matrix = hand_m
        bpy.context.view_layer.update()
        curl, thumb = GRIPS.get(g, GRIPS["loose"])
        pbs[f"fingers.{side}"].rotation_mode = pbs[f"thumb.{side}"].rotation_mode = "XYZ"
        pbs[f"fingers.{side}"].rotation_euler = (-curl, 0, 0)                     # local X runs across the knuckles
        pbs[f"thumb.{side}"].rotation_euler = (-thumb, 0, sx * thumb * 0.6)           # in across the palm
        bpy.context.view_layer.update()
        if is_right:
            info = dict(wrist=tuple(wrist + Vector((0, 0, floor))), fwd=tuple(hf), aim=tuple(want))
    for i, side in enumerate(("R", "L")):
        if legs:
            fwd, lift = legs[i]
            dy = -fwd                                                   # local -Y is forward
        else:
            dy = -stride if i == 0 else stride
            lift = 0.04 if (stride and dy > 0) else 0.0                 # the trailing heel comes up
        uh, ut = _bone(arm, f"upperleg.{side}")
        lh, lt = _bone(arm, f"lowerleg.{side}")
        fh, ft = _bone(arm, f"foot.{side}")
        ankle = lt + Vector((0, dy, lift - bob))                        # a dipped body keeps its planted foot on the floor
        knee = two_bone(uh, ankle, (ut - uh).length, (lt - lh).length, (0, -1, 0))
        _aim(pbs[f"upperleg.{side}"], knee - uh)
        _aim(pbs[f"lowerleg.{side}"], ankle - knee)
        toe = ft - fh
        if legs and lift > 0.02:                                        # a swinging foot hangs toe-down a little
            toe = Matrix.Rotation(math.radians(25 * min(lift / 0.08, 1)), 3, "X") @ toe
        _aim(pbs[f"foot.{side}"], toe)
    if head_turn:
        _spin(pbs["head"], math.radians(head_turn))
    root = geo.empty(f"{name}_root", (0, 0, 0), col)
    arm.parent = root
    root.location = origin
    root.rotation_euler = (0, 0, math.radians(heading))
    return root, info
