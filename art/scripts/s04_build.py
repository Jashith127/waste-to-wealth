"""Station 4 · Cold room (Run 2). Builds art/blender/s04_cold.blend.

Run:  blender -b --python art/scripts/s04_build.py
Then: blender -b art/blender/s04_cold.blend --python art/scripts/render_station.py
      blender -b art/blender/s04_cold.blend --python art/scripts/render_station.py -- --preset night --power-cut --only bg_night,riyaz_idle_night,door_a_night,door_b_night,door_a_open_night,door_b_open_night
      python tools/pack_layers.py s04

Re-runnable. Destructive only to art/blender/s04_cold.blend, which lib/safety backs up first.

Inside the hub: the inside face of the same wall s03 shows from the street, at the same x
positions and in the same order: the two chambers (same insulated panels, doors and bands), the
cooling unit beside Door B, the entrance opening with its jali arch as the window (lit from the
street), the solar unit on the right bay. Each chamber is a pass-through: a door on the hall side
here, and its street-side door (with a lit porthole) at the far end, seen when the hall door is
open. A steel table with the tray of unsold meat, the sealed crate, Riyaz. The cold room is our proposal
(art bible §0 gap): generic, clean but not shiny (§4). The room is lit by its practicals only (no
sun reaches inside), so the power-cut render (practicals off) goes dark while the chamber windows,
an FX layer on solar, stay lit (§5: sold by what goes off).

Sources: s03 cold-room front (this repo); tray after F03's steel trays and the s01 leftovers tray;
interior tiles and wet floor R09/R11 (F03, F04); hose and drain, deck p. 34 (Five senses: Touch).
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import geo  # noqa: E402
import kit  # noqa: E402
import people  # noqa: E402
import rig  # noqa: E402
import s03_art_build as s03  # noqa: E402  (shared materials and the crate, so s03 and s04 match)
import station  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

TARGET = (-1.1, 2.0, 1.6)                # centred on the room, which is left of the entrance as the block is in s03
ROOM = dict(x0=-5.0, x1=2.7, back=3.0, front=1.0, height=3.7, low=2.5)      # low: the side wall and the left bay
BLOCK = dict(x0=-4.8, x1=-1.5, top=2.4)                          # the cold-room block: s03's COLD
DOORS = {"a": (-4.55, -3.65), "b": (-2.65, -1.75)}               # s03's doors: 0.9 m wide, 1 m apart
OPEN_X = (-1.2, 1.2)                                             # the entrance: s03's OPEN_X
LINTEL_Z = 2.25
WINDOW_Z = 1.72
CHAMBER_DEPTH = 1.1
CRATE_AT = Vector((-2.2, 2.1, 0.0))                              # on the floor in front of Chamber B
TABLE = dict(x0=-4.95, x1=-4.4, y0=1.1, y1=1.9, top=0.85)        # steel table beside Chamber A
TRAY_AT = Vector((-4.675, 1.5, TABLE["top"]))
RIYAZ_AT = (-3.2, 1.25, 0.0)                                     # between the two doors
SOLAR_BOX = dict(x0=1.7, x1=2.25, z0=1.25, z1=1.95)               # right bay, as the blind arch bay in s03
COOLING = dict(x0=-1.66, x1=-1.22, z0=1.35, z1=2.05, depth=0.32)    # between Door B and the entrance, as in s03


def floor_damp(name):
    """The hub's floor: wet stone (R11), but damp rather than mirror-wet, so the hidden idle legs
    used for shadows do not show up in reflections."""
    n = s03.M.Nodes(name)
    n.link(n.mix(n.noise(5.0, 8, 0.7), s03.M.rgb("env.floor-wet"), s03.M.rgb("#2E2926")), n.bsdf.inputs["Base Color"])
    n.link(n.maprange(n.noise(2.0, 2), 0.4, 0.6, 0.38, 0.62), n.bsdf.inputs["Roughness"])
    return n.mat


def jali_lit(name):
    """The entrance's jali seen from inside, against the evening: dark stone lattice, and the
    holes full of light. (s03's jali is the same pattern seen from the street, white on dark.)"""
    n = s03.M.Nodes(name)
    brick = n.add("ShaderNodeTexBrick")
    brick.offset, brick.squash = 0.5, 1.0
    brick.inputs["Scale"].default_value = 6.0
    brick.inputs["Mortar Size"].default_value = 0.05
    brick.inputs["Brick Width"].default_value = 0.42
    brick.inputs["Row Height"].default_value = 0.42
    brick.inputs["Color1"].default_value = s03.M.rgb("#F6D9AA")
    brick.inputs["Color2"].default_value = s03.M.rgb("#EFCB98")
    brick.inputs["Mortar"].default_value = s03.M.rgb("#3A332D")
    n.link(n.planar(), brick.inputs["Vector"])
    n.link(brick.outputs["Color"], n.bsdf.inputs["Emission Color"])
    n.set("Emission Strength", 4.0)
    n.set("Base Color", s03.M.rgb("#3A332D"))
    n.set("Roughness", 0.8)
    return n.mat


def street_view(name):
    """The lane beyond the entrance at evening: warm sky down to a paler, dustier ground."""
    n = s03.M.Nodes(name)
    sky = n.mix(n.height_mask(0.5, 2.4), s03.M.rgb("#F5C58F"), s03.M.rgb("#D9CDB8"))
    n.link(sky, n.bsdf.inputs["Emission Color"])
    n.set("Emission Strength", 2.6)
    n.set("Base Color", s03.M.rgb("#2A2420"))
    return n.mat


def room(st):
    """Floor with its cut edge, tiled side wall, the facade's inside face as the back wall (block with
    panels left, entrance opening middle, right bay), sections, practicals."""
    m, col, r = st.m, st.set, ROOM
    y, H = r["back"], r["height"]
    geo.box("FLOOR", (r["x0"], r["front"], -0.06), (r["x1"], y + 0.6, 0), m["floor"], col, geo.BEVEL_ARCH)
    geo.box("FLOOR_bedding", (r["x0"], r["front"], -0.12), (r["x1"], y + 0.6, -0.06), m["bedding"], col, 0)
    geo.box("FLOOR_soil", (r["x0"], r["front"], -0.25), (r["x1"], y + 0.6, -0.12), m["soil"], col, 0)
    geo.box("FLOOR_drain", (-0.5, 1.2, -0.004), (-0.2, 1.5, 0.004), m["grate"], col, 0.003)
    # side wall, tiled, cut at the front edge like a model section (6.1)
    geo.box("WALL_side", (r["x0"] - 0.2, r["front"] + 0.3, 0), (r["x0"], y + 0.6, r["low"]), m["tiles_in"], col, 0)
    geo.box("WALL_side_section", (r["x0"] - 0.2, r["front"] + 0.28, 0), (r["x0"], r["front"] + 0.3, r["low"]), m["section"], col, 0)
    # the cold-room block: insulated panels with seams around the two doors, a kick and a top trim
    b = BLOCK
    (a0, a1), (b0, b1) = DOORS["a"], DOORS["b"]
    for i, (x0, x1) in enumerate(((b["x0"], a0 - 0.05), (a1 + 0.05, b0 - 0.05), (b1 + 0.05, b["x1"]))):
        geo.box(f"COLD_front{i}", (x0, y, 0), (x1, y + 0.6, b["top"]), m["hub_panel"], col, 0.01)
    geo.box("COLD_front_over", (a0 - 0.05, y, 2.14), (b1 + 0.05, y + 0.6, b["top"]), m["hub_panel"], col, 0.01)
    geo.box("COLD_kick", (b["x0"], y - 0.02, 0), (b["x1"], y, 0.14), m["steel_dark"], col, 0.006)
    geo.box("COLD_trim", (b["x0"], y - 0.04, b["top"] - 0.1), (b["x1"], y, b["top"]), m["steel"], col, 0.006)
    for k, x in enumerate((-4.675, -3.1, -1.625)):
        geo.box(f"COLD_seam{k}", (x - 0.008, y - 0.006, 0.14), (x + 0.008, y, b["top"] - 0.1), m["hub_seam"], col, 0)
    # the rest of the wall, tiled: the left bay, the jamb, the right bay, and over the entrance
    geo.box("WALL_left_bay", (r["x0"], y, 0), (b["x0"], y + 0.6, r["low"]), m["tiles_in"], col, 0)
    geo.box("WALL_jamb", (b["x1"], y, 0), (OPEN_X[0], y + 0.6, H), m["tiles_in"], col, 0)
    geo.box("WALL_right", (OPEN_X[1], y, 0), (r["x1"], y + 0.6, H), m["tiles_in"], col, 0)
    geo.box("WALL_over", (OPEN_X[0], y, LINTEL_Z), (OPEN_X[1], y + 0.6, H), m["tiles_in"], col, 0)
    geo.box("ENTRANCE_lintel", (OPEN_X[0] - 0.1, y - 0.1, LINTEL_Z), (OPEN_X[1] + 0.1, y, LINTEL_Z + 0.2), m["masonry"], col, geo.BEVEL_ARCH)
    for side, (xa, xb) in (("L", (OPEN_X[0] - 0.1, OPEN_X[0])), ("R", (OPEN_X[1], OPEN_X[1] + 0.1))):
        geo.box(f"ENTRANCE_jamb_{side}", (xa, y - 0.1, 0), (xb, y, LINTEL_Z), m["masonry"], col, geo.BEVEL_ARCH)
    geo.box("ENTRANCE_step", (OPEN_X[0], y - 0.12, 0), (OPEN_X[1], y + 0.6, 0.03), m["steel_dark"], col, 0.006)
    # the street, seen through the entrance (the window to the outside): evening sky over the lane,
    # with the dark shapes of a pole, an auto and a passer-by against the light
    geo.box("STREET_glow", (OPEN_X[0] - 0.4, y + 0.9, 0), (OPEN_X[1] + 0.4, y + 0.92, LINTEL_Z + 0.3), m["street_view"], col, 0)
    sil = m["silhouette"]
    geo.limb("STREET_pole", (0.8, y + 0.85, 0), (0.8, y + 0.85, 2.4), 0.03, 0.025, sil, col)
    geo.box("STREET_wall", (-1.5, y + 0.8, 0), (-0.6, y + 0.88, 2.3), sil, col, 0.02)           # the far side of the lane
    geo.box("STREET_kerb", (-1.5, y + 0.8, 0), (1.5, y + 0.88, 0.35), sil, col, 0.02)
    geo.limb("STREET_person", (0.1, y + 0.8, 0.0), (0.1, y + 0.8, 1.4), 0.12, 0.1, sil, col)
    geo.sphere("STREET_person_head", (0.1, y + 0.8, 1.55), 0.1, (1, 1, 1), sil, col, segments=12, rings=8)
    # the jali arch over the entrance: s03's pointed arch and its moulded band, lit from behind
    s03.arch_fill("ENTRANCE_jali", 0.0, 2.2, LINTEL_Z + 0.25, 0.95, LINTEL_Z + 0.2, y - 0.02, m["jali_lit"], col)
    s03.arch_band("ENTRANCE_jali_arch", 0.0, 2.2, LINTEL_Z + 0.25, 0.95, LINTEL_Z + 0.2, 0.12, y - 0.04, m["masonry"], col)
    # clean model sections where the walls are cut (6.1), so no sky colour lands on them
    geo.box("WALL_section_end", (r["x1"], y, 0), (r["x1"] + 0.01, y + 0.6, H), m["section"], col, 0)
    geo.box("WALL_section_top_R", (OPEN_X[1], y, H), (r["x1"] + 0.01, y + 0.6, H + 0.01), m["section"], col, 0)
    geo.box("WALL_section_top_J", (b["x1"], y, H), (OPEN_X[1], y + 0.6, H + 0.01), m["section"], col, 0)
    geo.box("WALL_section_top_L", (r["x0"] - 0.2, y, r["low"]), (b["x0"], y + 0.6, r["low"] + 0.01), m["section"], col, 0)
    geo.box("WALL_side_top", (r["x0"] - 0.2, r["front"] + 0.28, r["low"]), (r["x0"], y, r["low"] + 0.01), m["section"], col, 0)
    # practical lights: a tube over the doors, a bulb over the table (mains: off in the power cut)
    practical = [
        geo.cylinder("ROOM_tube", (-4.5, y - 0.12, 2.3), 0.022, 2.9, m["tube"], col, axis="X", bevel=0),
        rig.point_light("LIGHT_tube", (-3.1, 1.9, 2.45), (0.95, 0.96, 0.91), 220, 0.5, col),
        geo.sphere("ROOM_bulb", (-4.7, 1.5, 2.2), 0.05, (1, 1, 1.25), m["bulb"], col),
        rig.point_light("LIGHT_bulb", (-4.7, 1.5, 2.1), (1.0, 0.79, 0.54), 70, 0.08, col),
        rig.point_light("LIGHT_fill", (-0.8, 0.9, 2.4), (0.95, 0.96, 0.91), 90, 0.6, col),
    ]
    for o in practical:
        o["practical"] = True
    geo.box("ROOM_tube_bracket", (-4.55, y - 0.14, 2.32), (-1.65, y, 2.36), m["steel_dark"], col, 0.004)
    geo.cylinder("ROOM_bulb_cord", (-4.7, 1.5, 2.25), 0.004, 0.55, m["cable"], col, bevel=0)
    # evening light from the street through the entrance: daylight, so on in the power cut too
    sky = rig.point_light("LIGHT_entrance", (0.0, 2.2, 1.7), (1.0, 0.76, 0.52), 160, 0.5, col)
    sky["window"] = True


def doors(st):
    """The two chambers and their doors. Each doorway is real: a frame, a PVC strip curtain and a
    cold, lit chamber behind it (A: racks of covered trays; B: sealed crates), on solar, so never
    practical. The doors are their own layers (PROP_door_a, PROP_door_a_open, ...), so the game can
    swing one open when something goes in, and only ever one at a time (task 04)."""
    m, col, y = st.m, st.set, ROOM["back"]
    for key, (x0, x1) in DOORS.items():
        K = key.upper()
        cx = (x0 + x1) / 2
        geo.box(f"DOOR_{K}_frame_L", (x0 - 0.05, y - 0.04, 0.12), (x0, y + 0.6, 2.14), m["steel"], col, 0.006)
        geo.box(f"DOOR_{K}_frame_R", (x1, y - 0.04, 0.12), (x1 + 0.05, y + 0.6, 2.14), m["steel"], col, 0.006)
        geo.box(f"DOOR_{K}_frame_T", (x0 - 0.05, y - 0.04, 2.1), (x1 + 0.05, y + 0.6, 2.14), m["steel"], col, 0.006)
        geo.box(f"DOOR_{K}_sill", (x0, y - 0.04, 0.0), (x1, y + 0.6, 0.12), m["steel_dark"], col, 0.006)
        # the chamber: 1.4 m deep, cold white panels, its own light (on solar). A pass-through: the
        # street-side door (s03's own door, seen from behind) closes the far end, its round window
        # full of evening light; shelving stands along both sides, leaving the aisle clear.
        back = y + 0.6 + CHAMBER_DEPTH
        geo.box(f"CHAMBER_{K}_floor", (x0 - 0.3, y + 0.6, 0), (x1 + 0.3, back, 0.12), m["steel_dark"], col, 0)
        geo.box(f"CHAMBER_{K}_back", (x0 - 0.3, back, 0), (x1 + 0.3, back + 0.1, 2.4), m["chamber"], col, 0)
        geo.box(f"CHAMBER_{K}_side", (x0 - 0.3, y + 0.6, 0), (x0 - 0.2, back, 2.4), m["chamber"], col, 0)
        geo.box(f"CHAMBER_{K}_ceiling", (x0 - 0.3, y + 0.6, 2.3), (x1 + 0.3, back, 2.4), m["chamber"], col, 0)
        geo.box(f"CHAMBER_{K}_street_door", (x0, back - 0.05, 0.12), (x1, back, 2.1), m["hub_panel"], col, 0.01)
        geo.box(f"CHAMBER_{K}_street_frame", (x0 - 0.05, back - 0.04, 0.1), (x1 + 0.05, back, 2.14), m["steel"], col, 0.008)
        geo.box(f"CHAMBER_{K}_street_lever", (x0 + 0.1, back - 0.11, 1.06), (x0 + 0.32, back - 0.05, 1.1), m["steel"], col, 0.008)
        geo.cylinder(f"CHAMBER_{K}_street_ring", (cx, back - 0.062, WINDOW_Z), 0.13, 0.012, m["steel"], col, axis="Y", bevel=0)
        geo.cylinder(f"CHAMBER_{K}_street_window", (cx, back - 0.07, WINDOW_Z), 0.11, 0.008, m["window_evening"], col, axis="Y", bevel=0)
        for k, z in enumerate((0.5, 1.05, 1.6)):
            for side, (sx0, sx1) in (("l", (x0 - 0.2, x0 + 0.05)), ("r", (x1 - 0.05, x1 + 0.2))):
                geo.box(f"CHAMBER_{K}_shelf{k}{side}", (sx0, y + 0.7, z), (sx1, back - 0.15, z + 0.03), m["steel"], col, 0.004)
                for j in range(3):
                    yy = y + 0.78 + j * 0.37
                    if key == "a":      # covered trays of meat waiting overnight
                        geo.box(f"CHAMBER_A_tray{k}{side}{j}", (sx0 + 0.01, yy, z + 0.03), (sx1 - 0.01, yy + 0.3, z + 0.1), m["steel"], col, 0.006)
                        geo.box(f"CHAMBER_A_cover{k}{side}{j}", (sx0 + 0.02, yy + 0.01, z + 0.1), (sx1 - 0.02, yy + 0.29, z + 0.13), m["cling"], col, 0.01, subsurf=1)
                    elif k < 2:          # sealed crates for the bulk pickup
                        geo.box(f"CHAMBER_B_crate{k}{side}{j}", (sx0, yy, z + 0.03), (sx1, yy + 0.32, z + 0.3), m["crate"], col, 0.012)
        geo.panel(f"CHAMBER_{K}_lamp", (cx, (y + back) / 2, 2.29), (0.6, 0.12), "+Z", m["glow"], col)
        rig.point_light(f"LIGHT_chamber_{key}", (cx, y + 1.0, 2.0), (0.87, 0.93, 0.96), 90, 0.3, col)
        # PVC strip curtain hanging in the doorway
        for j in range(5):
            xx = x0 + 0.08 + j * (x1 - x0 - 0.16) / 4
            geo.box(f"DOOR_{K}_strip{j}", (xx - 0.04, y + 0.05, 0.16), (xx + 0.04, y + 0.058, 2.08), m["strip"], col, 0)
        door_panel(st, key, x0, x1, closed=True)
        door_panel(st, key, x0, x1, closed=False)
        st.anchor(f"door_{key}", (cx, y - 0.08, 1.05))
        st.anchor(f"door_{key}_label", (cx, y - 0.08, 2.35))
    st.anchor("rule", ((DOORS["a"][1] + DOORS["b"][0]) / 2, y - 0.05, 1.4))


def door_panel(st, key, x0, x1, closed):
    """One insulated door, as on the s03 exterior: band, kick plate, lever, a round window lit from
    the chamber. Hinged on its left edge; open, it swings out into the room."""
    m, y = st.m, ROOM["back"]
    K = key.upper()
    name = f"door_{key}" + ("" if closed else "_open")
    col = st.prop(name)
    hinge = geo.empty(f"{name}_hinge", (x0, y - 0.03, 0), col)
    parts = [
        geo.box(f"{name}_panel", (x0, y - 0.07, 0.14), (x1, y - 0.03, 2.1), m["hub_panel"], col, 0.012),
        geo.box(f"{name}_band", (x0, y - 0.075, 1.36), (x1, y - 0.068, 1.5), m[f"band_{key}"], col, 0.003),
        geo.box(f"{name}_kick", (x0 + 0.02, y - 0.075, 0.16), (x1 - 0.02, y - 0.068, 0.38), m["steel"], col, 0.004),
        geo.box(f"{name}_hinge_box", (x1 - 0.15, y - 0.11, 1.0), (x1 - 0.09, y - 0.07, 1.16), m["steel_dark"], col, 0.006),
        geo.box(f"{name}_lever", (x1 - 0.32, y - 0.14, 1.06), (x1 - 0.1, y - 0.11, 1.1), m["steel"], col, 0.008),
        geo.cylinder(f"{name}_window_ring", ((x0 + x1) / 2, y - 0.082, WINDOW_Z), 0.13, 0.012, m["steel"], col, axis="Y", bevel=0),
        geo.cylinder(f"{name}_window", ((x0 + x1) / 2, y - 0.088, WINDOW_Z), 0.11, 0.008, m["glow"], col, axis="Y", bevel=0),
    ]
    for o in parts:                                  # pivot on the hinge: parts stay where they were built
        o.parent = hinge
        o.matrix_parent_inverse = Matrix.Translation(-hinge.location)
    if not closed:
        hinge.rotation_euler = (0, 0, math.radians(-105))


def solar_unit(st):
    """The solar unit's wall box (inverter and battery), a blank status screen and a small lamp, in the
    right bay, its conduit running up and over the entrance to the cold block's roof. Off the grid:
    never practical."""
    m, col, b, y = st.m, st.set, SOLAR_BOX, ROOM["back"]
    cx = (b["x0"] + b["x1"]) / 2
    top = ROOM["height"] - 0.06
    geo.box("SOLAR_box", (b["x0"], y - 0.22, b["z0"]), (b["x1"], y, b["z1"]), m["condenser"], col, 0.02)
    geo.box("SOLAR_screen", (b["x0"] + 0.1, y - 0.226, b["z1"] - 0.24), (b["x1"] - 0.1, y - 0.22, b["z1"] - 0.08), m["display"], col, 0.003)
    geo.sphere("SOLAR_lamp", (cx, y - 0.225, b["z0"] + 0.14), 0.022, (1, 0.5, 1), m["lamp"], col)
    geo.limb("SOLAR_conduit_up", (cx, y - 0.04, b["z1"]), (cx, y - 0.04, top), 0.018, 0.018, m["pipe"], col)
    geo.limb("SOLAR_conduit_run", (cx, y - 0.04, top), (BLOCK["x1"] + 0.1, y - 0.04, top), 0.018, 0.018, m["pipe"], col)
    st.anchor("solar", (cx, y - 0.23, (b["z0"] + b["z1"]) / 2))


def cooling_unit(st):
    """The cold room's cooling unit, as seen outside in s03: a pale box with a ringed, guarded fan a
    hand's width from Door B, two refrigerant pipes going up into the roof. Here it faces the room."""
    m, col, c, y = st.m, st.set, COOLING, ROOM["back"]
    cx, cz, d = (c["x0"] + c["x1"]) / 2, (c["z0"] + c["z1"]) / 2, c["depth"]
    fr = (c["x1"] - c["x0"]) * 0.46                      # the fan ring fills the box
    geo.box("COOLING_body", (c["x0"], y - d, c["z0"]), (c["x1"], y, c["z1"]), m["condenser"], col, 0.02)
    geo.cylinder("COOLING_fan_ring", (cx, y - d - 0.012, cz), fr, 0.012, m["steel_dark"], col, axis="Y", bevel=0)
    geo.cylinder("COOLING_fan", (cx, y - d - 0.018, cz), fr * 0.9, 0.006, m["cable"], col, axis="Y", bevel=0)
    for i, r in enumerate((fr * 0.3, fr * 0.6)):
        geo.cylinder(f"COOLING_guard{i}", (cx, y - d - 0.026, cz), r, 0.004, m["steel"], col, axis="Y", bevel=0, segments=32)
    for k in range(8):                                  # guard spokes
        a = math.pi * k / 4
        geo.limb(f"COOLING_spoke{k}", (cx, y - d - 0.03, cz), (cx + fr * 0.95 * math.cos(a), y - d - 0.03, cz + fr * 0.95 * math.sin(a)), 0.003, 0.003, m["steel"], col, segments=4)
    geo.limb("COOLING_pipe0", (c["x1"] - 0.1, y - 0.1, c["z1"]), (c["x1"] - 0.1, y - 0.1, ROOM["height"] - 0.03), 0.03, 0.03, m["pipe"], col)
    geo.limb("COOLING_pipe1", (c["x1"] - 0.2, y - 0.06, c["z1"]), (c["x1"] - 0.2, y - 0.06, ROOM["height"] - 0.03), 0.02, 0.02, m["steel"], col)
    st.anchor("cooling_unit", (cx, y - d, cz))


def cold_roof(st):
    """The cold block's roof over both chambers, with its solar panels as s03 shows them (tilted, in
    frames, on short legs), so the chambers do not read as dark boxes over the wall."""
    m, col, r, bl = st.m, st.set, ROOM, BLOCK
    y0, y1 = r["back"], r["back"] + 0.6 + CHAMBER_DEPTH + 0.2
    top = bl["top"]
    geo.box("COLD_roof", (bl["x0"] - 0.05, y0, top), (bl["x1"], y1, top + 0.1), m["hub_panel"], col, 0.01)
    geo.box("COLD_roof_lip", (bl["x0"] - 0.05, y1 - 0.06, top + 0.1), (bl["x1"], y1, top + 0.2), m["hub_panel"], col, 0.006)
    tilt = Matrix.Rotation(math.radians(-18), 4, "X")
    for i, x in enumerate((-4.05, -2.5)):
        cells = geo.box(f"ROOF_solar_cells{i}", (-0.52, -0.8, -0.02), (0.52, 0.8, 0.02), m["solar"], col, 0.004)
        frame = geo.box(f"ROOF_solar_frame{i}", (-0.55, -0.83, -0.035), (0.55, 0.83, -0.015), m["steel"], col, 0.004)
        for o in (cells, frame):
            o.matrix_world = Matrix.Translation((x, y0 + 0.95, top + 0.55)) @ tilt
        geo.limb(f"ROOF_solar_leg{i}", (x, y0 + 0.3, top + 0.1), (x, y0 + 0.3, top + 0.3), 0.02, 0.02, m["steel_dark"], col)
    sky = rig.point_light("LIGHT_roof_sky", (-3.1, y0 + 1.4, top + 1.6), (1.0, 0.86, 0.7), 260, 0.8, col)
    sky["window"] = True                                # evening light on the roof only: the wall and roof shade the room from it


def table_and_tray(st):
    """A steel prep table by Chamber A and PROP_meat_tray: the day's unsold meat on a steel tray
    (as the s01 leftovers tray, F03), matte, no blood (§4)."""
    m, col, t = st.m, st.set, TABLE
    geo.box("TABLE_top", (t["x0"], t["y0"], t["top"] - 0.04), (t["x1"], t["y1"], t["top"]), m["steel"], col, 0.008)
    geo.box("TABLE_shelf", (t["x0"] + 0.05, t["y0"] + 0.05, 0.22), (t["x1"] - 0.05, t["y1"] - 0.05, 0.25), m["steel"], col, 0.006)
    for i, (x, yy) in enumerate(((t["x0"] + 0.05, t["y0"] + 0.05), (t["x1"] - 0.05, t["y0"] + 0.05),
                                 (t["x0"] + 0.05, t["y1"] - 0.05), (t["x1"] - 0.05, t["y1"] - 0.05))):
        geo.cylinder(f"TABLE_leg{i}", (x, yy, 0), 0.022, t["top"] - 0.04, m["steel_dark"], col, bevel=0)
    tray = st.prop("meat_tray")
    x, yy, top = TRAY_AT
    w, d, h, th = 0.46, 0.32, 0.05, 0.012
    geo.box("TRAY_base", (x - w / 2, yy - d / 2, top), (x + w / 2, yy + d / 2, top + 0.018), m["steel"], tray, 0.008)
    for name, lo, hi in (("front", (x - w / 2, yy - d / 2, top + 0.012), (x + w / 2, yy - d / 2 + th, top + h)),
                         ("back", (x - w / 2, yy + d / 2 - th, top + 0.012), (x + w / 2, yy + d / 2, top + h)),
                         ("left", (x - w / 2, yy - d / 2, top + 0.012), (x - w / 2 + th, yy + d / 2, top + h)),
                         ("right", (x + w / 2 - th, yy - d / 2, top + 0.012), (x + w / 2, yy + d / 2, top + h))):
        geo.box(f"TRAY_rim_{name}", lo, hi, m["steel"], tray, 0.005)
    for i, (dx, dy, rot) in enumerate(((-0.11, -0.03, 0.0), (0.0, 0.05, 0.4), (0.11, -0.02, -0.3))):
        geo.sphere(f"TRAY_piece{i}", (x + dx, yy + dy, top + 0.05), 0.06, (1.3, 1.0, 0.5), m["meat"], tray, rot=(0, 0, rot))
    kit.shadow_catcher("TRAY_shadow_catcher", (x, yy, top + 0.001), (w + 0.1, d + 0.1), m, tray)
    st.anchor("meat_tray_centre", (x, yy, top + 0.08))


def details(st):
    """Wet-room details: a hose coiled on the side wall, a squeegee against it (deck p. 34)."""
    m, col = st.m, st.set
    hx, hy, hz, r = ROOM["x0"] + 0.03, 1.6, 1.25, 0.2
    pts = [(hx, hy + r * math.cos(a), hz + r * math.sin(a)) for a in (2 * math.pi * k / 14 for k in range(15))]
    for k in range(14):
        geo.limb(f"HOSE_{k}", pts[k], pts[k + 1], 0.02, 0.02, m["hose"], col)
    geo.box("HOSE_hook", (hx, hy - 0.03, hz + r - 0.02), (hx + 0.08, hy + 0.03, hz + r + 0.02), m["steel_dark"], col, 0.004)
    geo.limb("SQUEEGEE_handle", (ROOM["x0"] + 0.06, 2.6, 0.05), (ROOM["x0"] + 0.06, 2.75, 1.25), 0.014, 0.014, m["steel"], col)
    geo.box("SQUEEGEE_blade", (ROOM["x0"] + 0.02, 2.4, 0.0), (ROOM["x0"] + 0.12, 2.8, 0.08), m["cable"], col, 0.01)
    for i, (x, y, rr, sx) in enumerate(((-0.3, 1.3, 0.3, 1.8), (-3.9, 1.1, 0.22, 1.4))):
        p = geo.cylinder(f"PUDDLE_{i}", (x, y, 0.0), rr, 0.003, m["water"], col, segments=32, bevel=0)
        p.scale = (sx, 1.0, 1.0)


def riyaz(st):
    """Riyaz as in s01 and s03 (same costume, the clean worn apron), hands loose and still wet."""
    mats = people.costume_materials("riyaz", apron="#D6CFC0", cap="#E6E2D8", wet_hands=True)
    mats["apron"] = s03.apron_worn("MAT_riyaz_apron_worn")
    people.figure("RIYAZ_idle", RIYAZ_AT, 15, mats, (-0.34, 0.0, 0.62), (0.34, 0.0, 0.62), st.char("riyaz", "idle"))
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], 1.75))


