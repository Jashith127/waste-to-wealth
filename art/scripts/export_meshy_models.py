"""Export each cleaned Meshy character root in the currently opened Blender scene as a GLB."""
from pathlib import Path

import bpy


OUT = Path(r"C:\Users\Jash\Desktop\Waste to wealth\art\build\models\meshy_clean")
OUT.mkdir(parents=True, exist_ok=True)


def descendants(root):
    found = [root]
    for obj in bpy.context.scene.objects:
        parent = obj.parent
        while parent:
            if parent == root:
                found.append(obj)
                break
            parent = parent.parent
    return found


for root in sorted((o for o in bpy.context.scene.objects if o.name.endswith("_root")), key=lambda o: o.name):
    bpy.ops.object.select_all(action="DESELECT")
    selected = descendants(root)
    for obj in selected:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    destination = OUT / f"{root.name.removesuffix('_root').lower()}_clean.glb"
    bpy.ops.export_scene.gltf(filepath=str(destination), export_format="GLB", use_selection=True)
    print(f"[export] {destination}")
