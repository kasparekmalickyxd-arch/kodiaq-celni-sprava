import bpy
from pathlib import Path
from szio.dds import DDS_HEADER

ROOT = Path.cwd()

from Sollumz.ydr.shader_materials import create_shader
from Sollumz.sollumz_properties import SollumType


def make_bc1_dds(width=4, height=4, fill=0x10):
    """Create the same minimal, valid packed BC1/DXT1 DDS shape used by Sollumz tests."""
    block_size = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * 8
    header = DDS_HEADER()
    header.dwSize = 124
    header.dwFlags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000
    header.dwWidth = width
    header.dwHeight = height
    header.dwPitchOrLinearSize = block_size
    header.dwMipMapCount = 1
    header.ddspf.dwSize = 32
    header.ddspf.dwFlags = 0x4
    header.ddspf.dwFourCC = b'DXT1'
    header.dwCaps = 0x1000
    return bytes(bytearray(b'DDS ') + bytes(header) + bytes([fill]) * block_size)


def packed_dds(name, fill):
    old = bpy.data.images.get(name)
    if old is not None:
        bpy.data.images.remove(old)
    dds = make_bc1_dds(fill=fill)
    img = bpy.data.images.new(name=name, width=1, height=1)
    img.source = 'FILE'
    img.filepath = f'//{name}.dds'
    img.pack(data=dds, data_len=len(dds))
    return img

# Real packed DDS images are important here. A generated Blender image with
# image.pack() exported as a null Texture parameter in CWXML/CodeWalker.
tex_diffuse = packed_dds('v4_diffuse', 0x10)
tex_damage = packed_dds('v4_damage', 0x22)
tex_dirt = packed_dds('v4_dirt', 0x44)
tex_spec = packed_dds('v4_spec', 0x66)
tex_normal = packed_dds('v4_normal', 0x88)
tex_neutral = packed_dds('v4_neutral', 0xAA)

# Only drawable model meshes are allowed through this pass. In the previous V4
# attempt the collision bound's GTA collision material was accidentally replaced
# by a render material, which removed the Physics children during export.
drawable_meshes = [
    o for o in bpy.context.scene.objects
    if o.type == 'MESH' and getattr(o, 'sollum_type', None) == SollumType.DRAWABLE_MODEL
]
if not drawable_meshes:
    raise RuntimeError('No Sollumz Drawable Model meshes found')

old_materials = []
seen = set()
for obj in drawable_meshes:
    for mat in obj.data.materials:
        if mat is not None and mat.name not in seen:
            old_materials.append(mat)
            seen.add(mat.name)

replacement = {}
for idx, old in enumerate(old_materials):
    mat = create_shader('vehicle_paint1.sps')
    mat.name = 'V4_' + old.name
    replacement[old.name] = mat

    for node in mat.node_tree.nodes:
        if node.type != 'TEX_IMAGE':
            continue
        n = node.name.lower()
        if 'damage' in n:
            img = tex_damage
        elif 'dirt' in n:
            img = tex_dirt
        elif 'spec' in n:
            img = tex_spec
        elif 'bump' in n or 'normal' in n:
            img = tex_normal
        elif 'diffuse' in n:
            img = tex_diffuse
        else:
            img = tex_neutral
        node.image = img
        node.texture_properties.embedded = True

for obj in drawable_meshes:
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

# Hard gates inside Blender before writing the file.
problems = []
for obj in drawable_meshes:
    for mat in obj.data.materials:
        if mat is None:
            continue
        fn = getattr(getattr(mat, 'shader_properties', None), 'filename', '')
        if fn == 'default.sps':
            problems.append(f'{obj.name}: default.sps')
        for node in mat.node_tree.nodes if mat.node_tree else []:
            if node.type == 'TEX_IMAGE':
                if node.image is None:
                    problems.append(f'{obj.name}/{mat.name}: null texture {node.name}')
                elif node.image.packed_file is None:
                    problems.append(f'{obj.name}/{mat.name}: unpacked texture {node.name}')

# Verify the collision was left intact and is still using a collision material.
collisions = [o for o in bpy.context.scene.objects if o.name == 'chassis.col']
if len(collisions) != 1:
    problems.append(f'expected one chassis.col, got {len(collisions)}')
else:
    col = collisions[0]
    if getattr(col, 'sollum_type', None) not in {
        SollumType.BOUND_BOX, SollumType.BOUND_GEOMETRY, SollumType.BOUND_GEOMETRYBVH
    }:
        problems.append(f'chassis.col wrong type: {getattr(col, "sollum_type", None)}')
    if not col.data.materials:
        problems.append('chassis.col has no collision material')
    else:
        cmat = col.data.materials[0]
        if getattr(cmat, 'sollum_type', None) != 'sollumz_collision_material':
            # The enum/property representation differs slightly across Sollumz
            # versions, so also accept the known collision shader property.
            if not hasattr(cmat, 'collision_properties'):
                problems.append(f'chassis.col material was replaced: {cmat.name}')

if problems:
    raise RuntimeError('V4 material hardening failed: ' + '; '.join(problems[:30]))

out = ROOT / 'build_output' / 'kodiaqcs.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('V4 VEHICLE MATERIALS READY', {
    'drawable_meshes': len(drawable_meshes),
    'replaced_materials': len(replacement),
    'shader': 'vehicle_paint1.sps',
    'packed_dds': 6,
    'collision_material': collisions[0].data.materials[0].name if collisions else None,
})
