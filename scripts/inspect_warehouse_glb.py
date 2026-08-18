import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path.cwd()
SRC=ROOT/'source'/'warehouse_kodiaq.glb'
OUT=ROOT/'build_output'/'warehouse_inspect'
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.import_scene.gltf(filepath=str(SRC))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']

# collect world-space bounds
mins=Vector((1e9,1e9,1e9)); maxs=Vector((-1e9,-1e9,-1e9))
for o in meshes:
    for c in o.bound_box:
        p=o.matrix_world @ Vector(c)
        for i in range(3):
            mins[i]=min(mins[i],p[i]); maxs[i]=max(maxs[i],p[i])

dims=maxs-mins
info={
 'mesh_count':len(meshes),
 'object_count':len(bpy.context.scene.objects),
 'materials':sorted({m.name for o in meshes for m in o.data.materials if m}),
 'material_count':len({m.name for o in meshes for m in o.data.materials if m}),
 'vertices':sum(len(o.data.vertices) for o in meshes),
 'polygons':sum(len(o.data.polygons) for o in meshes),
 'bounds_min':list(mins), 'bounds_max':list(maxs), 'dimensions':list(dims),
 'objects':[]
}
for o in meshes:
    info['objects'].append({
      'name':o.name,
      'verts':len(o.data.vertices),
      'polys':len(o.data.polygons),
      'materials':[m.name if m else None for m in o.data.materials],
      'location':list(o.matrix_world.translation),
      'dimensions':list(o.dimensions)
    })

(OUT/'inspect.json').write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding='utf-8')
print('WAREHOUSE_INSPECT_SUMMARY', json.dumps({k:info[k] for k in ['mesh_count','material_count','vertices','polygons','dimensions']},ensure_ascii=False))
print('WAREHOUSE_OBJECT_NAMES', [o.name for o in meshes])
print('WAREHOUSE_MATERIALS', info['materials'])

# simple preview: normalize geometry only for camera framing, don't save modifications to source
# rotate if longest horizontal axis is X rather than Y
if dims.x > dims.y:
    for o in meshes:
        o.rotation_euler[2] += math.radians(90)
        bpy.context.view_layer.objects.active=o
        o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    for o in meshes: o.select_set(False)

# recalc bounds and scale length to 4.70m
mins=Vector((1e9,1e9,1e9)); maxs=Vector((-1e9,-1e9,-1e9))
for o in meshes:
    for c in o.bound_box:
        p=o.matrix_world @ Vector(c)
        for i in range(3): mins[i]=min(mins[i],p[i]); maxs[i]=max(maxs[i],p[i])
d=maxs-mins
scale=4.70/max(d.x,d.y)
center=(mins+maxs)/2
for o in meshes:
    o.location-=center
    o.scale*=scale
# ground after scaling
bpy.context.view_layer.update()
mins=Vector((1e9,1e9,1e9)); maxs=Vector((-1e9,-1e9,-1e9))
for o in meshes:
    for c in o.bound_box:
        p=o.matrix_world @ Vector(c)
        for i in range(3): mins[i]=min(mins[i],p[i]); maxs[i]=max(maxs[i],p[i])
for o in meshes: o.location.z -= mins.z

# camera/light/world
bpy.ops.object.light_add(type='AREA',location=(4,5,6)); key=bpy.context.object; key.data.energy=1700; key.data.shape='DISK'; key.data.size=5
bpy.ops.object.light_add(type='AREA',location=(-4,-2,4)); fill=bpy.context.object; fill.data.energy=900; fill.data.size=4
bpy.ops.object.camera_add(location=(6.6,7.2,3.9)); cam=bpy.context.object; bpy.context.scene.camera=cam

def point_at(obj, target=(0,0,0.9)):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
point_at(cam)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.world.color=(0.06,0.06,0.07)
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'preview.png')
bpy.ops.render.render(write_still=True)
print('WAREHOUSE_PREVIEW_READY', OUT/'preview.png')
