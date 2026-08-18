import bpy
from pathlib import Path

ROOT = Path.cwd()

try:
    from Sollumz.ydr.shader_materials import create_shader
except Exception:
    import sys
    base = next((k.rsplit('.', 2)[0] for k in sys.modules if k.endswith('.ydr.shader_materials') and 'sollumz' in k.lower()), None)
    if not base:
        raise
    create_shader = __import__(base + '.ydr.shader_materials', fromlist=['create_shader']).create_shader

COLORS = {
    'BODY_WHITE': (0.93, 0.95, 0.97, 1.0),
    'CS_BLUE': (0.02, 0.19, 0.75, 1.0),
    'CS_BLUE_DARK': (0.0, 0.06, 0.35, 1.0),
    'TRIM_BLACK': (0.01, 0.012, 0.018, 1.0),
    'GLASS_DARK': (0.02, 0.04, 0.07, 1.0),
    'METAL': (0.25, 0.28, 0.32, 1.0),
    'LIGHT_RED': (1.0, 0.01, 0.015, 1.0),
    'LIGHT_BLUE': (0.0, 0.20, 1.0, 1.0),
    'SIGN_AMBER': (1.0, 0.33, 0.01, 1.0),
}

def rgba_for(name):
    u = name.upper()
    # Exact/prefix matching survives Blender's .001 suffixes.
    for key, rgba in COLORS.items():
        if u == key or u.startswith(key + '.'):
            return rgba
    return (0.65, 0.65, 0.65, 1.0)


def make_packed_image(name, rgba):
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name=name, width=4, height=4, alpha=True)
    img.pixels = list(rgba) * 16
    img.update()
    # Packed generated images are embedded into the YFT by Sollumz when the
    # corresponding texture parameter has embedded=True.
    try:
        img.pack()
    except Exception:
        pass
    return img

flat_normal = make_packed_image('v4_flat_normal', (0.5, 0.5, 1.0, 1.0))
neutral_spec = make_packed_image('v4_neutral_spec', (0.35, 0.35, 0.35, 1.0))
neutral_dirt = make_packed_image('v4_neutral_dirt', (1.0, 1.0, 1.0, 1.0))
neutral_black = make_packed_image('v4_neutral_black', (0.0, 0.0, 0.0, 1.0))

# Rebuild every material as a real GTA vehicle shader. The older pipeline used
# default.sps for all vehicle surfaces and left DiffuseSampler empty.
old_materials = [m for m in list(bpy.data.materials) if getattr(m, 'sollum_type', '') and m.users > 0]
replacement = {}
for old in old_materials:
    base_name = old.name.split('.')[0]
    rgba = rgba_for(old.name)
    try:
        mat = create_shader('vehicle_paint1.sps')
    except Exception:
        mat = create_shader('vehicle_mesh.sps')
    mat.name = 'V4_' + base_name
    replacement[old.name] = mat

    diffuse = make_packed_image('v4_diff_' + base_name.lower(), rgba)
    for node in mat.node_tree.nodes:
        if node.type != 'TEX_IMAGE':
            continue
        n = node.name.lower()
        if 'bump' in n or 'normal' in n:
            img = flat_normal
        elif 'spec' in n:
            img = neutral_spec
        elif 'dirt' in n:
            img = neutral_dirt
        elif 'palette' in n or 'mask' in n:
            img = neutral_black
        else:
            img = diffuse
        node.image = img
        try:
            node.texture_properties.embedded = True
        except Exception:
            pass

# Replace material slots on all meshes, and add every channel commonly required
# by GTA vehicle shaders. This intentionally prioritizes safe spawning over
# perfect appearance for this diagnostic build.
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    mesh = obj.data
    for i, slot in enumerate(mesh.materials):
        if slot and slot.name in replacement:
            mesh.materials[i] = replacement[slot.name]

    while len(mesh.uv_layers) < 2:
        mesh.uv_layers.new(name=f'UVMap {len(mesh.uv_layers)}')
    mesh.uv_layers[0].name = 'UVMap 0'
    mesh.uv_layers[1].name = 'UVMap 1'

    for cname in ('Color 0', 'Color 1'):
        attr = mesh.color_attributes.get(cname)
        if attr is None:
            attr = mesh.color_attributes.new(name=cname, type='BYTE_COLOR', domain='CORNER')
        for item in attr.data:
            item.color = (1.0, 1.0, 1.0, 1.0)

# A hard gate: no live material may remain on default.sps, and no texture sampler
# on a live Sollumz shader may be null.
problems = []
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    for mat in obj.data.materials:
        if mat is None:
            continue
        fn = getattr(getattr(mat, 'shader_properties', None), 'filename', '')
        if fn == 'default.sps':
            problems.append(f'{obj.name}: default.sps')
        for node in mat.node_tree.nodes if mat.node_tree else []:
            if node.type == 'TEX_IMAGE' and node.image is None:
                problems.append(f'{obj.name}/{mat.name}: null texture {node.name}')
if problems:
    raise RuntimeError('V4 material hardening failed: ' + '; '.join(problems[:20]))

out = ROOT / 'build_output' / 'kodiaqcs.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('V4 VEHICLE MATERIALS READY', {
    'replaced': len(replacement),
    'live_shaders': sorted(set(getattr(m.shader_properties, 'filename', '') for m in replacement.values()))
})
