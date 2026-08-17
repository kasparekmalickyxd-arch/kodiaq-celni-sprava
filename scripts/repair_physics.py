import bpy
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path.cwd()
STREAM = ROOT / 'build_output' / 'kodiaq_cs' / 'stream'
XML_DIR = ROOT / 'build_output' / 'cwxml_repaired'
XML_DIR.mkdir(parents=True, exist_ok=True)
STREAM.mkdir(parents=True, exist_ok=True)

from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.boundhelper import create_bound_box
from Sollumz.tools.blenderhelper import create_empty_object, add_child_of_bone_constraint, delete_hierarchy
from Sollumz.ybn.collision_materials import create_collision_material_from_index

# Find fragment.
frags = [o for o in bpy.context.scene.objects if getattr(o, 'sollum_type', '') == SollumType.FRAGMENT]
if not frags:
    frags = [o for o in bpy.context.scene.objects if o.name == 'kodiaqcs' and o.type == 'ARMATURE']
if not frags:
    raise RuntimeError('kodiaqcs fragment not found')
frag = frags[0]
frag.name = 'kodiaqcs'

if 'chassis' not in frag.data.bones:
    raise RuntimeError('chassis bone not found')

# Remove any old/partial composite before creating a deterministic one.
for child in list(frag.children):
    if getattr(child, 'sollum_type', None) == SollumType.BOUND_COMPOSITE:
        delete_hierarchy(child)

# Create a simple, stable chassis collision. This is intentionally conservative:
# one primitive bound, one physics group, one physics child.
composite = create_empty_object(SollumType.BOUND_COMPOSITE, name='kodiaqcs.col')
composite.parent = frag
composite.location = (0.0, 0.0, 0.0)

col = create_bound_box()
col.name = 'chassis.col'
col.parent = composite
# primitive is created as a 1m box; size to the lower body envelope
col.dimensions = (1.72, 4.10, 1.20)
bpy.context.view_layer.objects.active = col
col.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
# Keep its local offset modest; the COPY_TRANSFORMS constraint adds chassis-bone placement.
col.location = (0.0, 0.0, 0.25)

# Collision material is required for the exporter to treat this as an active physics child.
col.data.materials.clear()
col.data.materials.append(create_collision_material_from_index(0))

# Link collision to root chassis bone and enable bone physics.
chassis = frag.data.bones['chassis']
chassis.sollumz_use_physics = True
try:
    chassis.group_properties.strength = -1.0
except Exception:
    pass
add_child_of_bone_constraint(col, frag, 'chassis')
col.child_properties.mass = 2050.0

# Keep non-root bones non-physics until each has a dedicated collision.
for bone in frag.data.bones:
    if bone.name != 'chassis':
        bone.sollumz_use_physics = False

# Save repaired build source before exporting.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'build_output' / 'kodiaqcs.blend'))

# Export CWXML first so CI can structurally validate the fragment.
bpy.ops.object.select_all(action='DESELECT')
frag.select_set(True)
bpy.context.view_layer.objects.active = frag

res = bpy.ops.sollumz.export_assets(
    directory=str(XML_DIR),
    direct_export=True,
    use_custom_settings=True,
    target_formats={'CWXML'},
    target_versions={'GEN8'},
    limit_to_selected=True,
    exclude_skeleton=False,
    ymap_exclude_entities=False,
    ymap_box_occluders=False,
    ymap_model_occluders=False,
    ymap_car_generators=False,
    apply_transforms=False,
    mesh_domain='FACE_CORNER',
    export_ytyps=False,
    export_ytyps_include='ALL',
    export_ymaps=False,
    export_ymaps_include='ALL',
    export_ytds=False,
    export_ytds_include='ALL',
)
print('CWXML repaired export:', res)

xml_path = XML_DIR / 'kodiaqcs.yft.xml'
if not xml_path.exists():
    raise RuntimeError('repaired YFT XML was not produced')
root = ET.parse(xml_path).getroot()
physics = root.find('./Physics/LOD1')
if physics is None:
    raise RuntimeError('repaired YFT still has no Physics/LOD1 section')
if root.find('./Physics/LOD1/Archetype/Bounds') is None:
    raise RuntimeError('repaired YFT has no physics Bound Composite')
if len(root.findall('./Physics/LOD1/Groups/Item')) < 1:
    raise RuntimeError('repaired YFT has no physics groups')
if len(root.findall('./Physics/LOD1/Children/Item')) < 1:
    raise RuntimeError('repaired YFT has no physics children')
print('Physics XML validation passed')

# Delete stale native YFTs and regenerate from the repaired fragment.
for name in ('kodiaqcs.yft', 'kodiaqcs_hi.yft'):
    p = STREAM / name
    if p.exists():
        p.unlink()

res = bpy.ops.sollumz.export_assets(
    directory=str(STREAM),
    direct_export=True,
    use_custom_settings=True,
    target_formats={'NATIVE'},
    target_versions={'GEN8'},
    limit_to_selected=True,
    exclude_skeleton=False,
    ymap_exclude_entities=False,
    ymap_box_occluders=False,
    ymap_model_occluders=False,
    ymap_car_generators=False,
    apply_transforms=False,
    mesh_domain='FACE_CORNER',
    export_ytyps=False,
    export_ytyps_include='ALL',
    export_ymaps=False,
    export_ymaps_include='ALL',
    export_ytds=False,
    export_ytds_include='ALL',
)
print('Native repaired YFT export:', res)

# Normalize version subdirectories.
for subname in ('gen8', 'legacy'):
    sub = STREAM / subname
    if sub.exists():
        for p in sub.iterdir():
            if p.is_file():
                (STREAM / p.name).write_bytes(p.read_bytes())

# A separate hi file is conventional for vehicles. If no true VeryHigh LOD exists,
# duplicate the structurally valid YFT rather than keeping a stale pre-repair file.
yft = STREAM / 'kodiaqcs.yft'
if not yft.exists():
    raise RuntimeError('native repaired kodiaqcs.yft not produced')
hi = STREAM / 'kodiaqcs_hi.yft'
if not hi.exists():
    hi.write_bytes(yft.read_bytes())

print('REPAIRED STREAM:', [(p.name, p.stat().st_size) for p in STREAM.iterdir() if p.is_file()])
