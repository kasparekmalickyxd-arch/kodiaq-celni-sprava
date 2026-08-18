import bpy
import math
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'build_output' / 'kodiaq_cs'
STREAM = OUT / 'stream'
DATA = OUT / 'data'
CLIENT = OUT / 'client'
for p in (STREAM, DATA, CLIENT):
    p.mkdir(parents=True, exist_ok=True)

try:
    from Sollumz.sollumz_properties import SollumType
except Exception:
    import sys
    base = next((k.rsplit('.', 1)[0] for k in sys.modules if k.endswith('.sollumz_properties') and 'sollumz' in k.lower()), None)
    if not base:
        raise
    SollumType = __import__(base + '.sollumz_properties', fromlist=['SollumType']).SollumType

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Semantic materials. A later hardening pass replaces these with the same
# known-good GTA vehicle shader path that made V4/V5 spawn without crashing.
def make_mat(name, rgba, rough=0.3, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        bsdf.inputs['Base Color'].default_value = rgba
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
    return m

WHITE = make_mat('BODY_WHITE', (0.94,0.96,0.98,1), 0.24, 0.08)
BLACK = make_mat('TRIM_BLACK', (0.008,0.012,0.018,1), 0.30, 0.03)
GLASS = make_mat('GLASS_DARK', (0.016,0.035,0.055,1), 0.12, 0.0)
SILVER = make_mat('METAL_SILVER', (0.44,0.47,0.51,1), 0.18, 0.52)
DARK = make_mat('METAL_DARK', (0.06,0.07,0.09,1), 0.20, 0.58)
BLUE = make_mat('CS_BLUE', (0.0,0.24,0.82,1), 0.28, 0.0)
BLUE2 = make_mat('CS_BLUE_DARK', (0.0,0.07,0.36,1), 0.28, 0.0)
RED = make_mat('LIGHT_RED', (1.0,0.01,0.02,1), 0.12, 0.0)
LBLUE = make_mat('LIGHT_BLUE', (0.0,0.32,1.0,1), 0.12, 0.0)
WHITE_LIGHT = make_mat('LIGHT_WHITE', (0.94,0.98,1.0,1), 0.10, 0.0)
AMBER = make_mat('SIGN_AMBER', (1.0,0.38,0.015,1), 0.14, 0.0)
PLATE = make_mat('PLATE_WHITE', (0.92,0.93,0.95,1), 0.36, 0.0)
BRAKE = make_mat('BRAKE_RED', (0.62,0.01,0.02,1), 0.24, 0.18)

objects=[]
def apply_mat(o,m):
    if o.type=='MESH': o.data.materials.append(m)
    return o

def smooth(o):
    if o.type=='MESH':
        for p in o.data.polygons: p.use_smooth=True
    return o

def cube(name,loc,scale,mat,bevel=0.0,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=(scale[0]/2,scale[1]/2,scale[2]/2)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('soft','BEVEL'); mod.width=bevel; mod.segments=3
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
    apply_mat(o,mat); objects.append(o); return o

def cyl(name,loc,radius,depth,mat,rot=(0,0,0),verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; apply_mat(o,mat); smooth(o); objects.append(o); return o

def torus(name,loc,major,minor,mat,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=48,minor_segments=16,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; apply_mat(o,mat); smooth(o); objects.append(o); return o

def text_mesh(name,text,loc,size,mat,rot=(0,0,0),extrude=0.004):
    bpy.ops.object.text_add(location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.data.body=text; o.data.align_x='CENTER'; o.data.align_y='CENTER'
    o.data.size=size; o.data.extrude=extrude; o.data.bevel_depth=0.0015
    bpy.ops.object.convert(target='MESH'); apply_mat(o,mat); objects.append(o); return o

def poly_prism(name,points_xz,y,depth,mat,bevel=0.0):
    n=len(points_xz)
    verts=[(x,y-depth/2,z) for x,z in points_xz]+[(x,y+depth/2,z) for x,z in points_xz]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    for i in range(n):
        j=(i+1)%n; faces.append((i,j,n+j,n+i))
    me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); apply_mat(o,mat)
    if bevel:
        mod=o.modifiers.new('soft','BEVEL'); mod.width=bevel; mod.segments=2
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
    objects.append(o); return o

def side_panel(name,side,yz,thickness,mat):
    x=side*0.938; n=len(yz)
    verts=[(x-side*thickness/2,y,z) for y,z in yz]+[(x+side*thickness/2,y,z) for y,z in yz]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    for i in range(n):
        j=(i+1)%n; faces.append((i,j,n+j,n+i))
    me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); apply_mat(o,mat); objects.append(o); return o

# Smooth Kodiaq-II-inspired shell. Overall envelope is close to 4.76 x 1.86 m.
sections=[
 (2.38,.79,.43,.94,.58,1.03),(2.18,.88,.42,1.04,.64,1.12),(1.78,.92,.41,1.13,.69,1.22),
 (1.32,.93,.40,1.24,.70,1.30),(.94,.935,.40,1.31,.69,1.53),(.50,.935,.40,1.35,.70,1.72),
 (-.10,.935,.40,1.37,.71,1.78),(-.75,.93,.40,1.36,.70,1.76),(-1.30,.92,.41,1.33,.68,1.69),
 (-1.75,.89,.42,1.25,.65,1.55),(-2.16,.85,.44,1.11,.61,1.30),(-2.38,.78,.47,1.00,.57,1.12)]

def ring(y,w,z0,zs,rw,zr):
    return [(-w*.78,y,z0),(-w,y,z0+.19),(-w,y,zs-.10),(-w*.93,y,zs),(-rw,y,zr),
            (rw,y,zr),(w*.93,y,zs),(w,y,zs-.10),(w,y,z0+.19),(w*.78,y,z0)]
verts=[]
for s in sections: verts.extend(ring(*s))
R=10; faces=[]
for si in range(len(sections)-1):
    a=si*R; b=(si+1)*R
    for j in range(R):
        k=(j+1)%R; faces.append((a+j,a+k,b+k,b+j))
faces.append(tuple(range(R-1,-1,-1))); last=(len(sections)-1)*R; faces.append(tuple(last+j for j in range(R)))
me=bpy.data.meshes.new('body_shell_mesh'); me.from_pydata(verts,[],faces); me.update()
body=bpy.data.objects.new('body_shell',me); bpy.context.collection.objects.link(body); apply_mat(body,WHITE); smooth(body)
bev=body.modifiers.new('body_refine','BEVEL'); bev.width=.032; bev.segments=3; bev.limit_method='ANGLE'
bpy.context.view_layer.objects.active=body; bpy.ops.object.modifier_apply(modifier=bev.name); objects.append(body)

# RS lower trim, bumpers and vertical grille.
for sx in (-1,1):
    side_panel(f'rocker_black_{sx}',sx,[(1.70,.47),(-1.78,.47),(-1.88,.61),(1.82,.61)],.020,BLACK)
cube('front_splitter',(0,2.39,.51),(1.62,.14,.18),BLACK,.035)
cube('rear_diffuser',(0,-2.39,.54),(1.58,.14,.19),BLACK,.035)
for sx in (-1,1): cube(f'front_intake_{sx}',(sx*.66,2.405,.72),(.34,.045,.26),BLACK,.045)
cube('front_grille',(0,2.405,.91),(1.10,.045,.55),BLACK,.05)
for x in [-.45,-.36,-.27,-.18,-.09,0,.09,.18,.27,.36,.45]:
    cube(f'grille_slat_{x:+.2f}',(x,2.435,.91),(.022,.016,.44),SILVER,.004)
cyl('front_badge',(0,2.445,1.22),.073,.024,DARK,rot=(math.radians(90),0,0),verts=48)

# Split LED headlamps.
for sx in (-1,1):
    pts=[(sx*.86,1.19),(sx*.43,1.17),(sx*.37,1.09),(sx*.83,1.08)]
    if sx<0: pts=list(reversed(pts))
    poly_prism(f'headlight_upper_{sx}',pts,2.425,.036,WHITE_LIGHT,.012)
    cube(f'headlight_lower_{sx}',(sx*.61,2.428,1.00),(.30,.030,.085),WHITE_LIGHT,.018)

# Glass and pillars.
poly_prism('windshield',[(-.69,1.61),(-.66,1.32),(.66,1.32),(.69,1.61)],.91,.040,GLASS,.014)
poly_prism('rear_window',[(-.64,1.55),(-.61,1.25),(.61,1.25),(.64,1.55)],-1.78,.038,GLASS,.014)
for sx in (-1,1):
    side_panel(f'window_front_{sx}',sx,[(.82,1.31),(.56,1.68),(-.03,1.71),(-.04,1.31)],.018,GLASS)
    side_panel(f'window_rear_{sx}',sx,[(-.10,1.31),(-.08,1.71),(-.82,1.68),(-.92,1.31)],.018,GLASS)
    side_panel(f'window_quarter_{sx}',sx,[(-.98,1.31),(-.88,1.67),(-1.42,1.55),(-1.53,1.29)],.018,GLASS)
    side_panel(f'b_pillar_{sx}',sx,[(.02,1.28),(-.08,1.28),(-.08,1.74),(.03,1.74)],.024,BLACK)
    side_panel(f'c_pillar_{sx}',sx,[(-.88,1.28),(-.99,1.28),(-.90,1.68),(-.82,1.68)],.024,BLACK)
    cube(f'mirror_{sx}',(sx*1.00,.77,1.27),(.19,.29,.12),BLACK,.045)
    cube(f'mirror_cap_{sx}',(sx*1.015,.78,1.31),(.18,.24,.055),WHITE,.035)
    cube(f'roofrail_{sx}',(sx*.60,-.25,1.835),(.035,2.20,.045),DARK,.014)
    for y in (.83,-.08,-.93): cube(f'door_seam_{sx}_{y:+.2f}',(sx*.944,y,1.02),(.012,.018,.62),BLACK,.002)
    cube(f'handle_front_{sx}',(sx*.953,.32,1.20),(.018,.18,.035),SILVER,.012)
    cube(f'handle_rear_{sx}',(sx*.953,-.63,1.20),(.018,.18,.035),SILVER,.012)
cube('roof_center_glass',(0,-.28,1.805),(.93,1.70,.018),GLASS,.015)

# Round wheels, deep rims and red RS-style calipers.
wheel_positions={'wheel_lf':(-.94,1.43,.43),'wheel_rf':(.94,1.43,.43),'wheel_lr':(-.94,-1.35,.43),'wheel_rr':(.94,-1.35,.43)}
for name,(x,y,z) in wheel_positions.items():
    torus(name,(x,y,z),.315,.085,BLACK,rot=(0,math.radians(90),0))
    cyl(name+'_rim_outer',(x,y,z),.255,.275,DARK,rot=(0,math.radians(90),0))
    outer=.145 if x>0 else -.145
    cyl(name+'_rim_face',(x+outer,y,z),.225,.025,SILVER,rot=(0,math.radians(90),0))
    cyl(name+'_hub',(x+(outer*1.14),y,z),.064,.030,DARK,rot=(0,math.radians(90),0),verts=32)
    cube(name+'_caliper',(x+(outer*1.18),y-.14,z),(.030,.10,.18),BRAKE,.02)
    for i in range(10):
        a=math.radians(i*36); dy=math.cos(a)*.12; dz=math.sin(a)*.12
        cube(name+f'_spoke_{i}',(x+(outer*1.24),y+dy,z+dz),(.024,.23,.035),SILVER,.006,rot=(a,0,0))

# Rear full-width light signature.
cube('rear_light_bar',(0,-2.416,1.16),(1.18,.032,.048),RED,.015)
for sx in (-1,1):
    pts=[(sx*.86,1.23),(sx*.51,1.20),(sx*.48,1.10),(sx*.84,1.10)]
    if sx<0: pts=list(reversed(pts))
    poly_prism(f'taillight_{sx}',pts,-2.425,.035,RED,.014)
text_mesh('rear_skoda','SKODA',(0,-2.448,1.34),.14,SILVER,rot=(math.radians(90),0,math.radians(180)),extrude=.004)
cube('rear_plate',(0,-2.438,.91),(.50,.025,.12),PLATE,.012)

# Customs livery as fitted thin geometry, not floating blocks.
for sx in (-1,1):
    side_panel(f'cs_blue_band_{sx}',sx,[(1.30,.93),(-1.48,.93),(-1.55,1.10),(1.24,1.10)],.022,BLUE)
    for i in range(9):
        y0=1.22-i*.31
        side_panel(f'cs_chevron_{sx}_{i}',sx,[(y0,.91),(y0-.18,.91),(y0-.04,1.13),(y0+.14,1.13)],.024,BLUE if i%2==0 else BLUE2)
    rot=(math.radians(90),0,math.radians(90 if sx>0 else -90)); loc=(sx*.953,-.14,1.24)
    text_mesh(f'cs_side_text_{sx}','CELNI SPRAVA',loc,.195,BLACK,rot=rot,extrude=.003)
for i,x in enumerate([-.62,-.46,-.30,-.14,.02,.18,.34,.50,.66]):
    cube(f'hood_cs_{i}',(x,1.76,1.325),(.11,.52,.015),BLUE if i%2==0 else BLUE2,.003,rot=(0,0,math.radians(-7)))
text_mesh('hood_cs_text','CELNI SPRAVA',(0,1.39,1.335),.17,BLACK,extrude=.003)

# Emergency equipment. Extra 3 = blue, Extra 4 = red.
cube('lightbar_base',(0,-.08,1.885),(1.28,.17,.055),BLACK,.025)
for x in (-.48,-.29,-.10): cube('blue_light_module',(x,-.08,1.93),(.16,.13,.075),LBLUE,.018)
for x in (.10,.29,.48): cube('red_light_module',(x,-.08,1.93),(.16,.13,.075),RED,.018)
cube('blue_grille',(-.25,2.444,.89),(.16,.018,.055),LBLUE,.010); cube('red_grille',(.25,2.444,.89),(.16,.018,.055),RED,.010)
cube('blue_rear',(-.26,-2.447,.74),(.16,.018,.055),LBLUE,.010); cube('red_rear',(.26,-2.447,.74),(.16,.018,.055),RED,.010)

# Rear message board extras.
cube('stop_board',(0,-1.63,1.99),(1.14,.085,.34),BLACK,.025)
text_mesh('stop_text','STOP',(0,-1.681,1.99),.23,AMBER,rot=(math.radians(90),0,0),extrude=.005)
cube('follow_board',(0,-1.63,1.99),(1.14,.085,.34),BLACK,.025)
text_mesh('follow_text_1','NASLEDUJ',(0,-1.681,2.055),.112,AMBER,rot=(math.radians(90),0,0),extrude=.004)
text_mesh('follow_text_2','ME',(0,-1.681,1.925),.145,AMBER,rot=(math.radians(90),0,0),extrude=.004)
cube('sign_bracket_l',(-.42,-1.54,1.83),(.04,.12,.25),BLACK,.010); cube('sign_bracket_r',(.42,-1.54,1.83),(.04,.12,.25),BLACK,.010)

# Convert geometry to a single Sollumz Drawable then Fragment.
bpy.ops.object.select_all(action='DESELECT')
for o in objects: o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.context.scene.create_seperate_drawables=False
bpy.context.scene.auto_create_embedded_col=False
bpy.context.scene.center_drawable_to_selection=False
print('V6 convert:',bpy.ops.sollumz.converttodrawable())
drawables=[o for o in bpy.context.scene.objects if getattr(o,'sollum_type',None)==SollumType.DRAWABLE]
if not drawables: raise RuntimeError('No V6 drawable created')
drawable=drawables[-1]; drawable.name='kodiaqcs.drawable'
bpy.ops.object.select_all(action='DESELECT'); drawable.select_set(True); bpy.context.view_layer.objects.active=drawable
print('V6 fragment:',bpy.ops.sollumz.createfragment())
frags=[o for o in bpy.context.scene.objects if getattr(o,'sollum_type',None)==SollumType.FRAGMENT]
if not frags: raise RuntimeError('No V6 fragment created')
frag=frags[-1]; frag.name='kodiaqcs'

# Temporary bones. harden_vehicle.py replaces these with the proven 32-bone skeleton.
bpy.context.view_layer.objects.active=frag; bpy.ops.object.mode_set(mode='EDIT'); arm=frag.data; bones={}
def add_bone(name,head,tail,parent=None):
    b=arm.edit_bones.new(name); b.head=head; b.tail=tail
    if parent: b.parent=bones[parent]
    bones[name]=b
add_bone('chassis',(0,0,.55),(0,0,.75))
for n,p in wheel_positions.items(): add_bone(n,p,(p[0],p[1],p[2]+.20),'chassis')
for i in range(1,5): add_bone(f'extra_{i}',(0,-1.8,1.8),(0,-1.8,2.0),'chassis')
bpy.ops.object.mode_set(mode='OBJECT')

models=[o for o in drawable.children_recursive if getattr(o,'sollum_type',None)==SollumType.DRAWABLE_MODEL and o.type=='MESH']
def bone_for_model(name):
    s=name.lower()
    for n in wheel_positions:
        if s.startswith(n): return n
    if 'stop_' in s: return 'extra_1'
    if 'follow_' in s: return 'extra_2'
    if s.startswith('blue_'): return 'extra_3'
    if s.startswith('red_'): return 'extra_4'
    return 'chassis'
for m in models:
    b=bone_for_model(m.name); vg=m.vertex_groups.get(b) or m.vertex_groups.new(name=b)
    vg.add(list(range(len(m.data.vertices))),1.0,'REPLACE'); mod=m.modifiers.new('Armature','ARMATURE'); mod.object=frag

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))
print('V6 SOURCE READY',{'objects':len(objects),'drawable_models':len(models)})
