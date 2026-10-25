"""Station 3 · Weigh-in and payment, FINAL ART (task 14). Builds art/blender/s03_weighin.blend.

Run:  blender -b --python art/scripts/s03_art_build.py
Then: blender -b art/blender/s03_weighin.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s03

Separate from task 03's grey box (art/scripts/s03_build.py, the builder's file) so the two can
be made in parallel. It keeps every name and anchor task 03 specifies, so the packed layers drop
into Station03.ts unchanged: SCALE_platform + scale_pan, RATEBOARD_panel + rate_board,
PROP_crate + crate_centre / crate_knot, CHAR_attendant_idle / _type, CHAR_riyaz_idle.
Its set data lives in SET_DATA below, not in src/data/stations/s03.json (task 03 owns that file).

Re-runnable. Destructive only to art/blender/s03_weighin.blend, which lib/safety backs up first.

Sources (art bible §0; notes in review/s03-art-notes.md):
  Russell Market masonry, pointed arches, pilasters, the lintel and jali over the entrance:
      X04/R24 (2023, white) with the pink ghost of X03/R23 (decided §0).
  Counter: steel top as F04/R10; front in blue-and-white checker tiles, X05/R25.
  Crate: F03/R13 red crates for the form (ribbed, stackable, handholds); colour is the meaning
      blue of Chamber B (art bible §3.2), lid and clips because it is sealed (spec, station 4).
  Platform scale: gap in §0, generic form, no marks; the display is blank (Phaser draws 1.0 kg).
  Rate board: flex-banner frame after the F04 fascia; blank (Phaser draws params.rate_board).
  Cold room front, cooling unit, solar panel: gap in §0 (our proposal), generic, clean not shiny.
  Wet paving and drain: R07 paving, R11 wet floor, deck p. 34 (Five senses: Touch).
  Riyaz: s01 costume (deck p. 22 persona), wet hands held away from the body (deck p. 23).
  Attendant: our proposal, plain muted shirt and lanyard (task 14), typing the number (deck p. 26).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import bmesh  # noqa: E402
import bpy  # noqa: E402

import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import people  # noqa: E402
import rig  # noqa: E402
import safety  # noqa: E402
import station  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

SET_DATA = {
    "id": "s03",
    "set": {"blend": "art/blender/s03_weighin.blend", "lighting": "midday", "street": {"x0": -5.0, "x1": 6.0}},
    "signs": [],
}

TARGET = (0.0, 2.4, 0.5)                 # low, so the scale pan sits above the blueprint line (y 660)
OPEN_X = (-1.2, 1.2)                     # hub entrance in the central bay (R24: a lintelled door under a jali arch)
LINTEL_Z = 2.25
HUB_FLOOR = 0.15
COUNTER = dict(x0=0.25, x1=1.55, y0=2.1, y1=2.6, top=1.2)     # task 03: 1.2 m high; with the scale gap, 2 m wide
SCALE = dict(x0=-0.4, x1=0.2, y0=1.95, y1=2.55, top=0.12)      # task 03: about 0.6 x 0.6 m, 0.12 m high
CRATE_AT = Vector((-1.5, 1.0, 0.0))                              # on the wet paving, by Chamber B
CRATE = (0.55, 0.36, 0.30)                                       # task 03
COLD = dict(x0=-4.8, x1=-1.5, y0=1.7, top=2.4)                   # cold-room front, against the left bay
DOORS = {"a": (-4.55, -3.65), "b": (-2.65, -1.75)}               # 0.9 m doors, 1 m apart (task 04)
RIYAZ_AT = (-0.85, 1.55, 0.0)
RIYAZ_HEADING = 95                                               # three-quarters: toward the counter, face to camera
ATTENDANT_AT = (0.95, 2.85, HUB_FLOOR)
BOARD = dict(x0=2.3, x1=4.1, z0=0.85, z1=2.1)                    # rate board filling the right bay: room for 3 lines at 28 px


class ArtStation(station.Station):
    """station.Station, but with its set data from SET_DATA instead of src/data/stations/."""

    def __init__(self, data):
        self.id = data["id"]
        self.data = data
        self.blend = safety.REPO / data["set"]["blend"]
        self.street = kit.Street(**data["set"]["street"])
        self.anchors = {}
        self.target = None
        safety.fresh_scene()
        bpy.context.scene.name = self.id.upper()
        self.m = kit.materials()
        self.set = geo.collection("SET")
        self.props = geo.collection("PROPS")


# ---------------------------------------------------------------- materials only this set needs
def jali(name):
    """The pierced screen in the entrance arch (R24): white lattice over dark holes."""
    n = M.Nodes(name)
    brick = n.add("ShaderNodeTexBrick")
    brick.offset, brick.squash = 0.5, 1.0
    brick.inputs["Scale"].default_value = 6.0
    brick.inputs["Mortar Size"].default_value = 0.05
    brick.inputs["Brick Width"].default_value = 0.42
    brick.inputs["Row Height"].default_value = 0.42
    brick.inputs["Color1"].default_value = M.rgb("#2A221D")
    brick.inputs["Color2"].default_value = M.rgb("#35291F")
    brick.inputs["Mortar"].default_value = M.rgb("env.facade-white")
    n.link(n.planar(), brick.inputs["Vector"])
    n.link(n.mix(n.maprange(n.noise(3.0, 4), 0.5, 0.8, 0.0, 0.4), brick.outputs["Color"], M.rgb("#B9B4AA")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.8)
    n.bump(brick.outputs["Fac"], 0.6, 0.01)
    return n.mat


def masonry_faint(name):
    """Russell Market masonry for this set: the kit's white-with-pink-ghost, but the ghost only in
    small worn patches (art bible §0: "a faint pink ghost"), and soot washing down from the cornice."""
    n = M.Nodes(name)
    ghost = n.maprange(n.noise(3.0, 6, 0.7), 0.66, 0.69, 0.0, 0.55)
    base = n.mix(ghost, n.mix(n.noise(12.0, 3), M.rgb("env.facade-white"), M.rgb("#C9C6BD")), M.rgb("env.facade-pink"))
    sep = n.add("ShaderNodeSeparateXYZ")
    n.link(n.add("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
    streak = n.maprange(sep.outputs["Z"], 3.0, 4.2, 0.0, 0.35)
    m = n.add("ShaderNodeMath", operation="MULTIPLY")
    n.link(streak, m.inputs[0])
    n.link(n.maprange(n.noise(18.0, 3, 0.5), 0.35, 0.75), m.inputs[1])
    base = n.mix(m.outputs[0], base, M.rgb("#8E887E"))
    n.link(M._with_grime(n, base, 0.0, 0.5, 0.45), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.8)
    n.bump(n.noise(30.0, 5), 0.12)
    return n.mat


def poster(name, tint):
    """A faded, illegible poster pasted on a pilaster (R24): colour blocks, no text, no photos."""
    n = M.Nodes(name)
    brick = n.add("ShaderNodeTexBrick")
    brick.offset, brick.squash = 0.0, 1.0
    brick.inputs["Scale"].default_value = 7.0
    brick.inputs["Mortar Size"].default_value = 0.04
    brick.inputs["Brick Width"].default_value = 1.6
    brick.inputs["Row Height"].default_value = 0.35
    brick.inputs["Color1"].default_value = M.rgb(tint)
    brick.inputs["Color2"].default_value = M.rgb("#B7AE9C")
    brick.inputs["Mortar"].default_value = M.rgb("#E3DDCF")
    n.link(n.planar(), brick.inputs["Vector"])
    faded = n.mix(n.maprange(n.noise(4, 4), 0.3, 0.8, 0.25, 0.6), brick.outputs["Color"], M.rgb("#DCD6C8"))
    n.link(faded, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.7)
    return n.mat


def grate(name):
    """Drain grate: steel bars every 5 cm over a dark channel."""
    n = M.Nodes(name)
    n.link(n.mix(n.stripes("X", 0.05), M.rgb("#5E5952"), M.rgb("#1F1A17")), n.bsdf.inputs["Base Color"])
    n.set("Metallic", 0.6)
    n.set("Roughness", 0.4)
    return n.mat


def apron_worn(name):
    """Riyaz's apron: clean (no blood: art bible §4 'meat'), but worn: washed-out, a soft grey
    tide line at the hem and creases."""
    n = M.Nodes(name)
    base = n.mix(n.noise(6.0, 4, 0.6), M.rgb("#D6CFC0"), M.rgb("#C2BAA9"))
    hem = n.height_mask(0.45, 0.62)
    m = n.add("ShaderNodeMath", operation="MULTIPLY")
    n.link(hem, m.inputs[0])
    m.inputs[1].default_value = 0.35
    n.link(n.mix(m.outputs[0], base, M.rgb("#9A9284")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.9)
    n.bump(n.noise(14.0, 3, 0.5), 0.2, 0.01)
    return n.mat


def crate_plastic(name):
    """The crate's moulded plastic in the exact meaning blue (task 14): a subtle fade only, so the
    sunlit top still reads as #1F5BA8 after AgX, not as a pale lavender."""
    n = M.Nodes(name)
    blue = M.rgb("#1A4E92")                                  # one step under #1F5BA8: the sun lifts it back
    n.link(n.mix(n.maprange(n.noise(4.0, 3), 0.3, 0.8, 0.0, 0.12), blue, M.rgb("#3A6CB0")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.55)
    n.bump(n.noise(80.0, 2), 0.03)
    return n.mat


def water(name):
    n = M.Nodes(name)
    n.set("Base Color", M.rgb("#5A5049"))
    n.set("Roughness", 0.16)
    n.set("Coat Weight", 0.3)
    return n.mat


def set_materials(m):
    m.update(
        paving=M.paving("MAT_paving_s03", wet_centre=(-0.7, 1.4), wet_radius=2.4),
        masonry=masonry_faint("MAT_masonry_s03"),
        poster_a=poster("MAT_poster_a", "#7E8A9A"),
        poster_b=poster("MAT_poster_b", "#9A7A6E"),
        jali=jali("MAT_jali"),
        grate=grate("MAT_drain_grate"),
        water=water("MAT_puddle"),
        drop=M.matte("MAT_drop", "#DCE6EA", 0.05),                     # bright beads, readable at 720p
        hub_panel=M.matte("MAT_coldroom_panel", "#D9D7D0", 0.45),         # new, clean, not shiny (§4)
        hub_seam=M.matte("MAT_coldroom_seam", "#A8A49C", 0.6),
        band_a=M.matte("MAT_band_chamber_a", "#2E6B34", 0.55),            # mean.income: Chamber A (§3.2)
        band_b=M.matte("MAT_band_chamber_b", "#1F5BA8", 0.55),            # mean.offsite: Chamber B (§3.2)
        crate=crate_plastic("MAT_crate_offsite"),                         # task 14: meaning blue, subtle fade
        crate_dark=M.matte("MAT_crate_slot", "#1C1714", 0.6),
        seal=M.plastic("MAT_crate_seal", "#E6E2D8", 0.5),
        solar=M.tiles("MAT_solar_cells", "#2A303A", "#2A303A", 0.16, checker=False),
        condenser=M.plastic("MAT_condenser", "#BDBAB2", 0.55),
        pipe=M.matte("MAT_pipe_lagging", "#2A2624", 0.7),
        display=M.matte("MAT_scale_display", "#24292A", 0.2),             # blank: Phaser draws "1.0 kg"
        board=M.matte("MAT_rateboard_flex", "#ECE7DC", 0.6),              # blank: Phaser draws the rates
        phone=M.matte("MAT_phone", "#1F1C1B", 0.25),
        lanyard=M.matte("MAT_lanyard", "#4A4F57", 0.7),
        badge=M.plastic("MAT_badge", "#E6E2D8", 0.5),
    )


# ---------------------------------------------------------------- geometry helpers for the masonry
def pointed_arch(xc, span, z_spring, rise, n=14):
    """Points (x, z) of a pointed arch from the left springing over the apex to the right one.
    Two arcs of radius 0.6 x span (R23/R24 arches are pointed, not round), squashed to `rise`."""
    r = 0.6 * span
    half = span / 2
    theta_apex = math.acos((half - r) / r)
    raw_rise = r * math.sin(theta_apex)
    left = []
    for i in range(n + 1):
        t = math.pi - (math.pi - theta_apex) * i / n
        left.append((xc - half + r + r * math.cos(t), z_spring + r * math.sin(t) * rise / raw_rise))
    right = [(2 * xc - x, z) for x, z in reversed(left[:-1])]
    return left + right


def arch_band(name, xc, span, z_spring, rise, z_foot, band, y, mat, col, proud=0.06):
    """A moulded band tracing a pointed arch and its legs down to z_foot, proud of the wall at y."""
    inner = [(xc - span / 2, z_foot)] + pointed_arch(xc, span, z_spring, rise) + [(xc + span / 2, z_foot)]
    outer = [(xc - span / 2 - band, z_foot)] + pointed_arch(xc, span + 2 * band, z_spring, rise + band) + [(xc + span / 2 + band, z_foot)]
    bm = bmesh.new()
    vi = [bm.verts.new((x, y, z)) for x, z in inner]
    vo = [bm.verts.new((x, y, z)) for x, z in outer]
    for k in range(len(vi) - 1):
        bm.faces.new((vi[k], vo[k], vo[k + 1], vi[k + 1]))
    obj = geo.solid(name, bm, mat, col, proud)
    obj.location.y -= proud / 2
    return obj


def arch_fill(name, xc, span, z_spring, rise, z_base, y, mat, col, thickness=0.04):
    """Flat panel filling a pointed arch down to z_base (the jali over the entrance)."""
    pts = [(xc - span / 2, z_base)] + pointed_arch(xc, span, z_spring, rise) + [(xc + span / 2, z_base)]
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, z)) for x, z in pts])
    return geo.solid(name, bm, mat, col, thickness)


