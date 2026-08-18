import bpy
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'build_output'
OUT.mkdir(parents=True, exist_ok=True)

# Export the generated model without invoking Eevee/OpenGL. This gives CI a
# GPU-independent visual QA source that can be inspected outside Blender.
bpy.ops.object.select_all(action='DESELECT')
selected = []
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and not obj.name.endswith('.col'):
        obj.select_set(True)
        selected.append(obj)

if not selected:
    raise RuntimeError('No V6 mesh objects available for OBJ QA export')

bpy.context.view_layer.objects.active = selected[0]
out = OUT / 'V6_preview_source.obj'
bpy.ops.wm.obj_export(
    filepath=str(out),
    export_selected_objects=True,
    export_materials=True,
    export_uv=True,
    export_normals=True,
)
print('V6 OBJ QA READY', out, 'meshes=', len(selected))
