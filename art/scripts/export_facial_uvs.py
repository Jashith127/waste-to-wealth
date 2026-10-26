"""Export front-face UV polygons for targeted texture repainting."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

result = {}
for obj in (o for o in bpy.context.scene.objects if o.type == "MESH"):
    verts = obj.data.vertices
    xs, ys, zs = ([v.co[i] for v in verts] for i in range(3))
    min_x, max_x, min_y, max_y, min_z, max_z = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    width, depth, height = max_x - min_x, max_y - min_y, max_z - min_z
    uv = obj.data.uv_layers.active.data
    polys = []
    for poly in obj.data.polygons:
        centre = sum((verts[i].co for i in poly.vertices), Vector()) / len(poly.vertices)
        if (min_z + height * 0.69 <= centre.z <= min_z + height * 0.89 and
                centre.y <= min_y + depth * 0.31 and abs(centre.x) <= width * 0.24):
            polys.append([[float(uv[i].uv.x), float(uv[i].uv.y)] for i in poly.loop_indices])
    material = obj.data.materials[0]
    image = next((n.image.name for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and 'basecolor' in n.image.name.lower()), None)
    result[image] = polys
out = Path(r"C:\Users\Jash\Desktop\Waste to wealth\art\build\textures\meshy\facial_uvs.json")
out.write_text(json.dumps(result), encoding="utf-8")
print(out)