# ---------------------------------------------------------------- the set
def market_wall(st):
    """Russell Market's ground floor (X04/R24, white with the pink ghost of X03/R23): the wall with
    the hub's entrance cut into the central bay, pilasters, a base moulding, the entrance lintel and
    jali arch, a blind arch in the right bay, and the cornice (seen only at the right of the frame)."""
    s, m, col = st.street, st.m, st.set
    w, t, top = s.wall_y, s.wall_t, s.top_z
    geo.box("MARKET_wall_L", (s.x0, w, 0), (OPEN_X[0], w + t, top), m["masonry"], col, geo.BEVEL_ARCH)
    geo.box("MARKET_wall_R", (OPEN_X[1], w, 0), (s.x1, w + t, top), m["masonry"], col, geo.BEVEL_ARCH)
    geo.box("MARKET_wall_over", (OPEN_X[0], w, LINTEL_Z), (OPEN_X[1], w + t, top), m["masonry"], col, 0)
    geo.box("MARKET_base", (s.x0, w - 0.08, 0), (s.x1, w, 0.42), m["masonry"], col, geo.BEVEL_ARCH)
    for i, (x0, x1) in enumerate(((-1.75, -1.32), (1.32, 1.75), (4.55, 4.98))):
        geo.box(f"MARKET_pilaster{i}", (x0, w - 0.14, 0), (x1, w, top), m["masonry"], col, geo.BEVEL_ARCH)
        geo.box(f"MARKET_pilaster{i}_base", (x0 - 0.05, w - 0.2, 0), (x1 + 0.05, w, 0.55), m["masonry"], col, geo.BEVEL_ARCH)
        geo.box(f"MARKET_pilaster{i}_ring", (x0 - 0.03, w - 0.18, 2.5), (x1 + 0.03, w, 2.6), m["masonry"], col, geo.BEVEL_PROP)
    for i, (x0, x1, z0, z1, mat) in enumerate(((1.36, 1.71, 1.25, 1.75, "poster_a"), (4.59, 4.94, 1.1, 1.55, "poster_b"),
                                               (4.62, 4.9, 1.62, 1.95, "poster_a"))):
        geo.box(f"MARKET_poster{i}", (x0, w - 0.146, z0), (x1, w - 0.14, z1), m[mat], col, 0)
    # entrance: lintel, then the pointed jali arch over it (R24)
    geo.box("MARKET_lintel", (OPEN_X[0] - 0.12, w - 0.12, LINTEL_Z), (OPEN_X[1] + 0.12, w, LINTEL_Z + 0.2), m["masonry"], col, geo.BEVEL_ARCH)
    arch_fill("MARKET_jali", 0.0, 2.2, LINTEL_Z + 0.25, 0.95, LINTEL_Z + 0.2, w - 0.03, m["jali"], col)
    arch_band("MARKET_jali_arch", 0.0, 2.2, LINTEL_Z + 0.25, 0.95, LINTEL_Z + 0.2, 0.12, w - 0.04, m["masonry"], col)
    # right bay: blind pointed arch (R23 long side), framing the rate board
    arch_band("MARKET_blind_arch_R", 3.2, 2.3, 2.05, 0.9, 0.42, 0.12, w - 0.04, m["masonry"], col)
    arch_band("MARKET_blind_arch_L", -3.3, 2.3, 2.05, 0.9, 0.42, 0.12, w - 0.04, m["masonry"], col)
    # cornice with brackets (R24), at the top right of the frame
    geo.box("MARKET_cornice", (s.x0, w - 0.32, 4.3), (s.x1, w, 4.45), m["masonry"], col, geo.BEVEL_ARCH)
    for k in range(int((s.x1 - s.x0) / 0.6)):
        x = s.x0 + 0.3 + k * 0.6
        geo.box(f"MARKET_bracket{k}", (x - 0.05, w - 0.26, 4.05), (x + 0.05, w, 4.3), m["masonry"], col, geo.BEVEL_PROP)


