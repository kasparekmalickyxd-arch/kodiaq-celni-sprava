import bpy
import json
from pathlib import Path

ROOT = Path.cwd()
meta = json.loads((ROOT/'build_output'/'warehouse_wheels.json').read_text(encoding='utf-8'))
wheel_positions = {k: tuple(v) for k,v in meta['positions'].items()}

frags=[o for o in bpy.context.scene.objects if o.type=='ARMATURE' and o.name=='kodiaqcs']
if not frags:
    frags=[o for o in bpy.context.scene.objects if o.type=='ARMATURE' and 'fragment' in str(getattr(o,'sollum_type','')).lower()]
if not frags:
    raise RuntimeError('Warehouse kodiaqcs fragment not found')
frag=frags[0]
arm=frag.data

bpy.context.view_layer.objects.active=frag
bpy.ops.object.mode_set(mode='EDIT')
for b in list(arm.edit_bones):
    arm.edit_bones.remove(b)

bones={}
def add_bone(name, head, parent=None, length=0.18):
    b=arm.edit_bones.new(name)
    b.head=head
    b.tail=(head[0], head[1]+length, head[2])
    b.use_connect=False
    if parent:
        b.parent=bones[parent]
    bones[name]=b

add_bone('chassis',(0,0,0),None,0.30)
add_bone('chassis_dummy',(0,0,0.55),'chassis')
add_bone('bodyshell',(0,0,0.78),'chassis')
add_bone('bonnet',(0,1.50,1.02),'chassis')
add_bone('boot',(0,-1.85,1.05),'chassis')
add_bone('windscreen',(0,0.83,1.42),'chassis')
add_bone('engine',(0,1.35,0.78),'chassis')
add_bone('exhaust',(-0.48,-2.16,0.42),'chassis')
add_bone('exhaust_2',(0.48,-2.16,0.42),'chassis')
add_bone('platelight',(0,-2.27,0.88),'chassis')
add_bone('steeringwheel',(-0.39,0.43,1.02),'chassis')

# Standard four-seat layout. Interior geometry from the Warehouse model stays
# chassis-rigid; these bones exist for GTA's vehicle seating/layout queries.
add_bone('seat_dside_f',(-0.42,0.36,0.78),'chassis')
add_bone('seat_pside_f',(0.42,0.36,0.78),'chassis')
add_bone('seat_dside_r',(-0.42,-0.61,0.78),'chassis')
add_bone('seat_pside_r',(0.42,-0.61,0.78),'chassis')
add_bone('seat_r',(0,-0.70,0.78),'chassis')

add_bone('door_dside_f',(-0.86,0.38,1.08),'chassis')
add_bone('door_pside_f',(0.86,0.38,1.08),'chassis')
add_bone('door_dside_r',(-0.86,-0.62,1.08),'chassis')
add_bone('door_pside_r',(0.86,-0.62,1.08),'chassis')
add_bone('window_lf',(-0.87,0.40,1.40),'chassis')
add_bone('window_rf',(0.87,0.40,1.40),'chassis')
add_bone('window_lr',(-0.87,-0.62,1.40),'chassis')
add_bone('window_rr',(0.87,-0.62,1.40),'chassis')

for name in ('wheel_lf','wheel_rf','wheel_lr','wheel_rr'):
    if name not in wheel_positions:
        raise RuntimeError(f'Missing dynamic wheel position {name}')
    add_bone(name,wheel_positions[name],'chassis',0.20)

add_bone('extra_1',(0,-1.92,1.93),'chassis')
add_bone('extra_2',(0,-1.92,1.93),'chassis')
add_bone('extra_3',(-0.30,-0.05,1.72),'chassis')
add_bone('extra_4',(0.30,-0.05,1.72),'chassis')

bpy.ops.object.mode_set(mode='OBJECT')

# Only chassis participates in conservative fragment physics. Wheels and extras
# remain transform bones, matching the proven crash-free baseline strategy.
for b in arm.bones:
    b.sollumz_use_physics=(b.name=='chassis')

# Keep every drawable mesh rigidly bound to an existing bone. Existing wheel and
# extra group names from the build pass are preserved.
drawables=[o for o in frag.children_recursive if 'drawable' in str(getattr(o,'sollum_type','')).lower() and o.type!='MESH']
for d in drawables:
    for obj in d.children_recursive:
        if obj.type!='MESH':
            continue
        valid=[vg for vg in obj.vertex_groups if vg.name in arm.bones]
        if not valid:
            for vg in list(obj.vertex_groups):
                obj.vertex_groups.remove(vg)
            vg=obj.vertex_groups.new(name='chassis')
            vg.add(list(range(len(obj.data.vertices))),1.0,'REPLACE')
        else:
            # remove only groups not represented by the new skeleton
            for vg in list(obj.vertex_groups):
                if vg.name not in arm.bones:
                    obj.vertex_groups.remove(vg)
        mod=obj.modifiers.get('Armature') or obj.modifiers.new('Armature','ARMATURE')
        mod.object=frag

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))
print('WAREHOUSE HARDENED SKELETON', [b.name for b in arm.bones])
print('WAREHOUSE WHEEL POSITIONS', wheel_positions)
