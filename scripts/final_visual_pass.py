import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path.cwd()

# The source Kodiaq is already converted to Sollumz at this point. This pass fixes
# the visual issues observed in FiveM without touching the proven fragment/physics
# architecture: no floating livery blocks, white body, cleaner police/customs
# graphics, correctly placed roof/rear equipment.

frags = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE' and o.name == 'kodiaqcs']
if not frags:
    raise RuntimeError('kodiaqcs fragment not found')
frag = frags[0]

models = [o for o in frag.children_recursive if o.type == 'MESH']
if not models:
    raise RuntimeError('No drawable meshes found')

# ---------- helper materials; the later warehouse_materials pass converts these
# to known-safe GTA vehicle shaders with embedded DDS textures.
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

# ---------- remove the old protruding block livery and sign brackets
remove_tokens = (
    'cs_side_bar_', 'cs_side_chevron_', 'cs_hood_mark_',
    'sign_bracket_l', 'sign_bracket_r'
)
removed = []
for o in list(models):
    low = o.name.lower()
    if any(tok in low for tok in remove_tokens):
        removed.append(o.name)
        bpy.data.objects.remove(o, do_unlink=True)

models = [o for o in frag.children_recursive if o.type == 'MESH']

# ---------- identify body shell pieces
# The Warehouse model contains a CarPaint shell plus two large Black1 layers.
# The latter were the reason the in-game vehicle looked almost entirely black.
def material_names(o):
    return {m.name for m in o.data.materials if m}

def world_dims(o):
    return Vector((abs(o.dimensions.x), abs(o.dimensions.y), abs(o.dimensions.z)))

body_models = []
paint_candidates = []
for o in models:
    names = material_names(o)
    dims = world_dims(o)
    has_paint = any('CARPAINT' in n.upper() or 'BODY_WHITE' in n.upper() for n in names)
    large_black_shell = any('BLACK1' in n.upper() for n in names) and dims.y > 4.25 and dims.z > 1.0
    if has_paint or large_black_shell:
        body_models.append(o)
        if has_paint and dims.y > 4.0:
            paint_candidates.append(o)

if not body_models:
    raise RuntimeError('Could not identify Warehouse body shell')

# Ensure safe role material slots and recolour the exterior shell white. The
# side stripe is assigned directly to body faces, so it cannot float or stick out.
for o in body_models:
    me = o.data
    # replace current slots for the body model with explicit roles
    while len(me.materials):
        me.materials.pop(index=0)
    me.materials.append(BODY_WHITE)   # 0
    me.materials.append(CS_BLUE)      # 1
    me.materials.append(CS_BLUE_DARK) # 2

    # initialize all exterior-shell faces to white
    for p in me.polygons:
        p.material_index = 0

    # Integrated blue side band. Use face centroids/normals to touch only the
    # side-facing door/body surfaces, not bonnet, roof or wheel wells.
    for p in me.polygons:
        c = o.matrix_world @ p.center
        n = (o.matrix_world.to_3x3() @ p.normal).normalized()
        side_facing = abs(n.x) > 0.42 and abs(c.x) > 0.55
        in_band = -1.52 < c.y < 1.34 and 0.72 < c.z < 1.08
        if side_facing and in_band:
            # A clean alternating darker segment pattern inside the blue strip.
            # This is face-level colouring on the body itself, not extra blocks.
            seg = int((c.y + 1.52) / 0.36)
            diagonal = (c.z - 0.72) > ((c.y + 1.52) % 0.36) * 0.55
            p.material_index = 2 if (seg % 2 == 1 and diagonal) else 1

# ---------- tuck existing text decals into the body instead of leaving them floating
# Text is tiny geometry because that is substantially safer than introducing a
# new alpha/decal shader into the already proven crash-safe build.
def mesh_center(o):
    if not o.data.vertices:
        return Vector((0,0,0))
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    return sum(pts, Vector()) / len(pts)

for o in models:
    low = o.name.lower()
    if 'cs_side_text_' in low:
        c = mesh_center(o)
        # Old decals were near |x| ~= .997. Move them onto the doors at .925.
        target_x = 0.925 if c.x > 0 else -0.925
        o.location.x += target_x - c.x
        # Keep lettering just above the blue band.
        o.location.z += 1.16 - c.z
        # use black lettering on white area
        while len(o.data.materials): o.data.materials.pop(index=0)
        o.data.materials.append(TRIM_BLACK)
    elif 'cs_hood_text' in low:
        c = mesh_center(o)
        # Lay the hood lettering close to the painted bonnet instead of hovering.
        o.location.z += 1.075 - c.z
        o.location.y += 1.42 - c.y
        while len(o.data.materials): o.data.materials.pop(index=0)
        o.data.materials.append(TRIM_BLACK)

# ---------- equipment placement
# Actual normalized model height is ~1.64 m. Old equipment was intentionally high
# for diagnostics and visibly floated in FiveM.
def move_named(tokens, delta):
    changed=[]
    for o in models:
        low=o.name.lower()
        if any(t in low for t in tokens):
            o.location += Vector(delta)
            changed.append(o.name)
    return changed

# roof bar down onto the roof
roof_changed = move_named(('lightbar_base','blue_roof_','red_roof_'), (0.0, 0.0, -0.105))

# rear sign moved from above the roof into the rear-window area
sign_changed = move_named(('stop_board','stop_text','follow_board','follow_text_'), (0.0, 0.14, -0.57))

# grille modules slightly inset into the grille; rear modules into tailgate area
for o in models:
    low=o.name.lower()
    if 'blue_grille' in low or 'red_grille' in low:
        o.location.y -= 0.025
        o.location.z += 0.02
    elif 'blue_rear' in low or 'red_rear' in low:
        o.location.y += 0.025
        o.location.z += 0.02

# Rebind every surviving/new body model to chassis if needed. Existing extras and
# wheels retain their named groups.
arm = frag.data
for o in [x for x in frag.children_recursive if x.type=='MESH']:
    valid = [vg for vg in o.vertex_groups if vg.name in arm.bones]
    if not valid:
        for vg in list(o.vertex_groups):
            o.vertex_groups.remove(vg)
        vg = o.vertex_groups.new(name='chassis')
        vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    mod = o.modifiers.get('Armature') or o.modifiers.new('Armature','ARMATURE')
    mod.object = frag

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))
print('FINAL VISUAL PASS READY', {
    'removed_old_livery_parts': len(removed),
    'body_models': len(body_models),
    'roof_parts_moved': len(roof_changed),
    'rear_sign_parts_moved': len(sign_changed),
})