def hub_room(st):
    """Behind the entrance: the hub's tiled room, kept dark so the attendant reads against it (§5)."""
    s, m, col = st.street, st.m, st.set
    x0, x1, back = *OPEN_X, s.wall_y + 2.4
    kit.building_mass(s, m, col, rooms=[(x0, x1, back + 0.2, LINTEL_Z + 0.1)])
    geo.box("HUB_floor", (x0, 2.6, 0), (x1, back, HUB_FLOOR), m["floor"], col, 0.01)
    geo.box("HUB_step", (x0, 2.6, 0), (x1, s.wall_y, HUB_FLOOR), m["steel_dark"], col, 0.01)
    geo.box("HUB_wall_back", (x0, back, 0), (x1, back + 0.2, LINTEL_Z + 0.3), m["tiles_in"], col, 0)
    geo.box("HUB_ceiling", (x0, s.wall_y + s.wall_t, LINTEL_Z), (x1, back + 0.2, LINTEL_Z + 0.1), m["ceiling"], col, 0)
    geo.box("HUB_rack", (x0 + 0.2, back - 0.45, HUB_FLOOR), (x0 + 1.2, back - 0.05, 1.7), m["steel"], col)
    practical = [
        geo.cylinder("HUB_tube", (x0 + 0.3, back - 0.1, 2.05), 0.02, 1.4, m["tube"], col, axis="X", bevel=0),
        rig.point_light("LIGHT_hub_tube", (0.0, back - 0.4, 2.0), (0.95, 0.96, 0.91), 40, 0.3, col),
    ]
    for o in practical:
        o["practical"] = True


