import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path.cwd()

# Final visual cleanup on top of the crash-safe Warehouse Kodiaq fragment.
frags = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE' and o.name == 'kodiaqcs']
if not frags:
    raise RuntimeError('kodiaqcs fragment not found')
frag = frags[0]
models = [o for o in frag.children_recursive if o.type == 'MESH']
if not models:
    raise RuntimeError('No drawable meshes found')

# Later warehouse_materials.py converts these simple role materials to stable GTA
# vehicle_paint1 shaders and embedded DDS textures.
def mat(name, rgb):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1.0)
    return m

BODY_WHITE = mat('BODY_WHITE', (0.96, 0.975, 0.99))
CS_BLUE = mat('CS_BLUE', (0.0, 0.30, 0.78))
CS_BLUE_DARK = mat('CS_BLUE_DARK', (0.0, 0.10, 0.38))
TRIM_BLACK = mat('TRIM_BLACK', (0.015, 0.018, 0.025))

# Delete the diagnostic blocks which visibly protruded from the car in FiveM.
remove_tokens = ('cs_side_bar_', 'cs_side_chevron_', 'cs_hood_mark_', 'sign_bracket_l', 'sign_bracket_r')
removed = []
for o in list(models):
    if any(tok in o.name.lower() for tok in remove_tokens):
        removed.append(o.name)
        bpy.data.objects.remove(o, do_unlink=True)
models = [o for o in frag.children_recursive if o.type == 'MESH']

# Detect painted shell pieces. The original Warehouse Kodiaq also contains two
# large Black1 layers that cover much of the exterior; recolouring them is what
# prevents the almost-all-black result seen in the user's screenshot.
def material_names(o):
    return {m.name for m in o.data.materials if m}

def dims(o):
    return Vector((abs(o.dimensions.x), abs(o.dimensions.y), abs(o.dimensions.z)))

body_models=[]
for o in models:
    names=material_names(o); d=dims(o)
    has_paint=any('CARPAINT' in n.upper() or 'BODY_WHITE' in n.upper() for n in names)
    large_black=any('BLACK1' in n.upper() for n in names) and d.y>4.25 and d.z>1.0
    if has_paint or large_black:
        body_models.append(o)
if not body_models:
    raise RuntimeError('Could not identify body shell')

# Real livery on body faces, not separate wedges/blocks.
blue_face_count=0
for o in body_models:
    me=o.data
    while len(me.materials): me.materials.pop(index=0)
    me.materials.append(BODY_WHITE)   # 0
    me.materials.append(CS_BLUE)      # 1
    me.materials.append(CS_BLUE_DARK) # 2
    for p in me.polygons:
        p.material_index=0
    for p in me.polygons:
        c=o.matrix_world @ p.center
        n=(o.matrix_world.to_3x3() @ p.normal).normalized()
        side=abs(n.x)>0.42 and abs(c.x)>0.55
        band=-1.52<c.y<1.34 and 0.72<c.z<1.08
        if side and band:
            seg=int((c.y+1.52)/0.36)
            diagonal=(c.z-0.72)>((c.y+1.52)%0.36)*0.55
            p.material_index=2 if (seg%2==1 and diagonal) else 1
            blue_face_count+=1

# Existing CELNÍ SPRÁVA lettering stays as very thin rigid geometry because this
# avoids introducing a new alpha/decal shader. Tuck it onto the body surface.
def mesh_center(o):
    if not o.data.vertices: return Vector((0,0,0))
    pts=[o.matrix_world @ v.co for v in o.data.vertices]
    return sum(pts,Vector())/len(pts)

text_count=0
for o in models:
    low=o.name.lower()
    if 'cs_side_text_' in low:
        c=mesh_center(o)
        target_x=0.925 if c.x>0 else -0.925
        o.location.x += target_x-c.x
        o.location.z += 1.16-c.z
        while len(o.data.materials): o.data.materials.pop(index=0)
        o.data.materials.append(TRIM_BLACK)
        text_count+=1
    elif 'cs_hood_text' in low:
        c=mesh_center(o)
        o.location.z += 1.075-c.z
        o.location.y += 1.42-c.y
        while len(o.data.materials): o.data.materials.pop(index=0)
        o.data.materials.append(TRIM_BLACK)
        text_count+=1

# Equipment: roof bar tight on roof, rear board inside rear-window area.
roof_count=sign_count=0
for o in models:
    low=o.name.lower()
    if any(t in low for t in ('lightbar_base','blue_roof_','red_roof_')):
        o.location.z -= 0.105; roof_count+=1
    if any(t in low for t in ('stop_board','stop_text','follow_board','follow_text_')):
        o.location.y += 0.14; o.location.z -= 0.57; sign_count+=1
    if 'blue_grille' in low or 'red_grille' in low:
        o.location.y -= 0.025; o.location.z += 0.02
    elif 'blue_rear' in low or 'red_rear' in low:
        o.location.y += 0.025; o.location.z += 0.02

# Ensure every surviving mesh remains bound to a valid runtime bone.
arm=frag.data
for o in [x for x in frag.children_recursive if x.type=='MESH']:
    valid=[vg for vg in o.vertex_groups if vg.name in arm.bones]
    if not valid:
        for vg in list(o.vertex_groups): o.vertex_groups.remove(vg)
        vg=o.vertex_groups.new(name='chassis')
        vg.add(list(range(len(o.data.vertices))),1.0,'REPLACE')
    mod=o.modifiers.get('Armature') or o.modifiers.new('Armature','ARMATURE')
    mod.object=frag

# Hard visual gates, so a build cannot silently regress to the diagnostic design.
if blue_face_count < 20:
    raise RuntimeError(f'Integrated blue livery too small: only {blue_face_count} body faces')
if text_count < 3:
    raise RuntimeError(f'Expected hood + both side CELNI SPRAVA text meshes, got {text_count}')
if roof_count < 5:
    raise RuntimeError(f'Roof emergency-light geometry incomplete: {roof_count}')
if sign_count < 5:
    raise RuntimeError(f'Rear message board geometry incomplete: {sign_count}')

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))
print('FINAL VISUAL PASS READY',{
 'removed_old_livery_parts':len(removed),'body_models':len(body_models),
 'integrated_blue_faces':blue_face_count,'text_meshes':text_count,
 'roof_parts_moved':roof_count,'rear_sign_parts_moved':sign_count})
