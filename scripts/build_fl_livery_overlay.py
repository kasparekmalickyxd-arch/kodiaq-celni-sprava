import bpy
import math
import struct
from pathlib import Path
from szio.dds import DDS_HEADER
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.sollumz_properties import SollumType

ROOT = Path.cwd()
SRC = ROOT / 'build_output' / 'fl_overlay_src'
OUT = ROOT / 'build_output' / 'fl_overlay_native'
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---------- image/material helpers ----------
def rgb565(rgb):
    r,g,b=rgb
    return ((r>>3)<<11)|((g>>2)<<5)|(b>>3)

def make_solid_bc1(rgb):
    c0=rgb565(rgb) or 1
    block=struct.pack('<HHI',c0,0,0)
    h=DDS_HEADER(); h.dwSize=124
    h.dwFlags=0x1|0x2|0x4|0x1000|0x80000
    h.dwWidth=4; h.dwHeight=4; h.dwPitchOrLinearSize=8; h.dwMipMapCount=1
    h.ddspf.dwSize=32; h.ddspf.dwFlags=0x4; h.ddspf.dwFourCC=b'DXT1'; h.dwCaps=0x1000
    return bytes(bytearray(b'DDS ')+bytes(h)+block)

def solid_image(name,rgb):
    data=make_solid_bc1(rgb)
    img=bpy.data.images.new(name=name,width=4,height=4)
    img.source='FILE'; img.filepath=f'//{name}.dds'; img.pack(data=data,data_len=len(data))
    return img

neutral=solid_image('fl_overlay_neutral',(245,245,245))
spec=solid_image('fl_overlay_spec',(120,120,120))
normal=solid_image('fl_overlay_normal',(128,128,255))
dirt=solid_image('fl_overlay_dirt',(245,245,245))

def livery_material(name, png_name):
    m=create_shader('vehicle_paint1.sps')
    m.name=name
    img=bpy.data.images.load(str(SRC/png_name),check_existing=False)
    img.name=name+'_diffuse'
    img.pack()
    for node in m.node_tree.nodes:
        if node.type!='TEX_IMAGE':
            continue
        n=node.name.lower()
        if 'diffuse' in n: node.image=img
        elif 'damage' in n: node.image=neutral
        elif 'dirt' in n: node.image=dirt
        elif 'spec' in n: node.image=spec
        elif 'bump' in n or 'normal' in n: node.image=normal
        else: node.image=neutral
        try: node.texture_properties.embedded=True
        except Exception: pass
    return m

MAT_SIDE=livery_material('FL_CS_SIDE','cs_side.png')
MAT_HOOD=livery_material('FL_CS_HOOD','cs_hood.png')
MAT_REAR=livery_material('FL_CS_REAR','cs_rear.png')

# ---------- mesh helpers ----------
def make_mesh(name, verts, faces, vertex_uv, material):
    me=bpy.data.meshes.new(name+'.mesh')
    me.from_pydata(verts,[],faces)
    me.update()
    obj=bpy.data.objects.new(name,me)
    bpy.context.collection.objects.link(obj)
    me.materials.append(material)
    uv=me.uv_layers.new(name='UVMap 0')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi=me.loops[li].vertex_index
            uv.data[li].uv=vertex_uv[vi]
    # shaders expect vehicle vertex colors
    for cname in ('Color 0','Color 1'):
        attr=me.color_attributes.new(name=cname,type='BYTE_COLOR',domain='CORNER')
        for item in attr.data: item.color=(1.0,1.0,1.0,1.0)
    return obj

# Side strip follows a mild Kodiaq body taper. X is left/right, Y front/back, Z up.
ys=[1.40,0.70,-0.55,-1.42]
xs=[0.905,0.947,0.952,0.918]
z0,z1=0.74,1.075
us=[0.0,0.28,0.72,1.0]

# Right side: outward normal +X.
verts=[]; uvs=[]
for x,y,u in zip(xs,ys,us):
    verts += [(x,y,z0),(x,y,z1)]
    uvs += [(u,0.0),(u,1.0)]
faces=[]
for i in range(3):
    a=i*2; b=(i+1)*2
    faces.append((a,a+1,b+1,b))
make_mesh('fl_cs_side_right',verts,faces,uvs,MAT_SIDE)

# Left side: mirror geometry and UV horizontally so lettering is not reversed.
verts=[]; uvs=[]
for x,y,u in zip(xs,ys,us):
    verts += [(-x,y,z0),(-x,y,z1)]
    uvs += [(1.0-u,0.0),(1.0-u,1.0)]
faces=[]
for i in range(3):
    a=i*2; b=(i+1)*2
    faces.append((a,b,b+1,a+1))
make_mesh('fl_cs_side_left',verts,faces,uvs,MAT_SIDE)

# Hood decal, slightly above the sheet metal and following its slope.
verts=[
    (-0.56,0.92,1.105),(0.56,0.92,1.105),
    (0.48,1.78,0.945),(-0.48,1.78,0.945),
]
uvs=[(0,0),(1,0),(1,1),(0,1)]
make_mesh('fl_cs_hood',verts,[(0,1,2,3)],uvs,MAT_HOOD)

# Rear tailgate band.
verts=[
    (-0.73,-2.115,0.82),(0.73,-2.115,0.82),
    (0.69,-2.105,1.055),(-0.69,-2.105,1.055),
]
uvs=[(0,0),(1,0),(1,1),(0,1)]
make_mesh('fl_cs_rear',verts,[(0,1,2,3)],uvs,MAT_REAR)

# Convert the four overlay meshes to one static GTA Drawable.
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type=='MESH': o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type=='MESH')
res=bpy.ops.sollumz.converttodrawable()
print('CONVERT DRAWABLE',res)

drawables=[o for o in bpy.context.scene.objects if getattr(o,'sollum_type',None)==SollumType.DRAWABLE]
if len(drawables)!=1:
    raise RuntimeError(f'Expected exactly one Drawable, got {len(drawables)}')
d=drawables[0]; d.name='civkodiaqfl_cs_overlay'

# Ensure every child mesh still carries expected channels/materials.
children=[o for o in d.children_recursive if o.type=='MESH']
if len(children)<4:
    raise RuntimeError(f'Overlay lost geometry: {len(children)} mesh children')
for o in children:
    if not o.data.uv_layers:
        o.data.uv_layers.new(name='UVMap 0')
    o.data.uv_layers[0].name='UVMap 0'
    if 'Color 0' not in o.data.color_attributes:
        a=o.data.color_attributes.new(name='Color 0',type='BYTE_COLOR',domain='CORNER')
        for x in a.data: x.color=(1,1,1,1)
    if 'Color 1' not in o.data.color_attributes:
        a=o.data.color_attributes.new(name='Color 1',type='BYTE_COLOR',domain='CORNER')
        for x in a.data: x.color=(1,1,1,1)

bpy.ops.object.select_all(action='DESELECT')
d.select_set(True); bpy.context.view_layer.objects.active=d
res=bpy.ops.sollumz.export_assets(
    directory=str(OUT),
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
print('NATIVE OVERLAY EXPORT',res)

out=OUT/'civkodiaqfl_cs_overlay.ydr'
if not out.exists() or out.stat().st_size<1000:
    raise RuntimeError('Native overlay YDR missing/suspiciously small')

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'civkodiaqfl_cs_overlay.blend'))
print('FL CUSTOMS OVERLAY READY', {'ydr_bytes':out.stat().st_size,'meshes':len(children)})
