"""Material library (art-bible §4). Procedural only: no photo textures, so no real
signage leaks in. Colours are the art-bible tokens; check them on the rendered PNG."""
import bpy

TOKENS = {
    "env.plaster": "#D9774F", "env.cream": "#DCC498", "env.facade-white": "#D4D3CC",
    "env.facade-pink": "#E2AF95", "env.shutter": "#5F7383", "env.tile-blue": "#658C9E",
    "env.paving": "#A39383", "env.floor-wet": "#48413E", "env.steel": "#8A7E72",
    "env.awning-red": "#94464C", "env.awning-dark": "#4A4246", "env.plastic-navy": "#454F5D",
    "env.door-green": "#70674C", "env.meat": "#9B5C42", "env.meat-light": "#B9886F",
    "env.interior": "#3F2A1A", "env.charcoal": "#1C1714",
    "cement": "#8E8A82", "grime": "#4A4036", "soil": "#5A463A", "bedding": "#8E7A62",
    "tile-white": "#D8D2C8", "wood": "#6B4A35", "skin": "#8D5B3E", "enamel": "#C9C6BC",
}


def rgb(hex_or_token):
    """sRGB hex (or token name) -> linear RGBA for Blender sockets."""
    h = TOKENS.get(hex_or_token, hex_or_token).lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, 1.0)


