import bpy
import math
import json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path.cwd()
SRC = ROOT / 'source' / 'warehouse_kodiaq.glb'
OUT = ROOT / 'build_output' / 'kodiaq_cs'
STREAM = OUT / 'stream'
DATA = OUT / 'data'
CLIENT = OUT / 'client'
for p in (OUT, STREAM, DATA, CLIENT):
    p.mkdir(parents=True, exist_ok=True)

try:
    from Sollumz.sollumz_properties import SollumType
except Exception:
    import sys
    base = next((k.rsplit('.', 1)[0] for k in sys.modules if k.endswith('.sollumz_properties') and 'sollumz' in k.lower()), None)
    if not base:
        raise
    SollumType = __import__(base + '.sollumz_properties', fromlist=['SollumType']).SollumType

# ---------- clean + import ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SRC))

# Flatten the imported GLB hierarchy while preserving each mesh's world transform.
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

# Remove SketchUp locator/marker triangles which distort overall bounds.
for o in list(meshes):
    if len(o.data.polygons) <= 2:
        bpy.data.objects.remove(o, do_unlink=True)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']

# Remove leftover imported hierarchy nodes/cameras/lights.
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)


def bounds_of(objects):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objects:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
    return mn, mx

mn, mx = bounds_of(meshes)
dims = mx - mn
if dims.y < dims.x:
    # Defensive path for a future Warehouse conversion with length along X.
    R = Matrix.Rotation(math.radians(90), 4, 'Z')
    for o in meshes:
        o.matrix_world = R @ o.matrix_world
    mn, mx = bounds_of(meshes)
    dims = mx - mn

# Warehouse model is a little over 5 m long. Normalize to a Kodiaq-sized 4.70 m.
TARGET_LENGTH = 4.70
scale = TARGET_LENGTH / dims.y
center = (mn + mx) * 0.5
# The source's front is at its minimum Y after Blender GLB import. GTA convention
# in our proven resource uses +Y as front, so rotate 180 degrees around Z.
M = Matrix.Scale(scale, 4) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Translation((-center.x, -center.y, -mn.z))
for o in meshes:
    o.matrix_world = M @ o.matrix_world

# Apply transforms so Sollumz receives deterministic local coordinates.
for o in meshes:
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Reduce only the four extremely dense custom wheel meshes. Each was ~25k tris
# and ~75k imported vertices, which is needlessly risky for GTA drawable limits.
for o in meshes:
    polys = len(o.data.polygons)
    mats = {m.name for m in o.data.materials if m}
    if '*30' in mats and polys > 15000:
        mod = o.modifiers.new('GTA_safe_decimate', 'DECIMATE')
        mod.ratio = 0.46
        mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    elif polys > 30000:
        mod = o.modifiers.new('GTA_safe_decimate', 'DECIMATE')
        mod.ratio = 0.72
        mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)

# ---------- identify the four real Warehouse wheel assemblies ----------
def obj_center(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return sum(pts, Vector()) / len(pts)

primary = []
for o in meshes:
    mats = {m.name for m in o.data.materials if m}
    if '*30' in mats and len(o.data.polygons) > 5000:
        primary.append(o)
if len(primary) != 4:
    raise RuntimeError(f'Expected four primary Warehouse wheel meshes, got {len(primary)}')

wheel_positions = {}
primary_bones = {}
for o in primary:
    c = obj_center(o)
    side = 'l' if c.x < 0 else 'r'
    axle = 'f' if c.y > 0 else 'r'
    bone = f'wheel_{side}{axle}'
    primary_bones[o.name] = bone
    wheel_positions[bone] = [float(c.x), float(c.y), float(c.z)]

required = {'wheel_lf','wheel_rf','wheel_lr','wheel_rr'}
if set(wheel_positions) != required:
    raise RuntimeError(f'Wheel classification failed: {wheel_positions}')

# Assign every nearby brake/tyre/rim submesh to its wheel bone by spatial proximity.
# Body panels have centres far away and remain chassis geometry.
wheel_centres = {k: Vector(v) for k,v in wheel_positions.items()}
wheel_members = {k: [] for k in required}
for o in meshes:
    c = obj_center(o)
    bone, dist = min(((b, (c-wc).length) for b,wc in wheel_centres.items()), key=lambda x:x[1])
    if dist < 0.58:
        old = o.name
        o.name = f'{bone}__{old}'
        wheel_members[bone].append(o.name)

(ROOT/'build_output'/'warehouse_wheels.json').write_text(json.dumps({
    'positions': wheel_positions,
    'members': wheel_members,
    'source': '3D Warehouse 4c686761-b184-4128-9ad1-653a5e05424e'
}, indent=2), encoding='utf-8')

# ---------- custom Celní správa geometry ----------
def mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1.0)
    return m

