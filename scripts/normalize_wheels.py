import bpy
import json
import math
from pathlib import Path
from mathutils import Vector
from Sollumz.sollumz_properties import SollumType

ROOT=Path.cwd()
meta=json.loads((ROOT/'build_output'/'warehouse_wheels.json').read_text(encoding='utf-8'))
wheel_positions={k:Vector(v) for k,v in meta['positions'].items()}
required=('wheel_lf','wheel_rf','wheel_lr','wheel_rr')

frag=next((o for o in bpy.context.scene.objects if o.type=='ARMATURE' and o.name=='kodiaqcs'),None)
if frag is None:
    raise RuntimeError('kodiaqcs fragment not found')

drawable=next((o for o in frag.children_recursive if getattr(o,'sollum_type',None)==SollumType.DRAWABLE),None)
if drawable is None:
    raise RuntimeError('drawable not found')

# Remove original Warehouse wheel/rim/brake submeshes that were spatially assigned
# to wheel bones. Larger panels are kept and rebound to chassis, because some arch
# trim lies close to a wheel centre.
removed=[]
rebound=[]
for o in list(drawable.children_recursive):
    if o.type!='MESH' or getattr(o,'sollum_type',None)!=SollumType.DRAWABLE_MODEL:
        continue
    groups={vg.name for vg in o.vertex_groups}
    hits=[b for b in required if b in groups]
    if not hits:
        continue
    pts=[o.matrix_world @ Vector(c) for c in o.bound_box]
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    ext=mx-mn
    c=(mn+mx)*0.5
    b=min(hits,key=lambda n:(c-wheel_positions[n]).length)
    near=(c-wheel_positions[b]).length < 0.70
    wheel_sized=max(ext) < 0.95 and ext.z < 0.82
    if near and wheel_sized:
        removed.append(o.name)
        bpy.data.objects.remove(o,do_unlink=True)
    else:
        for vg in list(o.vertex_groups):
            o.vertex_groups.remove(vg)
        vg=o.vertex_groups.new(name='chassis')
        vg.add(list(range(len(o.data.vertices))),1.0,'REPLACE')
        rebound.append(o.name)

# Simple clean OEM-style wheel. Geometry is deliberately moderate-poly and has no
# imported transforms. Each piece is rigidly weighted to exactly one wheel bone.
MAT_TIRE=bpy.data.materials.get('TYRES_NEW') or bpy.data.materials.new('TYRES_NEW')
MAT_RIM=bpy.data.materials.get('RIM_NEW') or bpy.data.materials.new('RIM_NEW')
MAT_HUB=bpy.data.materials.get('HUB_NEW') or bpy.data.materials.new('HUB_NEW')
MAT_BRAKE=bpy.data.materials.get('BRAKE_NEW') or bpy.data.materials.new('BRAKE_NEW')
MAT_TIRE.diffuse_color=(0.015,0.018,0.022,1)
MAT_RIM.diffuse_color=(0.22,0.24,0.27,1)
MAT_HUB.diffuse_color=(0.06,0.07,0.08,1)
MAT_BRAKE.diffuse_color=(0.55,0.02,0.025,1)

created=[]
def finish(o,bone,mat):
    o.name=f'{bone}__{o.name}'
    if not o.data.materials:
        o.data.materials.append(mat)
    else:
        o.data.materials[0]=mat
    o.sollum_type=SollumType.DRAWABLE_MODEL
    o.parent=drawable
    for vg in list(o.vertex_groups):
        o.vertex_groups.remove(vg)
    vg=o.vertex_groups.new(name=bone)
    vg.add(list(range(len(o.data.vertices))),1.0,'REPLACE')
    mod=o.modifiers.get('Armature') or o.modifiers.new('Armature','ARMATURE')
    mod.object=frag
    created.append(o.name)
    return o

for bone in required:
    p=wheel_positions[bone]
    # tyre, outside radius 0.37 m, 0.22 m wide
    bpy.ops.mesh.primitive_torus_add(major_radius=0.292,minor_radius=0.078,major_segments=36,minor_segments=12,location=p,rotation=(0,math.radians(90),0))
    tire=bpy.context.object; tire.name='tire_new'; tire.scale.x=1.42
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(tire,bone,MAT_TIRE)
    # rim barrel
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=0.225,depth=0.185,location=p,rotation=(0,math.radians(90),0))
    rim=bpy.context.object; rim.name='rim_new'; finish(rim,bone,MAT_RIM)
    # dark centre hub
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=0.072,depth=0.195,location=p,rotation=(0,math.radians(90),0))
    hub=bpy.context.object; hub.name='hub_new'; finish(hub,bone,MAT_HUB)
    # red brake disc/caliper visual, slightly inboard
    sx=-1 if p.x<0 else 1
    bpy.ops.mesh.primitive_cylinder_add(vertices=28,radius=0.155,depth=0.035,location=(p.x-sx*0.045,p.y,p.z),rotation=(0,math.radians(90),0))
    brake=bpy.context.object; brake.name='brake_new'; finish(brake,bone,MAT_BRAKE)
    # five simple spokes
    for i in range(5):
        a=math.radians(i*72)
        bpy.ops.mesh.primitive_cube_add(location=(p.x+sx*0.098,p.y,p.z),rotation=(a,0,math.radians(90)))
        sp=bpy.context.object; sp.name=f'spoke_{i}'
        sp.scale=(0.025,0.018,0.175)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        finish(sp,bone,MAT_RIM)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))
(ROOT/'build_output'/'wheel_normalization.json').write_text(json.dumps({
    'removed_original_models':removed,
    'rebound_models':rebound,
    'created_models':created,
    'wheel_positions':{k:list(v) for k,v in wheel_positions.items()}
},indent=2),encoding='utf-8')
print('NORMAL WHEELS READY',{'removed':len(removed),'rebound':len(rebound),'created':len(created)})
