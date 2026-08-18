import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path.cwd(); OUT=ROOT/'build_output'; OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: pass
scene.render.resolution_x=1100; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.color=(0.035,0.04,0.05)

# Non-destructive QA floor and lights. This script never saves the blend.
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,0.02)); floor=bpy.context.object
fm=bpy.data.materials.new('QA_FLOOR'); fm.diffuse_color=(0.08,0.09,0.10,1); floor.data.materials.append(fm)
for loc,energy,size in [((4,5,7),1300,5.0),((-4,2,5),900,4.0),((1,-5,5),1000,4.0)]:
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=energy; l.data.shape='DISK'; l.data.size=size

bpy.ops.object.camera_add(); cam=bpy.context.object; scene.camera=cam; cam.data.lens=52

def point_camera(loc,target=(0,0,0.95)):
    cam.location=loc
    direction=Vector(target)-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

def render(name,loc):
    point_camera(loc); scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True); print('rendered',name)

render('V6_preview_front.png',(5.5,6.4,3.2))
render('V6_preview_rear.png',(-5.0,-6.0,2.9))
render('V6_preview_side.png',(6.5,0.0,2.1))
