"""Station 4, the roof: the hub's solar through the evening and the power cut. Builds
art/blender/s04_roof.blend (scene id "s04roof", so its renders and packed layers sit beside s04's).

Run:  blender -b --python art/scripts/s04roof_build.py
Then: blender -b art/blender/s04_roof.blend --python art/scripts/render_station.py -- --only bg
      blender -b art/blender/s04_roof.blend --python art/scripts/render_station.py -- --preset dusk --only bg_dusk
      blender -b art/blender/s04_roof.blend --python art/scripts/render_station.py -- --preset night --power-cut --only bg_night
      python tools/pack_layers.py s04roof

Re-runnable. Destructive only to art/blender/s04_roof.blend, which lib/safety backs up first.

Station04 plays these three renders as a time-lapse under a Phaser sky: day, dusk with the
neighbourhood's windows lit, then the grid goes and only the hub stays lit, on its own solar
(the skylight over the chambers and the stair-room lamp are never practical). Then the camera
zooms into the skylight, back to the chambers.

Sources: the hub, its panels, inverter and battery are our proposal (art bible §0 gap: generic,
clean, not shiny, §4). The rooftops, water tanks, wires and the minaret after F01/F02 and R19,
R22 (Tier A); Russell Market's white masonry (X04/R24) for the hub's own walls.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import rig  # noqa: E402
import s03_art_build as s03  # noqa: E402
from mathutils import Matrix  # noqa: E402

SET_DATA = {
    "id": "s04roof",
    "set": {"blend": "art/blender/s04_roof.blend", "lighting": "midday", "street": {"x0": -4.5, "x1": 4.5}},
    "signs": [],
}
TARGET = (0.6, 5.2, 1.6)                 # back and up: the skyline fills the top of the frame
DECK = dict(x0=-4.5, x1=4.5, y0=0.0, y1=6.0)
PANELS = [(-2.9 + i * 1.15, 2.4 + r * 1.3) for r in range(2) for i in range(3)]      # panel centres
STAIR = dict(x0=2.3, x1=3.9, y0=3.6, y1=5.4, top=2.4)
SKYLIGHT = dict(x0=-3.9, x1=-2.9, y0=0.6, y1=1.4)


def materials(m):
    s03.set_materials(m)
    m.update(
        roof=M.plaster("MAT_roof_deck", "#B8B0A2", 0.3, floor_z=-1.0),
        parapet=s03.masonry_faint("MAT_parapet_masonry"),
        neighbour_a=M.plaster("MAT_neighbour_a", "#CDBFA6", 0.35, floor_z=-6.0),
        neighbour_b=M.plaster("MAT_neighbour_b", "#B9A99A", 0.4, floor_z=-6.0),
        neighbour_c=M.plaster("MAT_neighbour_c", "env.plaster", 0.45, floor_z=-6.0),
        window_lit=M.emissive("MAT_window_lit", "#FFCF8A", 5.0),
        tank=M.plastic("MAT_water_tank", "#2B2A2A", 0.45),
        skylight=M.emissive("MAT_skylight_glow", "#DDEBF0", 6.0),
        lamp=M.emissive("MAT_stair_lamp", "#F2F2E6", 8.0),
        minaret=M.plaster("MAT_minaret", "#D8D6CC", 0.15, floor_z=-6.0),
    )


def deck(st):
    """The hub's roof: deck, parapet, the building's front cut as a section down out of frame."""
    m, col, d = st.m, st.set, DECK
    geo.box("ROOF_deck", (d["x0"], d["y0"], -0.15), (d["x1"], d["y1"], 0), m["roof"], col, geo.BEVEL_ARCH)
    # the building is cut just below the deck, as a model section (§6.1), so the roof is the subject
    geo.box("ROOF_front_wall", (d["x0"], d["y0"] - 0.25, -0.5), (d["x1"], d["y0"], 0.9), m["parapet"], col, geo.BEVEL_ARCH)
    geo.box("ROOF_side_wall", (d["x1"], d["y0"] - 0.25, -0.5), (d["x1"] + 0.25, d["y1"], 0.9), m["parapet"], col, geo.BEVEL_ARCH)
    geo.box("ROOF_section", (d["x0"] - 0.25, d["y0"] - 0.25, -0.75), (d["x1"] + 0.25, d["y1"] + 0.25, -0.5), m["section"], col, 0)
    geo.box("ROOF_parapet_back", (d["x0"], d["y1"], 0), (d["x1"] + 0.25, d["y1"] + 0.25, 0.9), m["parapet"], col, geo.BEVEL_ARCH)
    geo.box("ROOF_parapet_left", (d["x0"] - 0.25, d["y0"] - 0.25, 0), (d["x0"], d["y1"] + 0.25, 0.9), m["parapet"], col, geo.BEVEL_ARCH)
    geo.box("ROOF_coping", (d["x0"] - 0.28, d["y0"] - 0.3, 0.9), (d["x1"] + 0.28, d["y0"] + 0.02, 0.97), m["parapet"], col, geo.BEVEL_PROP)


def solar(st):
    """Six panels on low steel frames, tilted to the sky, wired to the inverter by the stair room;
    a conduit from there to the skylight over the chambers."""
    m, col = st.m, st.set
    tilt = Matrix.Rotation(math.radians(-15), 4, "X")
    for i, (x, y) in enumerate(PANELS):
        for name, size, mat in ((f"SOLAR_cells{i}", (0.5, 0.6, 0.02), m["solar"]), (f"SOLAR_frame{i}", (0.53, 0.63, 0.012), m["steel"])):
            o = geo.box(name, (-size[0], -size[1], -size[2]), (size[0], size[1], size[2] - (0.016 if "frame" in name else 0)), mat, col, 0.004)
            o.matrix_world = Matrix.Translation((x, y, 0.55)) @ tilt
        for j, dy in enumerate((-0.45, 0.45)):
            geo.limb(f"SOLAR_leg{i}{j}", (x, y + dy, 0), (x, y + dy, 0.55 - dy * 0.27), 0.02, 0.02, m["steel_dark"], col)
    inv = (STAIR["x0"] - 0.05, STAIR["y0"] + 0.3)
    geo.box("SOLAR_inverter", (inv[0] - 0.22, inv[1], 0.7), (inv[0], inv[1] + 0.5, 1.5), m["condenser"], col, 0.02)
    geo.box("SOLAR_battery", (inv[0] - 0.5, inv[1] - 0.1, 0), (inv[0], inv[1] + 0.6, 0.55), m["condenser"], col, 0.02)
    geo.sphere("SOLAR_led", (inv[0] - 0.225, inv[1] + 0.25, 1.4), 0.02, (0.5, 1, 1), m["lamp"], col)
    run = [(PANELS[2][0] + 0.5, PANELS[2][1], 0.12), (inv[0] - 0.3, PANELS[2][1], 0.12), (inv[0] - 0.3, inv[1] + 0.25, 0.12)]
    for k in range(len(run) - 1):
        geo.limb(f"SOLAR_cable{k}", run[k], run[k + 1], 0.02, 0.02, m["pipe"], col)
    sk = ((SKYLIGHT["x0"] + SKYLIGHT["x1"]) / 2, (SKYLIGHT["y0"] + SKYLIGHT["y1"]) / 2)
    feed = [(inv[0] - 0.5, inv[1] - 0.05, 0.08), (inv[0] - 0.5, 1.0, 0.08), (sk[0] + 0.55, 1.0, 0.08)]
    for k in range(len(feed) - 1):
        geo.limb(f"SOLAR_feed{k}", feed[k], feed[k + 1], 0.025, 0.025, m["pipe"], col)
    st.anchor("panels", (PANELS[1][0], (PANELS[1][1] + PANELS[4][1]) / 2, 0.7))
    st.anchor("inverter", (inv[0] - 0.11, inv[1] + 0.25, 1.1))
    for i, (x, y) in enumerate(PANELS):
        st.anchor(f"panel_{i}", (x, y, 0.62))


def hub_roof_fixtures(st):
    """The stair room with its solar-fed lamp, the skylight over the cold room, a water tank."""
    m, col, s = st.m, st.set, STAIR
    geo.box("STAIR_room", (s["x0"], s["y0"], 0), (s["x1"], s["y1"], s["top"]), m["parapet"], col, geo.BEVEL_ARCH)
    geo.box("STAIR_door", (s["x0"] + 0.4, s["y0"] - 0.02, 0), (s["x0"] + 1.2, s["y0"], 2.0), m["window_frame"], col, 0.01)
    geo.sphere("STAIR_lamp", (s["x0"] + 0.8, s["y0"] - 0.08, 2.15), 0.06, (1, 0.6, 0.8), m["lamp"], col)
    rig.point_light("LIGHT_stair_lamp", (s["x0"] + 0.8, s["y0"] - 0.35, 2.05), (1.0, 0.95, 0.85), 60, 0.1, col)      # solar: never practical
    k = SKYLIGHT
    geo.box("SKYLIGHT_curb", (k["x0"] - 0.08, k["y0"] - 0.08, 0), (k["x1"] + 0.08, k["y1"] + 0.08, 0.25), m["steel_dark"], col, 0.01)
    geo.box("SKYLIGHT_glass", (k["x0"], k["y0"], 0.25), (k["x1"], k["y1"], 0.3), m["skylight"], col, 0.005)
    rig.point_light("LIGHT_skylight", ((k["x0"] + k["x1"]) / 2, (k["y0"] + k["y1"]) / 2, 0.8), (0.87, 0.93, 0.96), 40, 0.4, col)
    st.anchor("skylight", ((k["x0"] + k["x1"]) / 2, (k["y0"] + k["y1"]) / 2, 0.3))
    geo.box("TANK_stand", (3.0, 0.6, 0), (4.0, 1.6, 0.6), m["steel_dark"], col, 0.01)
    geo.cylinder("TANK", (3.5, 1.1, 0.6), 0.48, 1.1, m["tank"], col, segments=32)
    for z in (0.85, 1.15, 1.45):
        geo.cylinder(f"TANK_rib{z:.2f}", (3.5, 1.1, z), 0.49, 0.03, m["tank"], col, segments=32, bevel=0)


def neighbours(st):
    """The rooftops around: lower and higher blocks with windows that light at dusk (mains:
    practical, so they go dark in the cut), wires between them, a minaret on the skyline (R22)."""
    m, col = st.m, st.set
    blocks = ((-9.0, -6.7, 4.0, 9.0, 5.2, "neighbour_c"), (-6.5, -4.6, 6.5, 10.0, 2.8, "neighbour_a"), (-4.4, -0.8, 6.8, 9.5, 1.6, "neighbour_b"),
              (-0.6, 3.0, 6.6, 11.0, 4.2, "neighbour_c"), (3.2, 6.5, 6.6, 9.0, 0.9, "neighbour_a"),
              (4.9, 7.5, -1.0, 6.0, -1.0, "neighbour_b"))
    n = 0
    for i, (x0, x1, y0, y1, top, mat) in enumerate(blocks):
        geo.box(f"NBR_{i}", (x0, y0, -4.0), (x1, y1, top), m[mat], col, geo.BEVEL_ARCH)
        face_y = y0 if y0 > DECK["y1"] else None
        for row in range(3):
            z = top - 1.1 - row * 1.6
            if z < -3.5:
                break
            for x in [x0 + 0.5 + k * 1.0 for k in range(int((x1 - x0 - 0.4) / 1.0))]:
                if face_y is not None:
                    geo.box(f"NBR_{i}_win{n}", (x, face_y - 0.02, z), (x + 0.5, face_y, z + 0.8), m["window_glass"], col, 0)
                    lit = geo.box(f"NBR_{i}_lit{n}", (x + 0.04, face_y - 0.03, z + 0.04), (x + 0.46, face_y - 0.02, z + 0.76), m["window_lit"], col, 0)
                else:
                    geo.box(f"NBR_{i}_win{n}", (x1, y0 + 0.6 + (x - x0), z), (x1 + 0.02, y0 + 1.1 + (x - x0), z + 0.8), m["window_glass"], col, 0)
                    lit = geo.box(f"NBR_{i}_lit{n}", (x1 + 0.02, y0 + 0.64 + (x - x0), z + 0.04), (x1 + 0.03, y0 + 1.06 + (x - x0), z + 0.76), m["window_lit"], col, 0)
                lit["practical"] = True
                n += 1
        light = rig.point_light(f"LIGHT_nbr_{i}", ((x0 + x1) / 2, (y0 if face_y else y1) - 0.6, top - 1.6), (1.0, 0.8, 0.55), 120, 0.5, col)
        light["practical"] = True
    for i, (a, b) in enumerate((((-4.6, 6.5, 2.6), (0.0, 6.6, 3.9)), ((3.0, 6.6, 3.5), (5.6, 5.5, 0.6)))):
        kit.wire(f"WIRE_{i}", a, b, 0.35, m["cable"], col)
    geo.cylinder("MINARET", (6.4, 12.5, -4.0), 0.55, 10.5, m["minaret"], col, segments=24, bevel=0, radius2=0.42)
    geo.cylinder("MINARET_balcony", (6.4, 12.5, 4.6), 0.75, 0.15, m["minaret"], col, segments=24)
    geo.sphere("MINARET_dome", (6.4, 12.5, 6.6), 0.5, (1, 1, 1.2), m["minaret"], col)


def build():
    st = s03.ArtStation(SET_DATA)
    materials(st.m)
    deck(st)
    solar(st)
    hub_roof_fixtures(st)
    neighbours(st)
    st.finish(TARGET)


if __name__ == "__main__":
    build()
