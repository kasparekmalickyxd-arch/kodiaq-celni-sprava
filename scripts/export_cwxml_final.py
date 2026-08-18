import bpy
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path.cwd()
XML_DIR = ROOT / 'build_output' / 'cwxml_final'
XML_DIR.mkdir(parents=True, exist_ok=True)

# Add the channels expected by GTA vehicle shaders before the final export.
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name='UVMap 0')
    elif mesh.uv_layers[0].name != 'UVMap 0':
        mesh.uv_layers[0].name = 'UVMap 0'
    if 'Color 1' not in mesh.color_attributes:
        attr = mesh.color_attributes.new(name='Color 1', type='BYTE_COLOR', domain='CORNER')
        for item in attr.data:
            item.color = (1.0, 1.0, 1.0, 1.0)

frags = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE' and o.name == 'kodiaqcs']
if not frags:
    raise RuntimeError('kodiaqcs fragment not found')
frag = frags[0]

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
print('FINAL CWXML EXPORT:', res)

xml_path = XML_DIR / 'kodiaqcs.yft.xml'
if not xml_path.exists():
    raise RuntimeError('final CWXML YFT missing')
root = ET.parse(xml_path).getroot()

# Structural gates that the previous native build did not enforce.
shaders = root.findall('./Drawable/ShaderGroup/Shaders/Item')
geometries = root.findall('.//Geometries/Item')
bones = root.findall('./Drawable/Skeleton/Bones/Item')
physics_children = root.findall('./Physics/LOD1/Children/Item')
bounds = root.findall('./Physics/LOD1/Archetype/Bounds/Children/Item')

if len(shaders) < 5:
    raise RuntimeError(f'Expected multiple livery/light materials, got only {len(shaders)} shaders')
if len(geometries) < 5:
    raise RuntimeError(f'Expected multiple vehicle geometries, got only {len(geometries)}')
if len(bones) < 20:
    raise RuntimeError(f'Vehicle skeleton is incomplete: only {len(bones)} bones')
if len(physics_children) != len(bounds) or len(bounds) < 1:
    raise RuntimeError(f'Physics child/bound mismatch: children={len(physics_children)} bounds={len(bounds)}')

bone_names = [b.findtext('Name') for b in bones]
required = {
    'chassis','bodyshell','wheel_lf','wheel_rf','wheel_lr','wheel_rr',
    'seat_dside_f','seat_pside_f','door_dside_f','door_pside_f',
    'extra_1','extra_2','extra_3','extra_4'
}
missing = sorted(required - set(bone_names))
if missing:
    raise RuntimeError('Missing runtime vehicle bones: ' + ', '.join(missing))

chassis = next(b for b in bones if b.findtext('Name') == 'chassis')
rot = chassis.find('Rotation')
if rot is not None:
    x = float(rot.attrib.get('x','0')); y = float(rot.attrib.get('y','0')); z = float(rot.attrib.get('z','0')); w = float(rot.attrib.get('w','1'))
    # Identity (or sign-equivalent identity) is the safe root orientation.
    if abs(x) > 0.01 or abs(y) > 0.01 or abs(z) > 0.01 or abs(abs(w) - 1.0) > 0.01:
        raise RuntimeError(f'Chassis root rotation is not identity: {(x,y,z,w)}')

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'build_output' / 'kodiaqcs_final.blend'))
print('CWXML VALIDATION PASSED', {'shaders':len(shaders),'geometries':len(geometries),'bones':len(bones),'physics_children':len(physics_children)})
