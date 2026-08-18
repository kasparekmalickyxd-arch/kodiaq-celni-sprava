import bpy
import struct
from pathlib import Path
from szio.dds import DDS_HEADER
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.sollumz_properties import SollumType, MaterialType

ROOT=Path.cwd()

def rgb565(rgb):
    r,g,b=rgb
    return ((r>>3)<<11)|((g>>2)<<5)|(b>>3)

def make_solid_bc1(rgb):
    c0=rgb565(rgb)
    if c0==0: c0=1
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
 'BODY_WHITE':(242,246,250),
 'TRIM_BLACK':(8,10,14),
 'METAL_DARK':(30,32,36),
 'METAL_SILVER':(165,170,178),
 'GLASS_DARK':(16,28,40),
 'LIGHT_WHITE':(232,242,250),
 'LIGHT_RED':(245,12,18),
 'LIGHT_BLUE':(0,98,255),
 'BRAKE_RED':(180,5,10),
 'CS_BLUE':(0,88,190),
 'CS_BLUE_DARK':(0,42,125),
 'SIGN_AMBER':(255,155,12),
}

def role_for(name):
    u=name.upper()
    # New custom materials first.
    if 'CS_BLUE_DARK' in u: return 'CS_BLUE_DARK'
    if 'CS_BLUE' in u: return 'CS_BLUE'
    if 'SIGN_AMBER' in u: return 'SIGN_AMBER'
    if 'LIGHT_BLUE' in u: return 'LIGHT_BLUE'
    if 'LIGHT_RED' in u: return 'LIGHT_RED'
    if 'BODY_WHITE' in u: return 'BODY_WHITE'
    if 'TRIM_BLACK' in u: return 'TRIM_BLACK'
    # Warehouse source materials.
    if 'CARPAINT' in u: return 'BODY_WHITE'
    if 'WINDOWS' in u: return 'GLASS_DARK'
    if 'LIGHTS_GLASS' in u or 'LIGHTS1' in u: return 'LIGHT_WHITE'
    if 'CALIPERS' in u: return 'BRAKE_RED'
    if u == 'RED' or u.startswith('RED.'): return 'LIGHT_RED'
    if 'TYRES' in u or 'MATTE BLACK' in u or 'BLACK1' in u: return 'TRIM_BLACK'
    if 'BRAKE DISCS' in u or 'CHROME' in u or 'COLOR M03' in u or '*16' in u or '*3' in u: return 'METAL_SILVER'
    if '*30' in u or '*6' in u or '*2' in u or '*15' in u or '*1' in u: return 'METAL_DARK'
    if '<AUTO>1' in u: return 'GLASS_DARK'
    if '<AUTO>' in u or '<AUTO>5' in u: return 'TRIM_BLACK'
    if '<AUTO>2' in u or '<AUTO>3' in u or '<AUTO>6' in u: return 'METAL_DARK'
    return 'TRIM_BLACK'

images={k:packed('wh_'+k.lower(),rgb) for k,rgb in PALETTE.items()}
neutral=packed('wh_neutral',(245,245,245))
spec=packed('wh_spec',(145,145,145))
normal=packed('wh_normal',(128,128,255))
dirt=packed('wh_dirt',(238,238,238))

drawable_meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and getattr(o,'sollum_type',None)==SollumType.DRAWABLE_MODEL]
if not drawable_meshes:
    raise RuntimeError('No Warehouse Drawable Model meshes found')

old=[]; seen=set()
for o in drawable_meshes:
    for m in o.data.materials:
        if m and m.name not in seen:
            seen.add(m.name); old.append(m)

replacement={}
for m in old:
    role=role_for(m.name)
    safe=create_shader('vehicle_paint1.sps')
    safe.name='WH_'+role+'_'+m.name
    replacement[m.name]=safe
    for node in safe.node_tree.nodes:
        if node.type!='TEX_IMAGE': continue
        n=node.name.lower()
        if 'diffuse' in n: img=images[role]
        elif 'damage' in n: img=neutral
        elif 'dirt' in n: img=dirt
        elif 'spec' in n: img=spec
        elif 'bump' in n or 'normal' in n: img=normal
        else: img=neutral
        node.image=img
        node.texture_properties.embedded=True

for o in drawable_meshes:
    me=o.data
    for i,m in enumerate(me.materials):
        if m and m.name in replacement:
            me.materials[i]=replacement[m.name]
    while len(me.uv_layers)<2:
        me.uv_layers.new(name=f'UVMap {len(me.uv_layers)}')
    me.uv_layers[0].name='UVMap 0'; me.uv_layers[1].name='UVMap 1'
    for cname in ('Color 0','Color 1'):
        attr=me.color_attributes.get(cname)
        if attr is None:
            attr=me.color_attributes.new(name=cname,type='BYTE_COLOR',domain='CORNER')
        for item in attr.data:
            item.color=(1.0,1.0,1.0,1.0)

problems=[]
for o in drawable_meshes:
    if len(o.data.vertices)>65000:
        problems.append(f'{o.name}: {len(o.data.vertices)} vertices exceeds safe per-model limit')
    for m in o.data.materials:
        if not m: continue
        fn=getattr(getattr(m,'shader_properties',None),'filename','')
        if fn=='default.sps': problems.append(o.name+': default.sps')
        if fn!='vehicle_paint1.sps': problems.append(o.name+': unexpected shader '+str(fn))
        for node in m.node_tree.nodes if m.node_tree else []:
            if node.type=='TEX_IMAGE':
                if node.image is None: problems.append(o.name+'/'+m.name+': null '+node.name)
                elif node.image.packed_file is None: problems.append(o.name+'/'+m.name+': unpacked '+node.name)

collisions=[o for o in bpy.context.scene.objects if o.name=='chassis.col']
if len(collisions)!=1:
    problems.append(f'expected one chassis.col, got {len(collisions)}')
else:
    col=collisions[0]
    if getattr(col,'sollum_type',None) not in {SollumType.BOUND_BOX,SollumType.BOUND_GEOMETRY,SollumType.BOUND_GEOMETRYBVH}:
        problems.append('chassis.col wrong type')
    if not col.data.materials or getattr(col.data.materials[0],'sollum_type',None)!=MaterialType.COLLISION:
        problems.append('chassis.col collision material invalid')

if problems:
    raise RuntimeError('Warehouse material hardening failed: '+'; '.join(problems[:40]))

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))
print('WAREHOUSE SAFE MATERIALS READY', {
    'drawable_meshes':len(drawable_meshes),
    'materials':len(replacement),
    'roles':sorted(set(role_for(m.name) for m in old)),
    'max_vertices':max(len(o.data.vertices) for o in drawable_meshes)
})
