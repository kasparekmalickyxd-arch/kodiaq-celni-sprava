import bpy
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'build_output' / 'kodiaq_cs'
STREAM = OUT / 'stream'
STREAM.mkdir(parents=True, exist_ok=True)

# Add the vertex channels expected by Sollumz vehicle shaders.
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

# Re-export the vehicle after channel cleanup.
bpy.ops.object.select_all(action='DESELECT')
frags = [o for o in bpy.context.scene.objects if getattr(o, 'sollum_type', '') == 'sollumz_fragment']
if not frags:
    # fall back to armature named kodiaqcs
    frags = [o for o in bpy.context.scene.objects if o.name == 'kodiaqcs']
if not frags:
    raise RuntimeError('kodiaqcs fragment not found')
frag = frags[0]
frag.select_set(True)
bpy.context.view_layer.objects.active = frag

print('Re-exporting cleaned native YFT...')
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
print('YFT export:', res)

# Export the created texture dictionary explicitly. The generic asset export does
# not export project TXDs unless requested, while the dedicated YTD operator does.
txds = bpy.context.scene.sz_txds.texture_dictionaries
if not txds:
    raise RuntimeError('No texture dictionary exists in the build project')
print('TXDs:', [t.name for t in txds])

res = bpy.ops.sollumz.export_ytd(
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
print('YTD export:', res)

# Flatten optional version directories.
for subname in ('gen8', 'legacy'):
    sub = STREAM / subname
    if sub.exists():
        for p in sub.iterdir():
            if p.is_file():
                (STREAM / p.name).write_bytes(p.read_bytes())

# Ensure conventional FiveM _hi file is present.
yft = STREAM / 'kodiaqcs.yft'
if yft.exists() and not (STREAM / 'kodiaqcs_hi.yft').exists():
    (STREAM / 'kodiaqcs_hi.yft').write_bytes(yft.read_bytes())

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'build_output' / 'kodiaqcs_final.blend'))
print('FINAL STREAM:', [(p.name, p.stat().st_size) for p in STREAM.iterdir() if p.is_file()])
