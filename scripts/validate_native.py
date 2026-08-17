import bpy
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path.cwd()
STREAM = ROOT / 'build_output' / 'kodiaq_cs' / 'stream'
OUT = ROOT / 'build_output' / 'native_roundtrip'
OUT.mkdir(parents=True, exist_ok=True)
yft = STREAM / 'kodiaqcs.yft'
if not yft.exists():
    raise RuntimeError('Native kodiaqcs.yft is missing')

# Start from a blank Blender scene so this validates the actual binary written to disk,
# not the source objects that produced it.
bpy.ops.wm.read_homefile(use_empty=True)

res = bpy.ops.sollumz.import_assets(
    directory=str(STREAM),
    files=[{'name': 'kodiaqcs.yft'}],
    use_custom_settings=True,
    import_as_asset=False,
    split_by_group=True,
    dwd_import_external_skeleton='NO',
    dwd_import_external_skeleton_saved_path='',
    frag_import_vehicle_windows=False,
    ymap_skip_missing_entities=True,
    ymap_exclude_entities=False,
    ymap_box_occluders=False,
    ymap_model_occluders=False,
    ymap_car_generators=False,
    ymap_instance_entities=True,
    ytyp_mlo_instance_entities=True,
    textures_mode='PACK',
    textures_extract_custom_directory='',
)
print('Native import result:', res)
if res != {'FINISHED'}:
    raise RuntimeError(f'Native YFT import failed: {res}')

frags = [o for o in bpy.context.scene.objects if getattr(o, 'sollum_type', '') == 'sollumz_fragment']
if not frags:
    raise RuntimeError('Native YFT imported but no Fragment object was created')
frag = next((o for o in frags if o.name.startswith('kodiaqcs')), frags[0])

# Native binary must retain an armature, drawable and a bound composite.
if frag.type != 'ARMATURE' or len(frag.data.bones) < 1:
    raise RuntimeError('Native YFT has no usable skeleton')
drawables = [o for o in frag.children if getattr(o, 'sollum_type', '') == 'sollumz_drawable']
composites = [o for o in frag.children if getattr(o, 'sollum_type', '') == 'sollumz_bound_composite']
if not drawables:
    raise RuntimeError('Native YFT roundtrip has no Drawable')
if not composites:
    raise RuntimeError('Native YFT roundtrip has no Bound Composite')

# Re-export the imported native YFT to CWXML. This verifies PyMateria can decode
# the binary and Sollumz still sees the expected Physics structure afterward.
bpy.ops.object.select_all(action='DESELECT')
frag.select_set(True)
bpy.context.view_layer.objects.active = frag
res = bpy.ops.sollumz.export_assets(
    directory=str(OUT),
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
print('Roundtrip CWXML export result:', res)
xml = OUT / 'kodiaqcs.yft.xml'
if not xml.exists():
    raise RuntimeError('Native roundtrip CWXML was not produced')
root = ET.parse(xml).getroot()
if root.find('./Physics/LOD1') is None:
    raise RuntimeError('Physics/LOD1 was lost in native YFT roundtrip')
if root.find('./Physics/LOD1/Archetype/Bounds') is None:
    raise RuntimeError('Bound Composite was lost in native YFT roundtrip')
groups = root.findall('./Physics/LOD1/Groups/Item')
children = root.findall('./Physics/LOD1/Children/Item')
if not groups or not children:
    raise RuntimeError(f'Native roundtrip physics incomplete: groups={len(groups)} children={len(children)}')

print('NATIVE ROUNDTRIP PASSED', {
    'bones': len(frag.data.bones),
    'drawables': len(drawables),
    'composites': len(composites),
    'groups': len(groups),
    'children': len(children),
    'native_size': yft.stat().st_size,
})