CS_BLUE = mat('CS_BLUE', (0.0, 0.27, 0.78))
CS_BLUE_DARK = mat('CS_BLUE_DARK', (0.0, 0.07, 0.33))
TRIM_BLACK = mat('TRIM_BLACK', (0.01, 0.015, 0.02))
LIGHT_RED = mat('LIGHT_RED', (1.0, 0.01, 0.015))
LIGHT_BLUE = mat('LIGHT_BLUE', (0.0, 0.18, 1.0))
SIGN_AMBER = mat('SIGN_AMBER', (1.0, 0.35, 0.01))
BODY_WHITE = mat('BODY_WHITE', (0.94, 0.96, 0.98))

added = []
def cube(name, loc, size, material, bevel=0.0, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = o.modifiers.new('soft_edges','BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(material)
    added.append(o)
    return o

def text_mesh(name, text, loc, size, material, rot=(0,0,0), extrude=0.003):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.body = text
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    o.data.size = size
    o.data.extrude = extrude
    o.data.bevel_depth = 0.001
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.object
    o.data.materials.append(material)
    added.append(o)
    return o

# Body width is ~2.05 m including mirrors after normalization. Decals sit just
# inside the mirror envelope, intersecting body very slightly to avoid floating.
side_x = 0.985
for sx in (-1, 1):
    cube(f'cs_side_bar_{sx}', (sx*side_x, 0.0, 0.91), (0.018, 2.95, 0.12), CS_BLUE, 0.004)
    for i, y in enumerate((-1.22,-0.88,-0.54,-0.20,0.14,0.48,0.82,1.16)):
        o = cube(f'cs_side_chevron_{sx}_{i}', (sx*(side_x+0.004), y, 0.92), (0.020,0.23,0.34), CS_BLUE if i%2==0 else CS_BLUE_DARK, 0.002)
        o.rotation_euler[0] = math.radians(28)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    if sx > 0:
        rot=(math.radians(90),0,math.radians(90))
        x=side_x+0.012
    else:
        rot=(math.radians(90),0,math.radians(-90))
        x=-(side_x+0.012)
    text_mesh(f'cs_side_text_{sx}', 'CELNÍ SPRÁVA', (x, 0.02, 1.13), 0.205, TRIM_BLACK, rot=rot, extrude=0.002)

# Hood identification and blue accent. Kept compact so it follows the bonnet area
# without requiring a crash-prone custom livery shader/YTD.
text_mesh('cs_hood_text', 'CELNÍ SPRÁVA', (0, 1.55, 1.18), 0.19, TRIM_BLACK, rot=(0,0,0), extrude=0.002)
for i,x in enumerate((-0.60,-0.42,-0.24,-0.06,0.12,0.30,0.48,0.66)):
    cube(f'cs_hood_mark_{i}', (x, 1.86, 1.14), (0.12,0.42,0.018), CS_BLUE if i%2==0 else CS_BLUE_DARK, 0.002)

# Low-profile red/blue roof bar plus grille/rear modules. All coloured modules are
# real GTA extras 3/4 so the Lua controller can flash them without carcols/siren data.
roof_z = 1.72
cube('lightbar_base', (0,-0.05,roof_z), (1.30,0.18,0.045), TRIM_BLACK, 0.015)
for x in (-0.46,-0.17):
    cube(f'blue_roof_{x}', (x,-0.05,roof_z+0.055), (0.25,0.15,0.085), LIGHT_BLUE, 0.018)
for x in (0.17,0.46):
    cube(f'red_roof_{x}', (x,-0.05,roof_z+0.055), (0.25,0.15,0.085), LIGHT_RED, 0.018)
cube('blue_grille', (-0.30, 2.31, 0.76), (0.19,0.025,0.065), LIGHT_BLUE, 0.008)
cube('red_grille', (0.30, 2.31, 0.76), (0.19,0.025,0.065), LIGHT_RED, 0.008)
cube('blue_rear', (-0.30, -2.31, 0.93), (0.19,0.025,0.065), LIGHT_BLUE, 0.008)
cube('red_rear', (0.30, -2.31, 0.93), (0.19,0.025,0.065), LIGHT_RED, 0.008)

# Rear message board. Extra 1 = STOP, Extra 2 = NÁSLEDUJ MĚ.
board_y = -1.92
board_z = 1.93
cube('sign_bracket_l', (-0.42,-1.78,1.76), (0.045,0.10,0.30), TRIM_BLACK, 0.008)
cube('sign_bracket_r', (0.42,-1.78,1.76), (0.045,0.10,0.30), TRIM_BLACK, 0.008)
cube('stop_board', (0,board_y,board_z), (1.18,0.085,0.39), TRIM_BLACK, 0.018)
text_mesh('stop_text', 'STOP', (0,board_y-0.048,board_z), 0.245, SIGN_AMBER, rot=(math.radians(90),0,0), extrude=0.004)
cube('follow_board', (0,board_y,board_z), (1.18,0.085,0.39), TRIM_BLACK, 0.018)
text_mesh('follow_text_1', 'NÁSLEDUJ', (0,board_y-0.048,board_z+0.075), 0.115, SIGN_AMBER, rot=(math.radians(90),0,0), extrude=0.004)
text_mesh('follow_text_2', 'MĚ', (0,board_y-0.048,board_z-0.090), 0.155, SIGN_AMBER, rot=(math.radians(90),0,0), extrude=0.004)

# ---------- convert all visual meshes to one Sollumz Drawable ----------
all_meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in all_meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = all_meshes[0]
bpy.context.scene.create_seperate_drawables = False
bpy.context.scene.auto_create_embedded_col = False
bpy.context.scene.center_drawable_to_selection = False
res = bpy.ops.sollumz.converttodrawable()
print('WAREHOUSE converttodrawable:', res)

drawables = [o for o in bpy.context.scene.objects if getattr(o,'sollum_type',None) == SollumType.DRAWABLE]
if not drawables:
    raise RuntimeError('No Sollumz Drawable created from Warehouse model')
drawable = drawables[-1]
drawable.name = 'kodiaqcs.drawable'

bpy.ops.object.select_all(action='DESELECT')
drawable.select_set(True)
bpy.context.view_layer.objects.active = drawable
res = bpy.ops.sollumz.createfragment()
print('WAREHOUSE createfragment:', res)
frags = [o for o in bpy.context.scene.objects if getattr(o,'sollum_type',None) == SollumType.FRAGMENT]
if not frags:
    raise RuntimeError('No Fragment created')
frag = frags[-1]
frag.name = 'kodiaqcs'

# Initial skeleton. A later hardening pass expands this using the same proven
# hierarchy as the crash-free baseline while preserving these wheel positions.
bpy.context.view_layer.objects.active = frag
bpy.ops.object.mode_set(mode='EDIT')
arm = frag.data
for b in list(arm.edit_bones):
    arm.edit_bones.remove(b)
bones = {}
def add_bone(name, head, parent=None, length=0.18):
    b = arm.edit_bones.new(name)
    b.head = head
    b.tail = (head[0], head[1] + length, head[2])
    if parent:
        b.parent = bones[parent]
    bones[name] = b

add_bone('chassis',(0,0,0.55),None,0.30)
for name,pos in wheel_positions.items():
    add_bone(name,tuple(pos),'chassis',0.20)
add_bone('extra_1',(0,board_y,board_z),'chassis',0.18)
add_bone('extra_2',(0,board_y,board_z),'chassis',0.18)
add_bone('extra_3',(-0.30,-0.05,roof_z),'chassis',0.18)
add_bone('extra_4',(0.30,-0.05,roof_z),'chassis',0.18)
bpy.ops.object.mode_set(mode='OBJECT')

models = [o for o in drawable.children_recursive if getattr(o,'sollum_type',None) == SollumType.DRAWABLE_MODEL and o.type=='MESH']
print('WAREHOUSE drawable model count:', len(models))

def bone_for_model(name):
    l = name.lower()
    for b in ('wheel_lf','wheel_rf','wheel_lr','wheel_rr'):
        if b in l:
            return b
    if 'stop_' in l:
        return 'extra_1'
    if 'follow_' in l:
        return 'extra_2'
    if 'blue_' in l:
        return 'extra_3'
    if 'red_' in l:
        return 'extra_4'
    return 'chassis'

for m in models:
    bname = bone_for_model(m.name)
    # Clean imported/automatic groups and bind the entire drawable model rigidly.
    for vg in list(m.vertex_groups):
        m.vertex_groups.remove(vg)
    vg = m.vertex_groups.new(name=bname)
    vg.add(list(range(len(m.data.vertices))), 1.0, 'REPLACE')
    mod = m.modifiers.get('Armature') or m.modifiers.new('Armature','ARMATURE')
    mod.object = frag

# QA statistics before the stable physics/material passes.
stats = {
    'source_meshes': len(meshes),
    'drawable_models': len(models),
    'polygons': sum(len(m.data.polygons) for m in models),
    'vertices': sum(len(m.data.vertices) for m in models),
    'wheel_positions': wheel_positions,
}
(ROOT/'build_output'/'warehouse_build_stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print('WAREHOUSE BUILD STATS', stats)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))
print('WAREHOUSE KODIAQ BLEND READY')
