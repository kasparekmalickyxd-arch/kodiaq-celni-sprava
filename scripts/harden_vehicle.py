import bpy
from pathlib import Path

ROOT = Path.cwd()

# Find the fragment armature created by build_vehicle.py.
frags = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE' and o.name == 'kodiaqcs']
if not frags:
    frags = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE' and getattr(o, 'sollum_type', '') == 'sollumz_fragment']
if not frags:
    raise RuntimeError('kodiaqcs fragment armature not found')
frag = frags[0]
arm = frag.data

# The old procedural build only had chassis/wheels/extras and its root bone was
# rotated 90 degrees by Blender because the bone pointed along Z. GTA vehicle
# layouts expect a conventional vehicle skeleton. Rebuild the rest skeleton with
# the root aligned along Blender/GTA +Y so the exported root rotation is identity.
bpy.context.view_layer.objects.active = frag
bpy.ops.object.mode_set(mode='EDIT')
for b in list(arm.edit_bones):
    arm.edit_bones.remove(b)

bones = {}
def add_bone(name, head, parent=None, length=0.18):
    b = arm.edit_bones.new(name)
    b.head = head
    b.tail = (head[0], head[1] + length, head[2])
    b.use_connect = False
    if parent:
        b.parent = bones[parent]
    bones[name] = b
    return b

# Root + common vehicle-layout bones.
add_bone('chassis', (0.0, 0.0, 0.0), None, 0.30)
add_bone('chassis_dummy', (0.0, 0.0, 0.55), 'chassis')
add_bone('bodyshell', (0.0, 0.0, 0.75), 'chassis')
add_bone('bonnet', (0.0, 1.55, 1.10), 'chassis')
add_bone('boot', (0.0, -1.85, 1.10), 'chassis')
add_bone('windscreen', (0.0, 0.95, 1.45), 'chassis')
add_bone('engine', (0.0, 1.45, 0.80), 'chassis')
add_bone('exhaust', (-0.48, -2.18, 0.48), 'chassis')
add_bone('exhaust_2', (0.48, -2.18, 0.48), 'chassis')
add_bone('platelight', (0.0, -2.32, 0.92), 'chassis')
add_bone('steeringwheel', (-0.42, 0.58, 1.03), 'chassis')

# Seats are referenced by LAYOUT_STANDARD during vehicle creation.
add_bone('seat_dside_f', (-0.43, 0.35, 0.83), 'chassis')
add_bone('seat_pside_f', (0.43, 0.35, 0.83), 'chassis')
add_bone('seat_dside_r', (-0.43, -0.62, 0.83), 'chassis')
add_bone('seat_pside_r', (0.43, -0.62, 0.83), 'chassis')
add_bone('seat_r', (0.0, -0.72, 0.83), 'chassis')

# Door/window names commonly queried by the vehicle layout and scripts.
add_bone('door_dside_f', (-0.88, 0.38, 1.10), 'chassis')
add_bone('door_pside_f', (0.88, 0.38, 1.10), 'chassis')
add_bone('door_dside_r', (-0.88, -0.62, 1.10), 'chassis')
add_bone('door_pside_r', (0.88, -0.62, 1.10), 'chassis')
add_bone('window_lf', (-0.90, 0.40, 1.42), 'chassis')
add_bone('window_rf', (0.90, 0.40, 1.42), 'chassis')
add_bone('window_lr', (-0.90, -0.62, 1.42), 'chassis')
add_bone('window_rr', (0.90, -0.62, 1.42), 'chassis')

# Wheels at the actual model locations.
wheel_positions = {
    'wheel_lf': (-0.94, 1.43, 0.43),
    'wheel_rf': (0.94, 1.43, 0.43),
    'wheel_lr': (-0.94, -1.35, 0.43),
    'wheel_rr': (0.94, -1.35, 0.43),
}
for name, pos in wheel_positions.items():
    add_bone(name, pos, 'chassis')

# Requested rear signs and emergency modules remain proper GTA extras.
add_bone('extra_1', (0.0, -1.82, 2.01), 'chassis')  # STOP
add_bone('extra_2', (0.0, -1.82, 2.01), 'chassis')  # NASLEDUJ ME
add_bone('extra_3', (-0.30, -0.03, 1.88), 'chassis') # blue modules
add_bone('extra_4', (0.30, -0.03, 1.88), 'chassis')  # red modules

bpy.ops.object.mode_set(mode='OBJECT')

# Root is the only breakable-physics group. Other bones are ordinary vehicle
# transform bones and deliberately have no fragment physics.
for bone in arm.bones:
    bone.sollumz_use_physics = (bone.name == 'chassis')

# Make sure all existing vertex groups still reference a real bone after the
# skeleton rebuild. Static body is rooted to chassis. Wheels/extras keep their
# existing named groups from build_vehicle.py.
drawables = [o for o in frag.children_recursive if getattr(o, 'sollum_type', '') == 'sollumz_drawable']
for drawable in drawables:
    for obj in drawable.children_recursive:
        if obj.type != 'MESH':
            continue
        # Remove vertex groups whose corresponding bone no longer exists.
        for vg in list(obj.vertex_groups):
            if vg.name not in arm.bones:
                obj.vertex_groups.remove(vg)
        if len(obj.vertex_groups) == 0:
            vg = obj.vertex_groups.new(name='chassis')
            vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')

# Save the hardened source for the next CI step.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'build_output' / 'kodiaqcs.blend'))
print('HARDENED VEHICLE SKELETON:', [b.name for b in arm.bones])
