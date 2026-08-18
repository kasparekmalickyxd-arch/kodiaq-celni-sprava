import bpy
import struct
from pathlib import Path
from szio.dds import DDS_HEADER
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.sollumz_properties import SollumType, MaterialType

ROOT = Path.cwd()

# Solid-colour BC1 blocks. Unlike the old diagnostic byte-fill textures these
# are real DXT1 blocks, so the game receives the intended white/blue/red/black.
def rgb565(rgb):
    r,g,b=rgb
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def make_solid_bc1(rgb):
    c0=rgb565(rgb)
    # DXT1 with index 0 everywhere. Keep c0 > c1 for normal opaque mode.
    if c0 == 0: c0 = 1
    block=struct.pack('<HHI',c0,0,0)
    h=DDS_HEADER(); h.dwSize=124
    h.dwFlags=0x1|0x2|0x4|0x1000|0x80000
    h.dwWidth=4; h.dwHeight=4; h.dwPitchOrLinearSize=8; h.dwMipMapCount=1
    h.ddspf.dwSize=32; h.ddspf.dwFlags=0x4; h.ddspf.dwFourCC=b'DXT1'; h.dwCaps=0x1000
    return bytes(bytearray(b'DDS ')+bytes(h)+block)

def packed(name,rgb):
    old=bpy.data.images.get(name)
    if old is not None: bpy.data.images.remove(old)
    data=make_solid_bc1(rgb)
    img=bpy.data.images.new(name=name,width=4,height=4)
    img.source='FILE'; img.filepath=f'//{name}.dds'; img.pack(data=data,data_len=len(data))
    return img

PALETTE={
 'BODY_WHITE':(240,245,250), 'TRIM_BLACK':(7,10,15), 'GLASS_DARK':(12,28,42),
 'METAL_SILVER':(128,134,142), 'METAL_DARK':(28,30,35),
 'CS_BLUE':(0,92,190), 'CS_BLUE_DARK':(0,45,130),
 'LIGHT_RED':(250,12,18), 'LIGHT_BLUE':(0,105,255), 'LIGHT_WHITE':(236,247,255),
 'SIGN_AMBER':(255,155,12), 'PLATE_WHITE':(238,240,242), 'BRAKE_RED':(180,8,12)
}

def role_for(name):
    u=name.upper()
    # Dark blue must win before the generic blue match.
    for key in ('CS_BLUE_DARK','BODY_WHITE','TRIM_BLACK','GLASS_DARK','METAL_SILVER','METAL_DARK',
                'LIGHT_RED','LIGHT_BLUE','LIGHT_WHITE','SIGN_AMBER','PLATE_WHITE','BRAKE_RED','CS_BLUE'):
        if key in u: return key
    return 'BODY_WHITE'

images={k:packed('v6_'+k.lower(),v) for k,v in PALETTE.items()}
white=packed('v6_neutral_white',(245,245,245))
spec=packed('v6_spec',(145,145,145))
normal=packed('v6_normal',(128,128,255))
dirt=packed('v6_dirt',(235,235,235))

drawable_meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and getattr(o,'sollum_type',None)==SollumType.DRAWABLE_MODEL]
if not drawable_meshes: raise RuntimeError('No V6 Drawable Model meshes found')

old_materials=[]; seen=set()
for obj in drawable_meshes:
    for m in obj.data.materials:
        if m and m.name not in seen:
            old_materials.append(m); seen.add(m.name)

replacement={}
for old in old_materials:
    role=role_for(old.name)
    mat=create_shader('vehicle_paint1.sps')
    mat.name='V6_'+role+'_'+old.name
    replacement[old.name]=mat
    diffuse=images[role]
    for node in mat.node_tree.nodes:
        if node.type!='TEX_IMAGE': continue
        n=node.name.lower()
        if 'diffuse' in n: img=diffuse
        elif 'damage' in n: img=white
        elif 'dirt' in n: img=dirt
        elif 'spec' in n: img=spec
        elif 'bump' in n or 'normal' in n: img=normal
        else: img=white
        node.image=img; node.texture_properties.embedded=True

for obj in drawable_meshes:
    me=obj.data
    for i,slot in enumerate(me.materials):
        if slot and slot.name in replacement: me.materials[i]=replacement[slot.name]
    while len(me.uv_layers)<2: me.uv_layers.new(name=f'UVMap {len(me.uv_layers)}')
    me.uv_layers[0].name='UVMap 0'; me.uv_layers[1].name='UVMap 1'
    for cname in ('Color 0','Color 1'):
        attr=me.color_attributes.get(cname)
        if attr is None: attr=me.color_attributes.new(name=cname,type='BYTE_COLOR',domain='CORNER')
        for item in attr.data: item.color=(1.0,1.0,1.0,1.0)

problems=[]
for obj in drawable_meshes:
    for m in obj.data.materials:
        if not m: continue
        fn=getattr(getattr(m,'shader_properties',None),'filename','')
        if fn=='default.sps': problems.append(obj.name+': default.sps')
        for node in m.node_tree.nodes if m.node_tree else []:
            if node.type=='TEX_IMAGE':
                if node.image is None: problems.append(obj.name+'/'+m.name+': null '+node.name)
                elif node.image.packed_file is None: problems.append(obj.name+'/'+m.name+': unpacked '+node.name)

collisions=[o for o in bpy.context.scene.objects if o.name=='chassis.col']
if len(collisions)!=1:
    problems.append(f'expected one chassis.col, got {len(collisions)}')
else:
    col=collisions[0]
    if getattr(col,'sollum_type',None) not in {SollumType.BOUND_BOX,SollumType.BOUND_GEOMETRY,SollumType.BOUND_GEOMETRYBVH}:
        problems.append('chassis.col wrong Sollum type')
    if not col.data.materials:
        problems.append('chassis.col no material')
    elif getattr(col.data.materials[0],'sollum_type',None)!=MaterialType.COLLISION:
        problems.append('chassis.col render material leak')

if problems: raise RuntimeError('V6 material hardening failed: '+'; '.join(problems[:30]))
out=ROOT/'build_output'/'kodiaqcs.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('V6 MATERIALS READY',{'meshes':len(drawable_meshes),'materials':len(replacement),'roles':sorted(set(role_for(m.name) for m in old_materials))})