def counter(st):
    """The hub's front counter (task 14): steel top, checker-tile front (X05/R25), new and clean.
    The scale sits in the gap at its left end, so the crate goes down at the attendant's side."""
    m, col = st.m, st.set
    c = COUNTER
    geo.box("COUNTER_body", (c["x0"], c["y0"], 0.05), (c["x1"], c["y1"], c["top"] - 0.04), m["tiles_checker"], col)
    geo.box("COUNTER_kick", (c["x0"] + 0.03, c["y0"] - 0.005, 0), (c["x1"] - 0.03, c["y1"], 0.08), m["steel_dark"], col, 0.005)
    geo.box("COUNTER_top", (c["x0"] - 0.03, c["y0"] - 0.04, c["top"] - 0.04), (c["x1"] + 0.03, c["y1"] + 0.02, c["top"]), m["steel"], col, 0.008)
    geo.box("COUNTER_back_L", (SCALE["x0"] - 0.08, SCALE["y1"], 0), (c["x0"], c["y1"], 0.95), m["tiles_checker"], col)
    geo.box("COUNTER_back_L_top", (SCALE["x0"] - 0.1, SCALE["y1"] - 0.02, 0.95), (c["x0"], c["y1"] + 0.02, 0.99), m["steel"], col, 0.008)