class Nodes:
    """Tiny helper around a material node tree."""

    def __init__(self, name):
        self.mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.tree = self.mat.node_tree
        self.tree.nodes.clear()
        self.out = self.add("ShaderNodeOutputMaterial")
        self.bsdf = self.add("ShaderNodeBsdfPrincipled")
        self.link(self.bsdf.outputs[0], self.out.inputs["Surface"])

    def add(self, kind, **props):
        n = self.tree.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.tree.links.new(a, b)

    def set(self, socket, value):
        self.bsdf.inputs[socket].default_value = value

    def coords(self, kind="Object"):
        return self.add("ShaderNodeTexCoord").outputs[kind]

    def noise(self, scale, detail=4.0, rough=0.6, coord="Object"):
        n = self.add("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        self.link(self.coords(coord), n.inputs["Vector"])
        return n.outputs["Fac"]

    def ramp(self, fac, stops):
        """stops: [(pos, hex), ...] -> colour output."""
        r = self.add("ShaderNodeValToRGB")
        el = r.color_ramp.elements
        while len(el) > len(stops):
            el.remove(el[-1])
        while len(el) < len(stops):
            el.new(0.5)
        for e, (pos, col) in zip(el, stops):
            e.position, e.color = pos, rgb(col)
        self.link(fac, r.inputs["Fac"])
        return r.outputs["Color"]

    def mix(self, fac, a, b):
        m = self.add("ShaderNodeMix", data_type="RGBA")
        for sock, v in ((m.inputs[0], fac), (m.inputs[6], a), (m.inputs[7], b)):
            if isinstance(v, (tuple, float, int)):
                sock.default_value = v
            else:
                self.link(v, sock)
        return m.outputs[2]

    def maprange(self, value, a, b, lo=0.0, hi=1.0):
        m = self.add("ShaderNodeMapRange")
        self.link(value, m.inputs["Value"])
        m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = a, b
        m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = lo, hi
        return m.outputs["Result"]

    def height_mask(self, z0, z1):
        """1 at z<=z0 fading to 0 at z>=z1 (world Z). For grime at the base of walls."""
        sep = self.add("ShaderNodeSeparateXYZ")
        self.link(self.add("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
        return self.maprange(sep.outputs["Z"], z0, z1, 1.0, 0.0)

    def stripes(self, axis, period):
        """0/1 bands along world `axis`, `period` metres per light+dark pair."""
        sep = self.add("ShaderNodeSeparateXYZ")
        self.link(self.add("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
        div = self.add("ShaderNodeMath", operation="DIVIDE")
        self.link(sep.outputs[axis], div.inputs[0])
        div.inputs[1].default_value = period
        frac = self.add("ShaderNodeMath", operation="FRACT")
        self.link(div.outputs[0], frac.inputs[0])
        gt = self.add("ShaderNodeMath", operation="GREATER_THAN")
        self.link(frac.outputs[0], gt.inputs[0])
        gt.inputs[1].default_value = 0.5
        return gt.outputs[0]

    def planar(self):
        """World position flattened onto the face's dominant plane, so 2D textures (brick,
        checker) lie flat on walls as well as floors."""
        pos = self.add("ShaderNodeNewGeometry")
        sp = self.add("ShaderNodeSeparateXYZ")
        sn = self.add("ShaderNodeSeparateXYZ")
        self.link(pos.outputs["Position"], sp.inputs[0])
        self.link(pos.outputs["Normal"], sn.inputs[0])

        def combine(a, b):
            c = self.add("ShaderNodeCombineXYZ")
            self.link(sp.outputs[a], c.inputs[0])
            self.link(sp.outputs[b], c.inputs[1])
            return c.outputs[0]

        def facing(axis):
            ab = self.add("ShaderNodeMath", operation="ABSOLUTE")
            self.link(sn.outputs[axis], ab.inputs[0])
            gt = self.add("ShaderNodeMath", operation="GREATER_THAN")
            self.link(ab.outputs[0], gt.inputs[0])
            gt.inputs[1].default_value = 0.5
            return gt.outputs[0]

        def vmix(fac, a, b):
            mx = self.add("ShaderNodeMix", data_type="VECTOR")
            self.link(fac, mx.inputs[0])
            self.link(a, mx.inputs[4])
            self.link(b, mx.inputs[5])
            return mx.outputs[1]

        xy_or_xz = vmix(facing("Y"), combine("X", "Y"), combine("X", "Z"))
        return vmix(facing("X"), xy_or_xz, combine("Y", "Z"))

    def bump(self, height, strength=0.2, distance=0.01):
        b = self.add("ShaderNodeBump")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = distance
        self.link(height, b.inputs["Height"])
        self.link(b.outputs["Normal"], self.bsdf.inputs["Normal"])


def _with_grime(n, base, z0=0.0, z1=0.45, amount=0.55):
    mask = n.height_mask(z0, z1)
    m = n.add("ShaderNodeMath", operation="MULTIPLY")
    n.link(mask, m.inputs[0])
    m.inputs[1].default_value = amount
    return n.mix(m.outputs[0], base, rgb("grime"))


def plaster(name, colour="env.cream", flake=0.35, floor_z=0.0):
    """Lime-washed plaster: flaked to cement at patches, grime at the base."""
    n = Nodes(name)
    flake_mask = n.maprange(n.noise(1.6, 6, 0.7), 0.5 + (1 - flake) * 0.2, 0.5 + (1 - flake) * 0.2 + 0.04)
    wash = n.mix(n.noise(9.0, 3), rgb(colour), n.mix(0.25, rgb(colour), rgb("grime")))
    base = n.mix(flake_mask, wash, rgb("cement"))
    n.link(_with_grime(n, base, floor_z, floor_z + 0.45), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.85)
    n.bump(n.noise(40.0, 6), 0.15)
    return n.mat


def masonry(name):
    """Russell Market masonry: white with the pink ghost in worn patches (art-bible §0)."""
    n = Nodes(name)
    ghost = n.maprange(n.noise(2.2, 5, 0.65), 0.55, 0.6)
    base = n.mix(ghost, rgb("env.facade-white"), rgb("env.facade-pink"))
    n.link(_with_grime(n, base), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.8)
    n.bump(n.noise(30.0, 5), 0.12)
    return n.mat


def shutter(name, colour="env.shutter"):
    """Rolling shutter: horizontal ribs every 8 cm, rust streaks from the bottom."""
    n = Nodes(name)
    sep = n.add("ShaderNodeSeparateXYZ")
    n.link(n.add("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
    wave = n.add("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
    wave.inputs["Scale"].default_value = 1.0
    n.link(n.coords("Object"), wave.inputs["Vector"])
    # scale so bands are 8 cm: wave scale 1 on object coords = 1 band per ~6.28 m, so use a mapping
    mapping = n.add("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1, 1, 78.5)
    n.link(n.coords("Object"), mapping.inputs["Vector"])
    n.link(mapping.outputs[0], wave.inputs["Vector"])
    rust = n.maprange(n.noise(6.0, 4), 0.55, 0.65)
    streak = n.height_mask(0.0, 0.9)
    m = n.add("ShaderNodeMath", operation="MULTIPLY")
    n.link(rust, m.inputs[0]); n.link(streak, m.inputs[1])
    base = n.mix(m.outputs[0], rgb(colour), rgb("#6B4A35"))
    n.link(base, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.55)
    n.set("Metallic", 0.4)
    n.bump(wave.outputs["Fac"], 0.7, 0.02)
    return n.mat


def steel(name, colour="env.steel", rough=0.35):
    n = Nodes(name)
    base = n.mix(n.noise(14.0, 5), rgb(colour), n.mix(0.35, rgb(colour), rgb("env.charcoal")))
    n.link(base, n.bsdf.inputs["Base Color"])
    n.set("Metallic", 0.85)
    n.set("Roughness", rough)
    n.bump(n.noise(60.0, 3), 0.05)
    return n.mat


def tiles(name, a="tile-white", b="env.tile-blue", size=0.15, checker=True):
    """Glazed tiles with grout; checker of a/b or plain a."""
    n = Nodes(name)
    brick = n.add("ShaderNodeTexBrick")
    brick.offset, brick.squash = 0.0, 1.0
    brick.inputs["Scale"].default_value = 1.0 / size
    brick.inputs["Mortar Size"].default_value = 0.006 / size
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.inputs["Color1"].default_value = rgb(a)
    brick.inputs["Color2"].default_value = rgb(a)
    brick.inputs["Mortar"].default_value = rgb("cement")
    vec = n.planar()
    n.link(vec, brick.inputs["Vector"])
    colour = brick.outputs["Color"]
    if checker:
        chk = n.add("ShaderNodeTexChecker")
        chk.inputs["Scale"].default_value = 1.0 / size
        chk.inputs["Color1"].default_value = rgb(a)
        chk.inputs["Color2"].default_value = rgb(b)
        n.link(vec, chk.inputs["Vector"])
        colour = n.mix(brick.outputs["Fac"], chk.outputs["Color"], rgb("cement"))
    n.link(_with_grime(n, colour, 0.0, 0.35, 0.35), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.3)
    n.bump(brick.outputs["Fac"], 0.3, 0.004)
    return n.mat


def paving(name, wet_centre=(0.0, 2.3), wet_radius=1.6):
    """40 cm slabs; a wet patch (dark, glossy) in front of the meat stall (Five senses: Touch)."""
    n = Nodes(name)
    brick = n.add("ShaderNodeTexBrick")
    brick.offset, brick.squash = 0.5, 1.0
    brick.inputs["Scale"].default_value = 2.5
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.inputs["Color1"].default_value = rgb("#8F877C")
    brick.inputs["Color2"].default_value = rgb("#77706A")
    brick.inputs["Mortar"].default_value = rgb("#625A52")
    brick.inputs["Bias"].default_value = 0.0
    brick.inputs["Mortar Smooth"].default_value = 0.4
    n.link(n.add("ShaderNodeNewGeometry").outputs["Position"], brick.inputs["Vector"])
    # wet mask: distance from wet_centre, broken up by noise
    pos = n.add("ShaderNodeNewGeometry").outputs["Position"]
    d = n.add("ShaderNodeVectorMath", operation="DISTANCE")
    n.link(pos, d.inputs[0])
    d.inputs[1].default_value = (wet_centre[0], wet_centre[1], 0)
    noisy = n.add("ShaderNodeMath", operation="ADD")
    n.link(d.outputs["Value"], noisy.inputs[0])
    nz = n.add("ShaderNodeMath", operation="MULTIPLY")
    n.link(n.noise(1.4, 3, 0.5, "Object"), nz.inputs[0]); nz.inputs[1].default_value = 1.2
    n.link(nz.outputs[0], noisy.inputs[1])
    wet = n.maprange(noisy.outputs[0], wet_radius + 0.6, wet_radius, 0.0, 1.0)
    grime = n.maprange(n.noise(1.2, 6, 0.7), 0.3, 0.7, 0.0, 0.8)
    dirty = n.mix(grime, brick.outputs["Color"], rgb("#5E5249"))
    dirty = n.mix(n.maprange(n.noise(14.0, 4), 0.58, 0.72, 0.0, 0.55), dirty, rgb("#3E3631"))   # stains
    dirty = n.mix(n.maprange(n.noise(0.5, 2), 0.45, 0.6, 0.0, 0.35), dirty, rgb("#A39A8C"))     # sun-bleached
    colour = n.mix(wet, dirty, rgb("#4E453F"))
    n.link(colour, n.bsdf.inputs["Base Color"])
    rough = n.add("ShaderNodeMix", data_type="FLOAT")
    n.link(wet, rough.inputs[0])
    rough.inputs[2].default_value, rough.inputs[3].default_value = 0.8, 0.22
    n.link(rough.outputs[0], n.bsdf.inputs["Roughness"])
    n.bump(brick.outputs["Fac"], 0.4, 0.01)
    return n.mat


def menu_board(name, cell=0.26):
    """Painted photo-menu board (F04 layout): cream ground, a grid of muted food-photo tiles.
    No text and no real photos: the tiles are colour blocks."""
    n = Nodes(name)
    brick = n.add("ShaderNodeTexBrick")
    brick.offset, brick.squash = 0.0, 1.0
    brick.inputs["Scale"].default_value = 1.0 / cell
    brick.inputs["Mortar Size"].default_value = 0.035
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 0.8
    brick.inputs["Bias"].default_value = 0.0
    brick.inputs["Color1"].default_value = rgb("#9B5C42")
    brick.inputs["Color2"].default_value = rgb("#B9886F")
    brick.inputs["Mortar"].default_value = rgb("#E1D9C6")
    n.link(n.planar(), brick.inputs["Vector"])
    tint = n.ramp(n.noise(9.0, 2, 0.5), [(0.3, "#7E8A5A"), (0.5, "#9B5C42"), (0.7, "#C9A26B")])
    tiles_col = n.mix(0.5, brick.outputs["Color"], tint)
    colour = n.mix(brick.outputs["Fac"], tiles_col, rgb("#E1D9C6"))
    n.link(n.mix(n.maprange(n.noise(5, 4), 0.4, 0.8, 0.0, 0.3), colour, rgb("#B8AE9C")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.55)
    return n.mat


def floor_wet(name):
    n = Nodes(name)
    base = n.mix(n.noise(5.0, 8, 0.7), rgb("env.floor-wet"), rgb("#2E2926"))
    n.link(base, n.bsdf.inputs["Base Color"])
    n.link(n.maprange(n.noise(2.0, 2), 0.4, 0.6, 0.15, 0.45), n.bsdf.inputs["Roughness"])
    return n.mat


def plastic(name, colour, rough=0.45):
    n = Nodes(name)
    faded = n.mix(n.noise(4.0, 3), rgb(colour), n.mix(0.3, rgb(colour), rgb("#FFFFFF")))
    n.link(faded, n.bsdf.inputs["Base Color"])
    n.set("Roughness", rough)
    n.bump(n.noise(80.0, 2), 0.03)
    return n.mat


def fabric_stripes(name, a="env.awning-red", b="env.awning-dark", width=0.12):
    """Awning fabric: stripes running down the slope, sun-faded."""
    n = Nodes(name)
    step = n.stripes("X", 2 * width)
    colour = n.mix(step, rgb(a), rgb(b))
    colour = n.mix(n.maprange(n.noise(3.0, 4), 0.45, 0.85, 0.0, 0.18), colour, rgb("#C9B5A6"))
    n.link(colour, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.9)
    n.bump(n.noise(120.0, 3), 0.08)
    return n.mat


def checker_cloth(name, a="#3E5A7A", b="#C9C2B2", size=0.035):
    """Checked shirt (F04 butcher)."""
    n = Nodes(name)
    chk = n.add("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 1.0 / size
    chk.inputs["Color1"].default_value = rgb(a)
    chk.inputs["Color2"].default_value = rgb(b)
    n.link(n.coords("Object"), chk.inputs["Vector"])
    n.link(chk.outputs["Color"], n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.85)
    return n.mat


def matte(name, colour, rough=0.7, metallic=0.0):
    n = Nodes(name)
    n.link(n.mix(n.noise(10.0, 3), rgb(colour), n.mix(0.2, rgb(colour), rgb("grime"))), n.bsdf.inputs["Base Color"])
    n.set("Roughness", rough)
    n.set("Metallic", metallic)
    return n.mat


def wood_block(name):
    n = Nodes(name)
    rings = n.add("ShaderNodeTexWave", wave_type="RINGS")
    rings.inputs["Scale"].default_value = 18.0
    rings.inputs["Distortion"].default_value = 4.0
    n.link(n.coords("Object"), rings.inputs["Vector"])
    colour = n.ramp(rings.outputs["Fac"], [(0.0, "#5A3C2A"), (0.6, "wood"), (1.0, "#8A6447")])
    colour = n.mix(n.maprange(n.noise(25, 4), 0.55, 0.7), colour, rgb("#3A2418"))  # nicks and stains
    n.link(colour, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.7)
    n.bump(rings.outputs["Fac"], 0.1)
    return n.mat


def meat(name):
    """Matte, dark, readable as meat from a distance; no gore (art-bible §4)."""
    n = Nodes(name)
    colour = n.ramp(n.noise(7.0, 6, 0.65), [(0.3, "#5E2C24"), (0.55, "#874538"), (0.78, "#B98E7A")])
    n.link(colour, n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.6)
    n.set("Subsurface Weight", 0.05)
    n.bump(n.noise(30, 5), 0.2)
    return n.mat


def carcass(name, lean, deep, fat, fat_amount=0.5):
    """Skinned carcass (F04, X05): lean with darker creases, streaky fat running down the body,
    faint rib banding, moist. Readable at 175 px/m without gore."""
    n = Nodes(name)
    mapping = n.add("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (7, 7, 1.6)          # streaks run with gravity
    n.link(n.coords("Object"), mapping.inputs["Vector"])
    streak = n.add("ShaderNodeTexNoise")
    streak.inputs["Scale"].default_value = 1.0
    streak.inputs["Detail"].default_value = 5.0
    streak.inputs["Roughness"].default_value = 0.6
    n.link(mapping.outputs[0], streak.inputs["Vector"])
    lo = 0.62 - 0.12 * fat_amount
    fat_mask = n.maprange(streak.outputs["Fac"], lo, lo + 0.05)
    base = n.mix(n.maprange(n.noise(9.0, 4, 0.6), 0.35, 0.7), rgb(deep), rgb(lean))
    ribs = n.mix(n.stripes("Z", 0.045), (0, 0, 0, 1), (1, 1, 1, 1))
    m = n.add("ShaderNodeMath", operation="MULTIPLY")
    n.link(ribs, m.inputs[0])
    m.inputs[1].default_value = 0.18
    base = n.mix(m.outputs[0], base, rgb(deep))
    n.link(n.mix(fat_mask, base, rgb(fat)), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.38)
    n.set("Subsurface Weight", 0.12)
    n.set("Coat Weight", 0.25)
    n.bump(streak.outputs["Fac"], 0.25, 0.01)
    return n.mat


def skin(name, colour="skin", wet=False):
    n = Nodes(name)
    n.link(n.mix(n.noise(20, 3), rgb(colour), n.mix(0.25, rgb(colour), rgb("#5A3424"))), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.22 if wet else 0.55)
    n.set("Subsurface Weight", 0.15)
    n.set("Coat Weight", 0.5 if wet else 0.0)   # wet hands (empathy map, deck p. 23)
    return n.mat


def bag_plastic(name):
    """Translucent white carry bag; a faint shadow of the bone and offal inside."""
    n = Nodes(name)
    contents = n.maprange(n.noise(3.5, 4, 0.6), 0.45, 0.75, 0.0, 0.28)
    n.link(n.mix(contents, rgb("#EDEBE4"), rgb("#9B6A5A")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.32)
    n.set("Subsurface Weight", 0.35)
    n.set("Transmission Weight", 0.15)
    n.set("Coat Weight", 0.3)
    n.bump(n.noise(18, 6, 0.7), 0.35, 0.006)
    return n.mat


def emissive(name, colour, strength):
    n = Nodes(name)
    n.set("Base Color", rgb(colour))
    n.set("Emission Color", rgb(colour))
    n.set("Emission Strength", strength)
    return n.mat


def glass(name, tint="#9FB4B8"):
    n = Nodes(name)
    n.set("Base Color", rgb(tint))
    n.set("Roughness", 0.08)
    n.set("Transmission Weight", 0.85)
    n.set("IOR", 1.45)
    return n.mat


def image(name, path, rough=0.6, box_uv=False, flex=False):
    """Image texture on UVs (signboards rendered from src/data by tools/render_signs.mjs)."""
    n = Nodes(name)
    tex = n.add("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path), check_existing=True)
    tex.interpolation = "Cubic"
    if box_uv:   # front face of a box: map the image to the face's own bounds
        tc = n.add("ShaderNodeTexCoord")
        sep = n.add("ShaderNodeSeparateXYZ")
        n.link(tc.outputs["Generated"], sep.inputs[0])
        comb = n.add("ShaderNodeCombineXYZ")
        n.link(sep.outputs["X"], comb.inputs[0])
        n.link(sep.outputs["Z"], comb.inputs[1])
        n.link(comb.outputs[0], tex.inputs["Vector"])
    else:
        n.link(n.add("ShaderNodeUVMap").outputs["UV"], tex.inputs["Vector"])
    faded = n.mix(n.maprange(n.noise(4, 4), 0.4, 0.8, 0.0, 0.2), tex.outputs["Color"], rgb("#D9C9B8"))
    n.link(faded, n.bsdf.inputs["Base Color"])
    n.set("Roughness", rough)
    if flex:   # printed flex banner: soft creases where it is stretched over the frame
        n.bump(n.noise(4.0, 3, 0.5), 0.12, 0.01)
    return n.mat
