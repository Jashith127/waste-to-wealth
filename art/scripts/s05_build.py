"""Station 5 · Bulk pickup (Run 2). Builds art/blender/s05_pickup.blend.

Run:  blender -b --python art/scripts/s05_build.py
Then: blender -b art/blender/s05_pickup.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s05

Re-runnable. Destructive only to art/blender/s05_pickup.blend (backed up by lib/safety).

The hub's loading bay on its service lane: Russell Market's masonry (X04/R24) for the hub's side
wall, a bay at kerb height, six sealed Chamber-B crates in two stacks (crate 0 is ours), and the
authorised collector's goods carrier: generic, with no brand, name or number plate (task 05). A
loader waits by the bay. Kit dressing from V01-V05. The truck and every crate are their own
layers, so Station05 can load the crates and drive the truck off.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import people  # noqa: E402
import s03_art_build as s03  # noqa: E402
import street_life  # noqa: E402
from mathutils import Vector  # noqa: E402

SET_DATA = {"id": "s05", "set": {"blend": "art/blender/s05_pickup.blend", "lighting": "midday", "street": {"x0": -5.0, "x1": 7.0}}, "signs": []}
TARGET = (0.0, 2.4, 0.5)
CRATE = (0.55, 0.36, 0.3)
BAY_TOP = 0.9
STACKS = (-3.0, -2.3)            # crate i: stack i % 2, level i // 2 (crate 0 at the bottom of the back stack)


def bay(st):
    s, m, col = st.street, st.m, st.set
    w = s.wall_y
    geo.box("HUB_wall", (s.x0, w, 0), (1.2, w + 0.3, 7.4), m["masonry"], col, geo.BEVEL_ARCH)
    geo.box("HUB_base", (s.x0, w - 0.08, 0), (1.2, w, 0.42), m["masonry"], col, geo.BEVEL_ARCH)
    for i, (x0, x1) in enumerate(((-4.9, -4.5), (-1.3, -0.9))):
        geo.box(f"HUB_pilaster{i}", (x0, w - 0.14, 0), (x1, w, 7.4), m["masonry"], col, geo.BEVEL_ARCH)
    s03.arch_band("HUB_blind_arch", -2.7, 2.6, 2.4, 0.9, 1.0, 0.12, w - 0.04, m["masonry"], col)
    # the loading door, a roller shutter (open) into the dark cold store
    geo.box("HUB_door_dark", (-3.8, w - 0.01, BAY_TOP), (-1.6, w + 0.01, 2.9), m["window_glass"], col, 0)
    geo.box("HUB_door_housing", (-3.85, w - 0.2, 2.9), (-1.55, w, 3.15), m["shutter_box"], col, 0.01)
    geo.box("BAY", (-4.4, 1.55, 0), (0.6, w, BAY_TOP), m["concrete"], col, geo.BEVEL_ARCH)
    geo.box("BAY_edge", (-4.4, 1.5, BAY_TOP - 0.08), (0.6, 1.6, BAY_TOP + 0.01), m["flex_yellow"], col, 0.01)
    for i, x in enumerate((-4.1, -1.2, 0.3)):
        geo.box(f"BAY_bumper{i}", (x - 0.15, 1.42, 0.35), (x + 0.15, 1.55, 0.75), m["auto_dark"], col, 0.02)
    geo.box("HUB_section_end", (1.2, w, 0), (1.21, w + 0.3, 7.4), m["section"], col, 0)
    st.anchor("bay", (-2.0, 2.2, BAY_TOP))


def crates(st):
    """Six sealed crates in Chamber B blue, each its own layer (crate_0 ... crate_5)."""
    m = st.m
    lx, ly, lz = CRATE
    for i in range(6):
        x, z = STACKS[i % 2], BAY_TOP + (i // 2) * lz
        col = st.prop(f"crate_{i}")
        c = Vector((x, 2.28, z))
        geo.box(f"CRATE{i}_body", (c.x - lx / 2 + 0.01, c.y - ly / 2 + 0.01, z), (c.x + lx / 2 - 0.01, c.y + ly / 2 - 0.01, z + lz - 0.04), m["crate"], col, 0.02)
        geo.box(f"CRATE{i}_lid", (c.x - lx / 2, c.y - ly / 2, z + lz - 0.04), (c.x + lx / 2, c.y + ly / 2, z + lz), m["crate"], col, 0.012)
        for k in range(5):
            xx = c.x - lx / 2 + 0.08 + k * (lx - 0.16) / 4
            geo.box(f"CRATE{i}_rib{k}", (xx - 0.012, c.y - ly / 2 - 0.008, z + 0.03), (xx + 0.012, c.y - ly / 2 + 0.004, z + lz - 0.07), m["crate"], col, 0.004)
        geo.box(f"CRATE{i}_handhold", (c.x + lx / 2 - 0.004, c.y - 0.07, z + lz - 0.13), (c.x + lx / 2 + 0.004, c.y + 0.07, z + lz - 0.085), m["crate_slot"] if "crate_slot" in m else m["crate_dark"], col, 0.01)
        st.anchor(f"crate_{i}_centre", (c.x, c.y, z + lz / 2))
    st.anchor("crate_0_knot", (STACKS[0], 2.28, BAY_TOP + lz))


def truck(st):
    """A small goods carrier (the type that does city pickups), generic: white cab, a box body with
    a roll-up shutter at the back, open to the bay. No brand, name or plate (task 05)."""
    m, col = st.m, st.prop("truck")
    white = m.setdefault("truck_white", M.plastic("MAT_truck_white", "#D9D6CE", 0.4))
    geo.box("TRUCK_chassis", (1.0, 0.75, 0.45), (5.7, 2.45, 0.62), m["steel_dark"], col, 0.02)
    geo.box("TRUCK_box", (1.0, 0.7, 0.62), (4.5, 2.5, 2.75), white, col, 0.03)
    for k in range(6):
        x = 1.3 + k * 0.55
        geo.box(f"TRUCK_rib{k}", (x - 0.02, 0.68, 0.7), (x + 0.02, 0.7, 2.7), m["steel"], col, 0.004)
    geo.box("TRUCK_rear_open", (0.98, 0.85, 0.7), (1.0, 2.35, 2.6), m["window_glass"], col, 0)
    geo.box("TRUCK_shutter_rolled", (0.95, 0.8, 2.6), (1.05, 2.4, 2.75), m["shutter"], col, 0.01)
    geo.box("TRUCK_cab", (4.55, 0.85, 0.62), (5.7, 2.35, 2.25), white, col, 0.08)
    geo.box("TRUCK_windscreen", (5.68, 0.95, 1.45), (5.72, 2.25, 2.1), m["window_glass"], col, 0.01)
    geo.box("TRUCK_side_window", (4.75, 0.83, 1.5), (5.45, 0.85, 2.05), m["window_glass"], col, 0.01)
    geo.box("TRUCK_bumper", (5.7, 0.85, 0.45), (5.8, 2.35, 0.68), m["steel_dark"], col, 0.02)
    for i, (x, y) in enumerate(((1.7, 0.68), (1.7, 2.42), (4.0, 0.68), (4.0, 2.42), (5.2, 0.7), (5.2, 2.4))):
        geo.cylinder(f"TRUCK_wheel{i}", (x, y - 0.06, 0.38), 0.38, 0.12, m["auto_dark"], col, axis="Y", segments=28, bevel=0.02)
    # built as if at the bay, then moved out onto the road at the kerb: vehicles stay off the footpath
    from mathutils import Vector
    off = Vector((0.0, -2.95, kit.ROAD_Z))
    root = geo.empty("TRUCK_root", (0, 0, 0), col)
    for o in list(col.objects):
        if o is not root and o.parent is None:
            o.parent = root
    root.location = off
    st.anchor("truck_bay", Vector((3.0, 1.6, 2.95)) + off)
    st.anchor("truck_rear", Vector((1.15, 1.6, 1.5)) + off)


def dress(st):
    s, m, col = st.street, st.m, st.props
    loader = people.costume_materials("loader", shirt="#5A6670", trousers="#3A3633", cap=None)
    people.figure("LOADER", (0.3, 1.25, 0), 70, loader, (-0.3, 0.02, 0.6), (0.3, 0.02, 0.6), col)
    kit.lamp_pole("POLE", 6.4, 0.3, m, col, height=7.0)
    kit.bollards("BOLLARD", (-4.6, -0.8), 1.3, m, col)
    kit.ph("JERRYCAN", "plastic_jerrycan", (0.35, 2.6, BAY_TOP), 15, 1.0, col)
    kit.ph("BIN", "metal_trash_can", (-4.7, 2.6, 0), 0, 1.0, col)
    kit.ph("HAND_truck", "hand_truck", (-0.2, 2.5, BAY_TOP), -40, 1.0, col)
    kit.road(s, m, st.set)
    kit.autorickshaw("AUTO_0", (-3.2, -1.25, kit.ROAD_Z), 0, m, col)
    kit.wire("WIRE_0", (s.x0, 2.9, 5.6), (6.4, 0.3, 6.6), 0.35, m["cable"], col)
    # a few late passers-by, cables and crows (V01, V03)
    street_life.wires(st, s.x0, 1.1)
    street_life.crows(st, (-3.6, -1.0), 4.25)
    street_life.people(st, [("PED_kurta", (2.4, 0.4), 95, "kurta", 0.14), ("PED_lungi", (-2.0, 0.55), -85, "lungi", 0.12)])


def build():
    st = s03.ArtStation(SET_DATA)
    s03.set_materials(st.m)
    kit.kit_materials(st.m)
    st.m.setdefault("pole", M.plaster("MAT_pole", "#9C978E", 0.2))
    kit.plinth(st.street, st.m, st.set)
    bay(st)
    crates(st)
    truck(st)
    dress(st)
    st.anchor("exit", (6.5, 1.2, 0.0))
    st.finish(TARGET)


if __name__ == "__main__":
    build()
