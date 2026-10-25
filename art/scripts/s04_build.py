"""Station 4 · Cold room (Run 2). Builds art/blender/s04_cold.blend.

Run:  blender -b --python art/scripts/s04_build.py
Then: blender -b art/blender/s04_cold.blend --python art/scripts/render_station.py
      blender -b art/blender/s04_cold.blend --python art/scripts/render_station.py -- --preset night --power-cut --only bg_night,riyaz_idle_night,door_a_night,door_b_night,door_a_open_night,door_b_open_night
      python tools/pack_layers.py s04

Re-runnable. Destructive only to art/blender/s04_cold.blend, which lib/safety backs up first.

Inside the hub: the same two-chamber cold room seen from the street in s03 (same insulated
panels, doors and bands, so the two stations read as one building), the solar unit on the wall,
a steel table with the tray of unsold meat, the sealed crate, Riyaz. The cold room is our proposal
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
from mathutils import Vector  # noqa: E402

TARGET = (0.0, 2.0, 0.3)                 # low, so the crate and tray sit above the blueprint line
ROOM = dict(x0=-3.2, x1=3.6, back=3.0, front=0.0, height=2.8)
DOORS = {"a": (-1.5, -0.6), "b": (0.4, 1.3)}                    # 0.9 x 2.0 m, 1 m apart (task 04)
WINDOW_Z = 1.72
CRATE_AT = Vector((1.7, 2.35, 0.0))                              # on the floor by Chamber B
TABLE = dict(x0=-2.8, x1=-1.7, y0=1.7, y1=2.4, top=0.85)          # steel table by Chamber A
TRAY_AT = Vector((-2.25, 2.05, TABLE["top"]))
RIYAZ_AT = (-0.05, 1.45, 0.0)
SOLAR_BOX = dict(x0=2.0, x1=2.55, z0=1.25, z1=1.95)


def floor_damp(name):
    """The hub's floor: wet stone (R11), but damp rather than mirror-wet, so the hidden idle legs
    used for shadows do not show up in reflections."""
    n = s03.M.Nodes(name)
    n.link(n.mix(n.noise(5.0, 8, 0.7), s03.M.rgb("env.floor-wet"), s03.M.rgb("#2E2926")), n.bsdf.inputs["Base Color"])
    n.link(n.maprange(n.noise(2.0, 2), 0.4, 0.6, 0.38, 0.62), n.bsdf.inputs["Roughness"])
    return n.mat


def room(st):
    """Floor with its cut edge, the cold-room front as the back wall, a tiled side wall, practicals."""
    m, col, r = st.m, st.set, ROOM
    geo.box("FLOOR", (r["x0"], r["front"], -0.06), (r["x1"], r["back"] + 0.6, 0), m["floor"], col, geo.BEVEL_ARCH)
    geo.box("FLOOR_bedding", (r["x0"], r["front"], -0.12), (r["x1"], r["back"] + 0.6, -0.06), m["bedding"], col, 0)
    geo.box("FLOOR_soil", (r["x0"], r["front"], -0.25), (r["x1"], r["back"] + 0.6, -0.12), m["soil"], col, 0)
    geo.box("FLOOR_drain", (0.9, 0.9, -0.004), (1.2, 1.2, 0.004), m["grate"], col, 0.003)
    # side wall, tiled, cut at the front edge like a model section (§6.1)
    geo.box("WALL_side", (r["x0"] - 0.2, 0.9, 0), (r["x0"], r["back"] + 0.6, r["height"]), m["tiles_in"], col, 0)
    geo.box("WALL_side_section", (r["x0"] - 0.2, 0.88, 0), (r["x0"], 0.9, r["height"]), m["section"], col, 0)
    # the cold-room front: insulated panels with seams, a base kick and a top trim
    y = r["back"]
    (a0, a1), (b0, b1) = DOORS["a"], DOORS["b"]
    for i, (x0, x1) in enumerate(((r["x0"], a0 - 0.05), (a1 + 0.05, b0 - 0.05), (b1 + 0.05, r["x1"]))):
        geo.box(f"COLD_front{i}", (x0, y, 0), (x1, y + 0.6, r["height"]), m["hub_panel"], col, 0.01)
    geo.box("COLD_front_over", (a0 - 0.05, y, 2.14), (b1 + 0.05, y + 0.6, r["height"]), m["hub_panel"], col, 0.01)
    geo.box("COLD_kick", (r["x0"], y - 0.02, 0), (r["x1"], y, 0.14), m["steel_dark"], col, 0.006)
    geo.box("COLD_trim", (r["x0"], y - 0.04, r["height"] - 0.12), (r["x1"], y, r["height"]), m["steel"], col, 0.006)
    # clean model sections where the walls are cut (§6.1), so no sky colour lands on them
    geo.box("COLD_section_end", (r["x1"], y, 0), (r["x1"] + 0.01, y + 0.6, r["height"]), m["section"], col, 0)
    geo.box("COLD_section_top", (r["x0"] - 0.2, y, r["height"]), (r["x1"] + 0.01, y + 0.6, r["height"] + 0.01), m["section"], col, 0)
    geo.box("WALL_side_top", (r["x0"] - 0.2, 0.88, r["height"]), (r["x0"], y, r["height"] + 0.01), m["section"], col, 0)
    for k, x in enumerate((-2.4, 2.0, 2.9)):
        geo.box(f"COLD_seam{k}", (x - 0.008, y - 0.006, 0.14), (x + 0.008, y, r["height"] - 0.12), m["hub_seam"], col, 0)
    # practical lights: a tube over the doors, a bulb over the table (mains: off in the power cut)
    practical = [
        geo.cylinder("ROOM_tube", (-1.2, y - 0.12, 2.5), 0.022, 2.0, m["tube"], col, axis="X", bevel=0),
        rig.point_light("LIGHT_tube", (0.0, 1.9, 2.45), (0.95, 0.96, 0.91), 220, 0.5, col),
        geo.sphere("ROOM_bulb", (-2.25, 2.0, 2.2), 0.05, (1, 1, 1.25), m["bulb"], col),
        rig.point_light("LIGHT_bulb", (-2.25, 2.0, 2.1), (1.0, 0.79, 0.54), 70, 0.08, col),
        rig.point_light("LIGHT_fill", (1.5, 0.6, 2.4), (0.95, 0.96, 0.91), 90, 0.6, col),
    ]
    for o in practical:
        o["practical"] = True
    geo.box("ROOM_tube_bracket", (-1.25, y - 0.14, 2.52), (0.85, y, 2.56), m["steel_dark"], col, 0.004)
    geo.cylinder("ROOM_bulb_cord", (-2.25, 2.0, 2.25), 0.004, 0.55, m["cable"], col, bevel=0)


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
        # the chamber: 1.4 m deep, cold white panels, its own light (on solar)
        back = y + 0.6 + 1.4
        geo.box(f"CHAMBER_{K}_floor", (x0 - 0.3, y + 0.6, 0), (x1 + 0.3, back, 0.12), m["steel_dark"], col, 0)
        geo.box(f"CHAMBER_{K}_back", (x0 - 0.3, back, 0), (x1 + 0.3, back + 0.1, 2.4), m["chamber"], col, 0)
        geo.box(f"CHAMBER_{K}_side", (x0 - 0.3, y + 0.6, 0), (x0 - 0.2, back, 2.4), m["chamber"], col, 0)
        geo.box(f"CHAMBER_{K}_ceiling", (x0 - 0.3, y + 0.6, 2.3), (x1 + 0.3, back, 2.4), m["chamber"], col, 0)
        for k, z in enumerate((0.5, 1.05, 1.6)):
            geo.box(f"CHAMBER_{K}_shelf{k}", (x0 - 0.15, back - 0.55, z), (x1 + 0.15, back - 0.05, z + 0.03), m["steel"], col, 0.004)
            for j in range(3):
                xx = x0 + 0.02 + j * 0.3
                if key == "a":      # covered trays of meat waiting overnight
                    geo.box(f"CHAMBER_A_tray{k}{j}", (xx, back - 0.48, z + 0.03), (xx + 0.26, back - 0.12, z + 0.1), m["steel"], col, 0.006)
                    geo.box(f"CHAMBER_A_cover{k}{j}", (xx + 0.01, back - 0.47, z + 0.1), (xx + 0.25, back - 0.13, z + 0.13), m["cling"], col, 0.01, subsurf=1)
                elif k < 2:          # sealed crates for the bulk pickup
                    geo.box(f"CHAMBER_B_crate{k}{j}", (xx, back - 0.5, z + 0.03), (xx + 0.27, back - 0.1, z + 0.3), m["crate"], col, 0.012)
        geo.panel(f"CHAMBER_{K}_lamp", (cx, (y + back) / 2, 2.29), (0.6, 0.12), "+Z", m["glow"], col)
        rig.point_light(f"LIGHT_chamber_{key}", (cx, y + 1.2, 2.0), (0.87, 0.93, 0.96), 40, 0.3, col)
        # PVC strip curtain hanging in the doorway
        for j in range(6):
            xx = x0 + 0.04 + j * (x1 - x0 - 0.08) / 5
            geo.box(f"DOOR_{K}_strip{j}", (xx - 0.07, y + 0.05, 0.16), (xx + 0.07, y + 0.058, 2.08), m["strip"], col, 0)
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
    for o in parts:
        geo.parent_keep(o, hinge)
    if not closed:
        hinge.rotation_euler = (0, 0, math.radians(-105))


def solar_unit(st):
    """The solar unit's wall box (inverter and battery), a blank status screen and a small lamp,
    with its conduit running up and along to both doors. Off the grid: never practical."""
    m, col, b, y = st.m, st.set, SOLAR_BOX, ROOM["back"]
    geo.box("SOLAR_box", (b["x0"], y - 0.22, b["z0"]), (b["x1"], y, b["z1"]), m["condenser"], col, 0.02)
    geo.box("SOLAR_screen", (b["x0"] + 0.1, y - 0.226, b["z1"] - 0.24), (b["x1"] - 0.1, y - 0.22, b["z1"] - 0.08), m["display"], col, 0.003)
    geo.sphere("SOLAR_lamp", ((b["x0"] + b["x1"]) / 2, y - 0.225, b["z0"] + 0.14), 0.022, (1, 0.5, 1), m["lamp"], col)
    geo.limb("SOLAR_conduit_up", ((b["x0"] + b["x1"]) / 2, y - 0.04, b["z1"]), ((b["x0"] + b["x1"]) / 2, y - 0.04, 2.45), 0.018, 0.018, m["pipe"], col)
    geo.limb("SOLAR_conduit_run", (DOORS["a"][0] + 0.3, y - 0.04, 2.45), ((b["x0"] + b["x1"]) / 2, y - 0.04, 2.45), 0.018, 0.018, m["pipe"], col)
    for key, (x0, x1) in DOORS.items():
        geo.limb(f"SOLAR_drop_{key}", (x0 + 0.3, y - 0.04, 2.45), (x0 + 0.3, y - 0.04, 2.14), 0.014, 0.014, m["pipe"], col)
    st.anchor("solar", ((b["x0"] + b["x1"]) / 2, y - 0.23, (b["z0"] + b["z1"]) / 2))


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
    for i, (x, y, rr, sx) in enumerate(((0.6, 1.0, 0.3, 1.8), (-1.6, 1.0, 0.22, 1.4))):
        p = geo.cylinder(f"PUDDLE_{i}", (x, y, 0.0), rr, 0.003, m["water"], col, segments=32, bevel=0)
        p.scale = (sx, 1.0, 1.0)


def riyaz(st):
    """Riyaz as in s01 and s03 (same costume, the clean worn apron), hands loose and still wet."""
    mats = people.costume_materials("riyaz", apron="#D6CFC0", cap="#E6E2D8", wet_hands=True)
    mats["apron"] = s03.apron_worn("MAT_riyaz_apron_worn")
    people.figure("RIYAZ_idle", RIYAZ_AT, 15, mats, (-0.34, -0.12, 0.8), (0.34, -0.12, 0.8), st.char("riyaz", "idle"))
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
    )
    room(st)
    doors(st)
    solar_unit(st)
    table_and_tray(st)
    details(st)
    s03.CRATE_AT = CRATE_AT                                   # the same sealed crate, here by Chamber B
    s03.crate(st)
    riyaz(st)
    kit.ph("HAND_truck", "hand_truck", (2.9, 2.2, 0), -50, 1.0, st.props)          # CC0, for moving crates
    kit.ph("JERRYCAN", "plastic_jerrycan", (-2.95, 2.75, 0), 15, 1.0, st.props)
    st.anchor("exit", (3.2, 1.0, 0.0))
    # Inside, no sun reaches the room: light it with its practicals and a dim sky (the night rig),
    # so the power-cut render goes dark when the practicals go off. The JSON keeps "midday" for the day.
    st.data["set"]["lighting"] = "night"
    st.finish(TARGET)


if __name__ == "__main__":
    build()