def scale(st):
    """Platform scale (§0 gap: generic form, no marks): low steel platform, a column, a small
    digital head. The display is blank; Phaser draws 1.0 kg (task 03)."""
    m, col, s = st.m, st.set, SCALE
    geo.box("SCALE_platform", (s["x0"], s["y0"], 0.02), (s["x1"], s["y1"], s["top"]), m["steel"], col, 0.01)
    geo.box("SCALE_base", (s["x0"] + 0.03, s["y0"] + 0.03, 0), (s["x1"] - 0.03, s["y1"] - 0.03, 0.03), m["steel_dark"], col, 0.005)
    for i, (x, y) in enumerate(((s["x0"] + 0.06, s["y0"] + 0.06), (s["x1"] - 0.06, s["y0"] + 0.06))):
        geo.cylinder(f"SCALE_foot{i}", (x, y, 0), 0.025, 0.02, m["cable"], col, bevel=0)
    cx = s["x1"] - 0.06
    geo.cylinder("SCALE_column", (cx, s["y1"] - 0.05, s["top"]), 0.022, 1.08, m["steel"], col, bevel=0)
    head = (cx, s["y1"] - 0.08, s["top"] + 1.12)
    geo.box("SCALE_head", (head[0] - 0.13, head[1] - 0.05, head[2] - 0.08), (head[0] + 0.13, head[1] + 0.05, head[2] + 0.08), m["condenser"], col, 0.015)
    geo.box("SCALE_display", (head[0] - 0.1, head[1] - 0.056, head[2] - 0.04), (head[0] + 0.1, head[1] - 0.05, head[2] + 0.05), m["display"], col, 0.002)
    st.anchor("scale_pan", ((s["x0"] + s["x1"]) / 2, (s["y0"] + s["y1"]) / 2, s["top"]))
    st.anchor("scale_display", (head[0], head[1] - 0.06, head[2] + 0.2))


def rate_board(st):
    """Flex rate board in the right bay, framed like the S1 fascia (F04). Blank in the render:
    Phaser draws params.rate_board and rate_note with a Proposed chip (task 03)."""
    m, col, b, w = st.m, st.set, BOARD, st.street.wall_y
    geo.box("RATEBOARD_frame", (b["x0"] - 0.04, w - 0.08, b["z0"] - 0.04), (b["x1"] + 0.04, w - 0.04, b["z1"] + 0.04), m["steel_dark"], col, 0.006)
    geo.panel("RATEBOARD_panel", ((b["x0"] + b["x1"]) / 2, w - 0.085, (b["z0"] + b["z1"]) / 2), (b["x1"] - b["x0"], b["z1"] - b["z0"]), "-Y", m["board"], col)
    for i, x in enumerate((b["x0"] + 0.1, b["x1"] - 0.1)):
        geo.cylinder(f"RATEBOARD_bolt{i}", (x, w - 0.09, b["z1"] - 0.06), 0.012, 0.01, m["steel"], col, axis="Y", bevel=0)
    st.anchor("rate_board", ((b["x0"] + b["x1"]) / 2, w - 0.09, (b["z0"] + b["z1"]) / 2))