def build():
    st = station.begin("s04")
    m = st.m
    s03.set_materials(m)
    m.update(
        glow=s03.M.emissive("MAT_chamber_glow", "#DDEBF0", 3.0),
        lamp=s03.M.emissive("MAT_solar_lamp", "#E9F1F2", 6.0),
        hose=s03.M.plastic("MAT_hose", "#4B5357", 0.5),
        chamber=s03.M.matte("MAT_chamber_panel", "#D4DADB", 0.5),
        cling=s03.M.glass("MAT_cling_film", "#E4E8E6"),
        strip=s03.M.glass("MAT_pvc_strip", "#C9D6DA"),
        floor=floor_damp("MAT_floor_damp"),
        water=s03.water("MAT_puddle_s04"),
        window_evening=s03.M.emissive("MAT_window_evening", "#F4D2A4", 2.0),
        jali_lit=jali_lit("MAT_jali_lit"),
        street_view=street_view("MAT_street_view"),
        silhouette=s03.M.matte("MAT_street_silhouette", "#2A2420", 0.9),
    )
    room(st)
    doors(st)
    solar_unit(st)
    cooling_unit(st)
    cold_roof(st)
    table_and_tray(st)
    details(st)
    s03.CRATE_AT = CRATE_AT                                   # the same sealed crate, here by Chamber B
    s03.crate(st)
    riyaz(st)
    kit.ph("HAND_truck", "hand_truck", (2.1, 2.1, 0), -50, 1.0, st.props)          # CC0, for moving crates
    kit.ph("JERRYCAN", "plastic_jerrycan", (2.45, 2.75, 0), 15, 1.0, st.props)
    st.anchor("exit", (0.0, 1.4, 0.0))                          # out through the entrance, to the pickup bay
    # Inside, no sun reaches the room: light it with its practicals and a dim sky (the night rig),
    # so the power-cut render goes dark when the practicals go off. The JSON keeps "midday" for the day.
    st.data["set"]["lighting"] = "night"
    st.finish(TARGET)


if __name__ == "__main__":
    build()
