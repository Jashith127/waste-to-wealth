"""Extract packed Meshy base-colour maps from the cleaned Blender scene for texture repair."""
from pathlib import Path
import bpy

out = Path(r"C:\Users\Jash\Desktop\Waste to wealth\art\build\textures\meshy")
out.mkdir(parents=True, exist_ok=True)
for image in bpy.data.images:
    if "basecolor" not in image.name.lower():
        continue
    image.filepath_raw = str(out / image.name)
    image.file_format = "PNG"
    image.save()
    print(f"[texture] {image.filepath_raw}")