def cold_room(st):
    """The front of the two-chamber cold room (§0 gap: our proposal, generic): insulated panels,
    two separate doors with a band each (Chamber A green, Chamber B blue: §3.2; the words are drawn
    by Phaser), the cooling unit on its side and the edge of the solar panel on its roof."""
    m, col, c, w = st.m, st.set, COLD, st.street.wall_y
    geo.box("COLD_body", (c["x0"], c["y0"], 0), (c["x1"], w, c["top"]), m["hub_panel"], col, 0.02)
    geo.box("COLD_plinth", (c["x0"] - 0.02, c["y0"] - 0.02, 0), (c["x1"] + 0.02, w, 0.12), m["steel_dark"], col, 0.01)
    for k in range(1, 4):                                   # panel seams
        x = c["x0"] + (c["x1"] - c["x0"]) * k / 4
        if any(d0 - 0.1 < x < d1 + 0.1 for d0, d1 in DOORS.values()):
            continue
        geo.box(f"COLD_seam{k}", (x - 0.008, c["y0"] - 0.006, 0.12), (x + 0.008, c["y0"], c["top"] - 0.02), m["hub_seam"], col, 0)
    for key, (x0, x1) in DOORS.items():
        y = c["y0"]
        geo.box(f"DOOR_{key.upper()}_frame", (x0 - 0.05, y - 0.04, 0.1), (x1 + 0.05, y, 2.12), m["steel"], col, 0.008)
        geo.box(f"DOOR_{key.upper()}", (x0, y - 0.07, 0.12), (x1, y - 0.03, 2.08), m["hub_panel"], col, 0.012)
        geo.box(f"DOOR_{key.upper()}_band", (x0, y - 0.075, 1.36), (x1, y - 0.068, 1.5), m[f"band_{key}"], col, 0.003)
        geo.box(f"DOOR_{key.upper()}_kick", (x0 + 0.02, y - 0.075, 0.14), (x1 - 0.02, y - 0.068, 0.36), m["steel"], col, 0.004)
        hx = x1 - 0.12
        geo.box(f"DOOR_{key.upper()}_hinge_box", (hx - 0.03, y - 0.11, 1.0), (hx + 0.03, y - 0.07, 1.16), m["steel_dark"], col, 0.006)
        geo.box(f"DOOR_{key.upper()}_lever", (hx - 0.2, y - 0.14, 1.06), (hx + 0.02, y - 0.11, 1.1), m["steel"], col, 0.008)
        geo.cylinder(f"DOOR_{key.upper()}_window", ((x0 + x1) / 2, y - 0.076, 1.78), 0.11, 0.008, m["window_glass"], col, axis="Y", bevel=0)
        st.anchor(f"door_{key}", ((x0 + x1) / 2, y - 0.08, 1.43))
    # cooling unit on the side that faces the counter, with its pipes into the roof
    x = c["x1"]
    geo.box("COLD_condenser", (x, 2.05, 1.35), (x + 0.32, 2.85, 2.05), m["condenser"], col, 0.02)
    geo.cylinder("COLD_fan_ring", (x + 0.32, 2.45, 1.7), 0.27, 0.012, m["steel_dark"], col, axis="X", bevel=0)
    geo.cylinder("COLD_fan", (x + 0.325, 2.45, 1.7), 0.24, 0.006, m["cable"], col, axis="X", bevel=0)
    for i, r in enumerate((0.08, 0.16)):
        geo.cylinder(f"COLD_fan_guard{i}", (x + 0.333, 2.45, 1.7), r, 0.004, m["steel"], col, axis="X", bevel=0, segments=32)
    geo.limb("COLD_pipe0", (x + 0.1, 2.75, 2.05), (x + 0.1, 2.75, c["top"] + 0.05), 0.03, 0.03, m["pipe"], col)
    geo.limb("COLD_pipe1", (x + 0.2, 2.8, 2.05), (x + 0.2, 2.8, c["top"] + 0.05), 0.02, 0.02, m["steel"], col)
    # solar panel on the roof, tilted to the sky; only its front edge shows under the frame top
    tilt = Matrix.Rotation(math.radians(-18), 4, "X")
    for i, x0 in enumerate((c["x0"] + 0.15, c["x0"] + 1.25)):
        cells = geo.box(f"SOLAR_cells{i}", (-0.52, -0.8, -0.02), (0.52, 0.8, 0.02), m["solar"], col, 0.004)
        frame = geo.box(f"SOLAR_frame{i}", (-0.55, -0.83, -0.035), (0.55, 0.83, -0.015), m["steel"], col, 0.004)
        for o in (cells, frame):
            o.matrix_world = Matrix.Translation((x0 + 0.55, 2.35, c["top"] + 0.35)) @ tilt
        geo.limb(f"SOLAR_leg{i}", (x0 + 0.55, 1.65, c["top"]), (x0 + 0.55, 1.65, c["top"] + 0.12), 0.02, 0.02, m["steel_dark"], col)
    st.anchor("solar", (c["x0"] + 1.2, 1.6, c["top"] + 0.2))


