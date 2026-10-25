"""The one camera and the light rig (art-bible §1 and §5). Never vary these per station."""
import math

import bpy
from mathutils import Euler, Vector

CAMERA_ROTATION = (math.radians(60), 0.0, math.radians(45))   # true 2:1 dimetric
ORTHO_SCALE = 11.0                                            # metres across frame width
CAMERA_DISTANCE = 30.0
RES_MASTER = (3840, 2160)
RES_DRAFT = (1920, 1080)
LOOK = "AgX - Medium High Contrast"      # art-bible §5: base contrast read washed out in the S1 slice


def _rot():
    return Euler(CAMERA_ROTATION, "XYZ")


def view_dir():
    """Unit vector the camera looks along (its -Z axis)."""
    return (_rot().to_matrix() @ Vector((0, 0, -1))).normalized()


def camera(target, name="CAM_iso"):
    """Orthographic iso camera centred on `target` (the station's focal point)."""
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ORTHO_SCALE
    cam_data.clip_start, cam_data.clip_end = 0.1, 100.0
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.rotation_euler = CAMERA_ROTATION
    cam.location = Vector(target) - view_dir() * CAMERA_DISTANCE
    bpy.context.scene.camera = cam
    return cam


def to_screen(point, target):
    """World point -> (px, py) on the 1920x1080 frame, origin top-left. For layout checks."""
    r = _rot().to_matrix()
    right, up = r @ Vector((1, 0, 0)), r @ Vector((0, 1, 0))
    d = Vector(point) - Vector(target)
    ppm = 1920 / ORTHO_SCALE
    return 960 + d.dot(right) * ppm, 540 - d.dot(up) * ppm


PRESETS = {
    # sun travel direction (where the light goes), colour, strength, angle (deg), sky colour, sky strength
    # Light comes from screen top-left and in front of the walls, so shop fronts (facing -Y) take raking sun.
    "morning": dict(sun_dir=(0.70, 0.60, -0.80), sun_col=(1.0, 0.886, 0.722), sun_str=5.5, angle=3.0,
                    sky_col=(0.62, 0.71, 0.78), sky_str=0.6, exposure=0.0),
    "midday":  dict(sun_dir=(0.70, 0.30, -1.30), sun_col=(1.0, 0.945, 0.863), sun_str=5.0, angle=2.0,
                    sky_col=(0.72, 0.78, 0.82), sky_str=0.8, exposure=-0.3),
    "dusk":    dict(sun_dir=(0.80, 0.45, -0.28), sun_col=(1.0, 0.62, 0.40), sun_str=3.2, angle=4.0,
                    sky_col=(0.42, 0.36, 0.44), sky_str=0.45, exposure=0.2),        # s04 roof time-lapse
    "night":   dict(sun_dir=None, sky_col=(0.165, 0.208, 0.314), sky_str=0.15, exposure=0.5),
}


def lights(preset="morning"):
    p = PRESETS[preset]
    scene = bpy.context.scene
    world = bpy.data.worlds.new(f"WORLD_{preset}")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*p["sky_col"], 1)
    bg.inputs["Strength"].default_value = p["sky_str"]
    scene.world = world
    scene.view_settings.exposure = p["exposure"]
    if p.get("sun_dir"):
        sun_data = bpy.data.lights.new("SUN_key", "SUN")
        sun_data.energy = p["sun_str"]
        sun_data.color = p["sun_col"]
        sun_data.angle = math.radians(p["angle"])
        sun = bpy.data.objects.new("SUN_key", sun_data)
        scene.collection.objects.link(sun)
        sun.rotation_euler = Vector(p["sun_dir"]).normalized().to_track_quat("-Z", "Y").to_euler()
        return sun
    return None


def point_light(name, loc, colour, watts, radius=0.05, collection=None):
    data = bpy.data.lights.new(name, "POINT")
    data.energy, data.color, data.shadow_soft_size = watts, colour, radius
    obj = bpy.data.objects.new(name, data)
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.location = loc
    return obj


def render_settings(res=RES_DRAFT, samples=128, transparent=True):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev_type in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dev_type
            prefs.refresh_devices()
            if any(d.type == dev_type for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == dev_type
                scene.cycles.device = "GPU"
                break
        except TypeError:
            continue
    print(f"[render] device={scene.cycles.device} backend={prefs.compute_device_type}")
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = LOOK
    scene.unit_settings.system = "METRIC"
