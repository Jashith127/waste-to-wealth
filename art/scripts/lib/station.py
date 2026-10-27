"""Station scaffolding shared by every art/scripts/sNN_build.py.

    st = station.begin("s01")        # fresh scene, JSON loaded, kit materials ready
    kit.plinth(st.street, st.m, st.set)
    ...
    st.anchor("kilo_centre", (x, y, z))
    st.finish(target=(0, 3, 1.0))      # camera, lights from the JSON, render settings, save

Collection names are the contract with art/scripts/render_station.py (docs/patterns.md):
  SET, PROPS               static set, rendered into bg.png
  FG                       static set in front of where sprites move (also in bg.png): fg.png,
                           which the game draws over moving sprites, so they pass behind it
  PROP_<name>              something the player moves: <name>.png, plus <name>_shadow.png
                           if it holds an object tagged ["shadow_catcher"]. A collection with
                           ["free"] (st.prop(name, free=True)) moves around the set: it renders
                           with no set holdouts, and fg.png does the occluding instead
  FX_<name>                light that toggles: bg_fx_<name>.png -> fx_<name>.png overlay
  CHAR_<name>_<pose>       one character pose: <name>_<pose>.png. The "idle" pose casts its
                           shadow into bg.png. ["free"] as for PROP_
"""
import json

import bpy

import geo
import kit
import rig
import safety


class Station:
    def __init__(self, sid):
        self.id = sid
        self.data = json.loads((safety.REPO / "src" / "data" / "stations" / f"{sid}.json").read_text(encoding="utf-8"))
        self.blend = safety.REPO / self.data["set"]["blend"]
        self.street = kit.Street(**self.data["set"].get("street", {}))
        self.anchors = {}
        self.target = None
        safety.fresh_scene()
        bpy.context.scene.name = sid.upper()
        self.m = kit.materials()
        self.set = geo.collection("SET")
        self.props = geo.collection("PROPS")
        self.fg = geo.collection("FG")

    def prop(self, name, free=False):
        col = geo.collection(f"PROP_{name}")
        col["free"] = free
        return col

    def fx(self, name):
        return geo.collection(f"FX_{name}")

    def char(self, name, pose, free=False):
        root = geo.collection(f"CHARS")
        col = geo.collection(f"CHAR_{name}_{pose}", root)
        col["free"] = free
        return col

    def anchor(self, name, world_point):
        """Remember a world point; finish() converts it to a 1920x1080 screen point for the game."""
        self.anchors[name] = tuple(world_point)

    def finish(self, target):
        self.target = target
        rig.camera(target)
        rig.lights(self.data["set"]["lighting"])
        rig.render_settings()
        scene = bpy.context.scene
        scene["station"] = self.id
        scene["anchors"] = json.dumps({k: rig.to_screen(v, target) for k, v in self.anchors.items()})
        safety.save(self.blend)


def begin(sid):
    return Station(sid)