def drain_and_puddles(st):
    """Wet paving: a drain channel along the kerb and puddles where the hub is hosed down (R07, R11)."""
    s, m, col = st.street, st.m, st.set
    geo.box("DRAIN_channel", (s.x0, 0.42, -0.04), (s.x1, 0.66, 0.002), m["cable"], col, 0)
    geo.box("DRAIN_grate", (s.x0 + 0.02, 0.44, 0.0), (s.x1 - 0.02, 0.64, 0.006), m["grate"], col, 0)
    geo.box("DRAIN_lip_front", (s.x0, 0.39, 0.0), (s.x1, 0.43, 0.008), m["kerb"], col, 0.003)
    geo.box("DRAIN_lip_back", (s.x0, 0.65, 0.0), (s.x1, 0.69, 0.008), m["kerb"], col, 0.003)
    for i, (x, y, r, sx) in enumerate(((-0.3, 0.8, 0.22, 2.4), (1.6, 0.85, 0.16, 2.0))):     # by the drain
        p = geo.cylinder(f"PUDDLE_{i}", (x, y, 0.0), r, 0.003, m["water"], col, segments=32, bevel=0)
        p.scale = (sx, 1.0, 1.0)


def crate(st):
    """PROP_crate (task 03/14): ribbed stackable crate after F03's crates, 0.55 x 0.36 x 0.30 m, in
    the meaning blue of Chamber B. Sealed: the lid is on and clipped, with a seal tag."""
    m, col = st.m, st.prop("crate")
    lx, ly, lz = CRATE
    c = CRATE_AT
    x0, x1, y0, y1 = c.x - lx / 2, c.x + lx / 2, c.y - ly / 2, c.y + ly / 2
    body_top = lz - 0.04
    geo.box("CRATE_body", (x0 + 0.01, y0 + 0.01, 0.0), (x1 - 0.01, y1 - 0.01, body_top), m["crate"], col, 0.02)
    geo.box("CRATE_lid", (x0 - 0.008, y0 - 0.008, body_top), (x1 + 0.008, y1 + 0.008, lz), m["crate"], col, 0.015)
    geo.box("CRATE_lid_rib", (x0 + 0.06, c.y - 0.04, lz), (x1 - 0.06, c.y + 0.04, lz + 0.012), m["crate"], col, 0.006)
    for k in range(5):                                      # vertical ribs on the long faces
        x = x0 + 0.08 + k * (lx - 0.16) / 4
        for side, yy in (("f", y0), ("b", y1 - 0.012)):
            geo.box(f"CRATE_rib_{side}{k}", (x - 0.012, yy, 0.03), (x + 0.012, yy + 0.012, body_top - 0.03), m["crate"], col, 0.004)
    geo.box("CRATE_band_low", (x0, y0, 0.03), (x1, y1, 0.06), m["crate"], col, 0.006)
    for i, xx in enumerate((x0 - 0.002, x1 - 0.008)):       # handholds in the short ends
        geo.box(f"CRATE_handhold{i}", (xx, c.y - 0.07, body_top - 0.09), (xx + 0.01, c.y + 0.07, body_top - 0.045), m["crate_dark"], col, 0.01)
    for i, xx in enumerate((c.x - 0.15, c.x + 0.15)):        # lid clips on the front
        geo.box(f"CRATE_clip{i}", (xx - 0.03, y0 - 0.016, body_top - 0.05), (xx + 0.03, y0 - 0.004, lz + 0.004), m["crate"], col, 0.004)
    geo.box("CRATE_seal", (c.x + 0.15 - 0.012, y0 - 0.024, body_top - 0.1), (c.x + 0.15 + 0.012, y0 - 0.018, body_top - 0.05), m["seal"], col, 0.002)
    kit.shadow_catcher("CRATE_shadow_catcher", (c.x + 0.08, c.y + 0.05, 0.004), (0.9, 0.7), m, col)
    st.anchor("crate_centre", (c.x, c.y, lz / 2))
    st.anchor("crate_knot", (c.x, c.y, lz))


def _world(origin, heading, local):
    return Vector(origin) + Matrix.Rotation(math.radians(heading), 3, "Z") @ Vector(local)


def riyaz(st):
    """Riyaz Q. as in s01 (deck p. 22), without the cleaver, apron clean but worn. He has just set
    down the knife and holds his wet hands away from his body (deck p. 23: wet hands make the phone
    uncomfortable), so it is the attendant who types."""
    m = st.m
    mats = people.costume_materials("riyaz", apron="#D6CFC0", cap="#E6E2D8", wet_hands=True)
    mats["apron"] = apron_worn("MAT_riyaz_apron_worn")
    right, left = (-0.52, -0.06, 0.92), (0.52, -0.06, 0.92)       # out to the sides, off the apron
    col = st.char("riyaz", "idle")
    people.figure("RIYAZ_idle", RIYAZ_AT, RIYAZ_HEADING, mats, right, left, col)
    for side, hand in (("R", right), ("L", left)):          # drips from the fingertips
        for k, (dz, r) in enumerate(((0.1, 0.02), (0.26, 0.016), (0.44, 0.013))):
            p = _world(RIYAZ_AT, RIYAZ_HEADING, (hand[0], hand[1], hand[2] - dz))
            geo.sphere(f"RIYAZ_drop_{side}{k}", p, r, (1, 1, 1.5), m["drop"], col, segments=10, rings=6)
        spot = _world(RIYAZ_AT, RIYAZ_HEADING, (hand[0], hand[1], 0.0))
        p = geo.cylinder(f"PUDDLE_drip_{side}", (spot.x, spot.y, 0.0), 0.09, 0.003, m["water"], st.set, segments=24, bevel=0)
        p.scale = (1.3, 1.0, 1.0)
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], 1.75))
    st.anchor("riyaz_hand", tuple(_world(RIYAZ_AT, RIYAZ_HEADING, right)))


def attendant(st):
    """The hub attendant (our proposal, task 14): plain muted shirt that is not a meaning colour,
    a lanyard and badge, a phone. Idle: hands on the counter, phone by the right hand. Type: the
    phone held up in both hands, typing the number Riyaz says (deck p. 26)."""
    m = st.m
    mats = people.costume_materials("attendant", shirt="#7E8784", trousers="#33302E", cap=None)
    top_local = COUNTER["top"] - HUB_FLOOR
    back_y = COUNTER["y1"] - ATTENDANT_AT[1]               # counter's back edge in local y (negative)
    poses = {
        "idle": ((-0.24, back_y - 0.12, top_local + 0.04), (0.24, back_y - 0.1, top_local + 0.04)),
        "type": ((-0.07, -0.34, 1.22), (0.07, -0.34, 1.22)),
    }
    for pose, (right, left) in poses.items():
        col = st.char("attendant", pose)
        root = people.figure(f"ATT_{pose}", ATTENDANT_AT, 0, mats, right, left, col, moustache=False)
        parts = [
            geo.limb(f"ATT_{pose}_lanyard_L", (-0.07, -0.152, 1.34), (0.0, -0.162, 1.1), 0.007, 0.007, m["lanyard"], col),
            geo.limb(f"ATT_{pose}_lanyard_R", (0.07, -0.152, 1.34), (0.0, -0.162, 1.1), 0.007, 0.007, m["lanyard"], col),
            geo.box(f"ATT_{pose}_badge", (-0.045, -0.172, 0.98), (0.045, -0.158, 1.1), m["badge"], col, 0.004),
        ]
        if pose == "type":
            phone = geo.box(f"ATT_{pose}_phone", (-0.04, -0.008, -0.075), (0.04, 0.008, 0.075), m["phone"], col, 0.006)
            phone.matrix_world = Matrix.Translation((0.0, -0.36, 1.27)) @ Matrix.Rotation(math.radians(-55), 4, "X")
            parts.append(phone)
        else:
            parts.append(geo.box(f"ATT_{pose}_phone", (-0.36, back_y - 0.2, top_local), (-0.28, back_y - 0.05, top_local + 0.012), m["phone"], col, 0.003))
        for p in parts:                                     # built in local space, like the figure
            p.parent = root
    st.anchor("attendant_head", (ATTENDANT_AT[0], ATTENDANT_AT[1], HUB_FLOOR + 1.75))
    st.anchor("attendant_phone", tuple(Vector(ATTENDANT_AT) + Vector((0.0, -0.36, 1.27))))


def dress(st):
    """The Shivajinagar kit round the hub's front (V01-V05): an auto at the kerb, two-wheelers
    nose-in, a passer-by, a lamp pole, a flex board on the pilaster; a hand truck and a jerrycan
    (CC0 models, art/external/polyhaven) by the counter."""
    s, m, col = st.street, st.m, st.props
    kit.kit_materials(m)
    m.setdefault("pole", M.plaster("MAT_pole", "#9C978E", 0.2))
    kit.autorickshaw("AUTO_0", (3.4, 0.5, 0), 0, m, col)
    kit.two_wheeler_row("BIKE", 4.6, 5.9, 2.25, m, col)
    kit.pedestrian("PED_0", (2.4, 1.35, 0), 100, col, kind=0, stride=0.14)
    kit.pedestrian("PED_1", (5.4, 1.1, 0), -80, col, kind=2, stride=-0.14)
    kit.lamp_pole("POLE", 5.7, 0.3, m, col, height=7.0, transformer=True)
    kit.flex_board("FLEX_0", 1.55, 3.3, 1.0, s, m, m["flex_yellow"], col)
    kit.ph("HAND_truck", "hand_truck", (1.85, 2.55, 0), -30, 1.0, col)
    kit.ph("JERRYCAN", "plastic_jerrycan", (-1.25, 2.55, 0), 20, 1.0, col)


def build():
    st = ArtStation(SET_DATA)
    set_materials(st.m)
    kit.plinth(st.street, st.m, st.set)
    market_wall(st)
    hub_room(st)
    counter(st)
    scale(st)
    rate_board(st)
    cold_room(st)
    drain_and_puddles(st)
    crate(st)
    riyaz(st)
    attendant(st)
    dress(st)
    st.anchor("exit", (4.0, 1.2, 0.0))
    st.finish(TARGET)


if __name__ == "__main__":
    build()
