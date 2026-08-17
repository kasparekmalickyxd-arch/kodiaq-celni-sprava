import bpy
import math
import os
import shutil
from pathlib import Path
from mathutils import Vector

# ---------------- paths ----------------
ROOT = Path.cwd()
OUT = ROOT / 'build_output' / 'kodiaq_cs'
STREAM = OUT / 'stream'
DATA = OUT / 'data'
CLIENT = OUT / 'client'
for p in (STREAM, DATA, CLIENT):
    p.mkdir(parents=True, exist_ok=True)

# ---------------- Sollumz imports ----------------
try:
    from Sollumz.sollumz_properties import SollumType
    from Sollumz.ydr.shader_materials import create_shader
except Exception:
    # Blender may register the extension under a bl_ext package. Find it dynamically.
    import sys
    base = next((k.rsplit('.', 1)[0] for k in sys.modules if k.endswith('.sollumz_properties') and 'sollumz' in k.lower()), None)
    if not base:
        raise
    SollumType = __import__(base + '.sollumz_properties', fromlist=['SollumType']).SollumType
    create_shader = __import__(base + '.ydr.shader_materials', fromlist=['create_shader']).create_shader

# ---------------- clean scene ----------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.armatures):
    pass

# ---------------- materials ----------------
def shader_mat(name, rgba):
    candidates = ['default.sps', 'vehicle_generic_smallspecmap.sps', 'vehicle_mesh.sps']
    mat = None
    for shader in candidates:
        try:
            mat = create_shader(shader)
            if mat:
                break
        except Exception:
            continue
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    mat.name = name
    if mat.use_nodes:
        bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            if 'Base Color' in bsdf.inputs:
                bsdf.inputs['Base Color'].default_value = rgba
            if 'Roughness' in bsdf.inputs:
                bsdf.inputs['Roughness'].default_value = 0.32
            if name.startswith('LIGHT_'):
                if 'Emission Color' in bsdf.inputs:
                    bsdf.inputs['Emission Color'].default_value = rgba
                if 'Emission Strength' in bsdf.inputs:
                    bsdf.inputs['Emission Strength'].default_value = 6.0
    return mat

WHITE = shader_mat('BODY_WHITE', (0.93,0.95,0.97,1))
BLUE = shader_mat('CS_BLUE', (0.02,0.19,0.75,1))
BLUE2 = shader_mat('CS_BLUE_DARK', (0.0,0.06,0.35,1))
BLACK = shader_mat('TRIM_BLACK', (0.01,0.012,0.018,1))
GLASS = shader_mat('GLASS_DARK', (0.02,0.04,0.07,1))
SILVER = shader_mat('METAL', (0.25,0.28,0.32,1))
RED = shader_mat('LIGHT_RED', (1.0,0.01,0.015,1))
LBLUE = shader_mat('LIGHT_BLUE', (0.0,0.2,1.0,1))
AMBER = shader_mat('SIGN_AMBER', (1.0,0.33,0.01,1))

objects=[]

def apply_mat(o, m):
    if o.type == 'MESH':
        o.data.materials.append(m)
    return o

def cube(name, loc, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object
    o.name=name
    o.scale=(scale[0]/2,scale[1]/2,scale[2]/2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=o.modifiers.new('soft_edges','BEVEL'); mod.width=bevel; mod.segments=2
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    apply_mat(o,mat); objects.append(o); return o

def cyl(name, loc, radius, depth, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; apply_mat(o,mat); objects.append(o); return o

def text_mesh(name, text, loc, size, mat, rot=(0,0,0), extrude=0.005, align='CENTER'):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o=bpy.context.object; o.name=name
    o.data.body=text; o.data.align_x=align; o.data.align_y='CENTER'; o.data.size=size; o.data.extrude=extrude
    bpy.ops.object.convert(target='MESH')
    apply_mat(o,mat); objects.append(o); return o

# ---------------- original low-poly Kodiaq-like body ----------------
# Main body envelope ~ 4.76 x 1.86 x 1.67m
cube('body_lower',(0,0,0.72),(1.82,4.50,0.66),WHITE,0.16)
cube('body_mid',(0,-0.05,1.10),(1.76,3.90,0.55),WHITE,0.16)
cube('cabin',(0,-0.28,1.45),(1.58,2.85,0.55),WHITE,0.13)
# sloped bonnet / roof details
hood=cube('hood',(0,1.55,1.13),(1.70,1.15,0.18),WHITE,0.06)
roof=cube('roof',(0,-0.35,1.73),(1.48,2.05,0.10),WHITE,0.04)
# bumpers/grille
cube('front_bumper',(0,2.27,0.56),(1.78,0.22,0.32),BLACK,0.04)
cube('rear_bumper',(0,-2.27,0.58),(1.76,0.22,0.28),BLACK,0.04)
cube('front_grille',(0,2.39,0.86),(1.15,0.04,0.48),BLACK,0)
for x in [-0.42,-0.30,-0.18,-0.06,0.06,0.18,0.30,0.42]:
    cube('grille_slat',(x,2.415,0.86),(0.018,0.018,0.38),SILVER,0)
# windows
cube('windshield',(0,1.00,1.45),(1.46,0.06,0.48),GLASS,0.02)
cube('rear_window',(0,-1.76,1.45),(1.42,0.05,0.44),GLASS,0.02)
for sx in (-1,1):
    cube(f'window_front_{sx}',(sx*0.895,0.38,1.43),(0.035,0.88,0.40),GLASS,0.01)
    cube(f'window_rear_{sx}',(sx*0.895,-0.62,1.43),(0.035,0.90,0.40),GLASS,0.01)
    cube(f'mirror_{sx}',(sx*1.00,0.83,1.26),(0.20,0.30,0.12),BLACK,0.04)
# headlights/tails
for sx in (-1,1):
    cube(f'headlight_{sx}',(sx*0.62,2.405,1.06),(0.45,0.035,0.10),SILVER,0.015)
    cube(f'taillight_{sx}',(sx*0.59,-2.405,1.05),(0.42,0.035,0.11),RED,0.015)
# roof rails
for sx in (-1,1): cube(f'roofrail_{sx}',(sx*0.63,-0.35,1.82),(0.04,2.15,0.05),BLACK,0.015)

# wheels - proper standard bone names
wheel_positions={'wheel_lf':(-0.94,1.43,0.43),'wheel_rf':(0.94,1.43,0.43),'wheel_lr':(-0.94,-1.35,0.43),'wheel_rr':(0.94,-1.35,0.43)}
for name,(x,y,z) in wheel_positions.items():
    cyl(name,(x,y,z),0.39,0.25,BLACK,rot=(0,math.radians(90),0))
    cyl(name+'_rim',(x,y,z),0.25,0.265,SILVER,rot=(0,math.radians(90),0))

# ---------------- Celní správa livery as real geometry ----------------
# side blue bar and diagonal blocks
for sx in (-1,1):
    cube(f'livery_bar_{sx}',(sx*0.916,-0.10,0.99),(0.018,3.05,0.16),BLUE,0.0)
    for i,y in enumerate([1.25,0.92,0.59,0.26,-0.07,-0.40,-0.73,-1.06]):
        o=cube(f'livery_diag_{sx}_{i}',(sx*0.922,y,1.03),(0.020,0.20,0.42),BLUE if i%2==0 else BLUE2,0)
        o.rotation_euler[0]=math.radians(25)
        bpy.context.view_layer.objects.active=o; bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
    # side text, rotated onto side plane
    if sx>0:
        rot=(math.radians(90),0,math.radians(90))
        loc=(0.931,-0.17,1.25)
    else:
        rot=(math.radians(90),0,math.radians(-90))
        loc=(-0.931,-0.17,1.25)
    text_mesh(f'cs_text_side_{sx}','CELNÍ SPRÁVA',loc,0.22,BLACK,rot=rot,extrude=0.004)

# hood markings
for i,x in enumerate([-0.64,-0.45,-0.26,-0.07,0.12,0.31,0.50,0.69]):
    cube(f'hood_blue_{i}',(x,1.88,1.235),(0.13,0.45,0.018),BLUE if i%2==0 else BLUE2,0)
text_mesh('cs_text_hood','CELNÍ SPRÁVA',(0,1.45,1.235),0.20,BLACK,rot=(0,0,0),extrude=0.004)

# ---------------- red/blue emergency modules as toggleable extras ----------------
# extra_3 = blue group, extra_4 = red group
blue_modules=[]; red_modules=[]
for x in (-0.45,-0.15): blue_modules.append(cube('blue_light_module',(x,-0.03,1.88),(0.24,0.14,0.10),LBLUE,0.02))
for x in (0.15,0.45): red_modules.append(cube('red_light_module',(x,-0.03,1.88),(0.24,0.14,0.10),RED,0.02))
blue_modules += [cube('blue_grille',(-0.27,2.42,0.86),(0.18,0.025,0.07),LBLUE,0.01), cube('blue_rear',(-0.28,-2.42,0.78),(0.18,0.025,0.07),LBLUE,0.01)]
red_modules += [cube('red_grille',(0.27,2.42,0.86),(0.18,0.025,0.07),RED,0.01), cube('red_rear',(0.28,-2.42,0.78),(0.18,0.025,0.07),RED,0.01)]

# ---------------- rear LED message board extras ----------------
# both boards overlap; Lua ensures only one is active
stop_board=cube('stop_board',(0,-1.82,2.01),(1.24,0.10,0.42),BLACK,0.02)
stop_text=text_mesh('stop_text','STOP',(0,-1.875,2.01),0.25,AMBER,rot=(math.radians(90),0,0),extrude=0.006)
follow_board=cube('follow_board',(0,-1.82,2.01),(1.24,0.10,0.42),BLACK,0.02)
follow1=text_mesh('follow_text_1','NÁSLEDUJ',(0,-1.875,2.08),0.13,AMBER,rot=(math.radians(90),0,0),extrude=0.006)
follow2=text_mesh('follow_text_2','MĚ',(0,-1.875,1.92),0.17,AMBER,rot=(math.radians(90),0,0),extrude=0.006)
# brackets
cube('sign_bracket_l',(-0.45,-1.68,1.82),(0.05,0.10,0.28),BLACK,0.01)
cube('sign_bracket_r',(0.45,-1.68,1.82),(0.05,0.10,0.28),BLACK,0.01)

# ---------------- convert geometry to single Sollumz Drawable ----------------
bpy.ops.object.select_all(action='DESELECT')
for o in objects: o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.context.scene.create_seperate_drawables=False
bpy.context.scene.auto_create_embedded_col=False
bpy.context.scene.center_drawable_to_selection=False
res=bpy.ops.sollumz.converttodrawable()
print('converttodrawable:',res)

drawables=[o for o in bpy.context.scene.objects if getattr(o,'sollum_type',None)==SollumType.DRAWABLE]
if not drawables: raise RuntimeError('No Sollumz Drawable created')
drawable=drawables[-1]; drawable.name='kodiaqcs.drawable'

# ---------------- create Fragment / armature ----------------
bpy.ops.object.select_all(action='DESELECT')
drawable.select_set(True); bpy.context.view_layer.objects.active=drawable
res=bpy.ops.sollumz.createfragment(); print('createfragment:',res)
frags=[o for o in bpy.context.scene.objects if getattr(o,'sollum_type',None)==SollumType.FRAGMENT]
if not frags: raise RuntimeError('No Fragment created')
frag=frags[-1]; frag.name='kodiaqcs'

# ---------------- skeleton ----------------
bpy.context.view_layer.objects.active=frag
bpy.ops.object.mode_set(mode='EDIT')
arm=frag.data
bones={}
def add_bone(name, head, tail, parent=None):
    b=arm.edit_bones.new(name); b.head=head; b.tail=tail
    if parent: b.parent=bones[parent]
    bones[name]=b
add_bone('chassis',(0,0,0.55),(0,0,0.75))
for n,p in wheel_positions.items(): add_bone(n,p,(p[0],p[1],p[2]+0.20),'chassis')
for i in range(1,5): add_bone(f'extra_{i}',(0,-1.8,1.8),(0,-1.8,2.0),'chassis')
bpy.ops.object.mode_set(mode='OBJECT')

# map Drawable Models to bones by original names
models=[o for o in drawable.children_recursive if getattr(o,'sollum_type',None)==SollumType.DRAWABLE_MODEL and o.type=='MESH']
print('Drawable models:',[o.name for o in models])

def bone_for_model(name):
    lname=name.lower()
    for n in wheel_positions:
        if lname.startswith(n): return n
    if 'stop_' in lname: return 'extra_1'
    if 'follow_' in lname: return 'extra_2'
    if 'blue_' in lname: return 'extra_3'
    if 'red_' in lname: return 'extra_4'
    return 'chassis'

for m in models:
    bname=bone_for_model(m.name)
    vg=m.vertex_groups.get(bname) or m.vertex_groups.new(name=bname)
    vg.add(list(range(len(m.data.vertices))),1.0,'REPLACE')
    mod=m.modifiers.new('Armature','ARMATURE'); mod.object=frag

# ---------------- create simple embedded collision ----------------
# Try using Sollumz's automatic embedded collision conversion on a duplicate of body envelope.
try:
    bpy.ops.object.select_all(action='DESELECT')
    # collision helper may not be available headlessly; non-fatal if it fails
    body_model=next((m for m in models if m.name.lower().startswith('body_lower')),None)
    if body_model:
        body_model.select_set(True); bpy.context.view_layer.objects.active=body_model
        bpy.context.scene.create_seperate_drawables=True
except Exception as e:
    print('Collision setup note:',e)

# ---------------- texture dictionary ----------------
# Create a tiny neutral texture so the resource includes a real YTD.
img=bpy.data.images.new('kodiaqcs_livery',width=64,height=64,alpha=True)
pixels=[0.95,0.95,0.95,1.0]*(64*64)
img.pixels= pixels
img.pack()
try:
    bpy.ops.sollumz.txd_create()
    txds=bpy.context.scene.sz_txds.texture_dictionaries
    txd=txds[-1]
    txd.name='kodiaqcs'
    txd.new_texture(img)
except Exception as e:
    print('TXD creation failed:',e)

# ---------------- save project ----------------
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'build_output'/'kodiaqcs.blend'))

# ---------------- export native ----------------
# Direct native YFT/YTD export through PyMateria on Windows.
export_res=bpy.ops.sollumz.export_assets(
    directory=str(STREAM),
    direct_export=True,
    use_custom_settings=True,
    target_formats={'NATIVE'},
    target_versions={'GEN8'},
)
print('native export result:',export_res)

# Also export CWXML for diagnostics/recovery.
xml_dir=ROOT/'build_output'/'cwxml'; xml_dir.mkdir(parents=True,exist_ok=True)
try:
    bpy.ops.sollumz.export_assets(
        directory=str(xml_dir), direct_export=True, use_custom_settings=True,
        target_formats={'CWXML'}, target_versions={'GEN8'})
except Exception as e:
    print('CWXML export note:',e)

# normalize nested Gen8 output if Sollumz emitted one
for sub in [STREAM/'gen8',STREAM/'legacy']:
    if sub.exists():
        for f in sub.iterdir():
            if f.is_file(): shutil.copy2(f,STREAM/f.name)

# Some exports may name the YTD from the texture dictionary exactly as intended.
# Ensure high-detail YFT exists for FiveM by duplicating the generated native YFT when no separate hi LOD was emitted.
yft=STREAM/'kodiaqcs.yft'
if yft.exists() and not (STREAM/'kodiaqcs_hi.yft').exists():
    shutil.copy2(yft,STREAM/'kodiaqcs_hi.yft')

# ---------------- FiveM resource files ----------------
(OUT/'fxmanifest.lua').write_text("""fx_version 'cerulean'\ngame 'gta5'\n\nauthor 'Custom Kodiaq CS build'\nversion '1.0.0'\n\nfiles {\n 'data/vehicles.meta',\n 'data/handling.meta',\n 'data/carvariations.meta',\n 'data/carcols.meta'\n}\n\ndata_file 'VEHICLE_METADATA_FILE' 'data/vehicles.meta'\ndata_file 'HANDLING_FILE' 'data/handling.meta'\ndata_file 'VEHICLE_VARIATION_FILE' 'data/carvariations.meta'\ndata_file 'CARCOLS_FILE' 'data/carcols.meta'\n\nclient_script 'client/controls.lua'\n""",encoding='utf-8')

(DATA/'handling.meta').write_text("""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<CHandlingDataMgr><HandlingData><Item type=\"CHandlingData\">\n<handlingName>KODIAQCS</handlingName><fMass value=\"2050.000000\"/><fInitialDragCoeff value=\"8.000000\"/><fPercentSubmerged value=\"85.000000\"/>\n<vecCentreOfMassOffset x=\"0.000000\" y=\"-0.050000\" z=\"-0.100000\"/><vecInertiaMultiplier x=\"1.100000\" y=\"1.350000\" z=\"1.500000\"/>\n<fDriveBiasFront value=\"0.500000\"/><nInitialDriveGears value=\"7\"/><fInitialDriveForce value=\"0.335000\"/><fDriveInertia value=\"1.050000\"/>\n<fClutchChangeRateScaleUpShift value=\"2.400000\"/><fClutchChangeRateScaleDownShift value=\"2.100000\"/><fInitialDriveMaxFlatVel value=\"231.000000\"/>\n<fBrakeForce value=\"0.950000\"/><fBrakeBiasFront value=\"0.610000\"/><fHandBrakeForce value=\"0.650000\"/><fSteeringLock value=\"36.000000\"/>\n<fTractionCurveMax value=\"2.650000\"/><fTractionCurveMin value=\"2.350000\"/><fTractionCurveLateral value=\"22.500000\"/><fLowSpeedTractionLossMult value=\"0.900000\"/>\n<fTractionBiasFront value=\"0.500000\"/><fTractionLossMult value=\"0.850000\"/><fSuspensionForce value=\"2.350000\"/><fSuspensionCompDamp value=\"1.550000\"/><fSuspensionReboundDamp value=\"2.250000\"/>\n<fSuspensionUpperLimit value=\"0.090000\"/><fSuspensionLowerLimit value=\"-0.120000\"/><fSuspensionBiasFront value=\"0.515000\"/><fAntiRollBarForce value=\"0.850000\"/><fAntiRollBarBiasFront value=\"0.545000\"/>\n<fCollisionDamageMult value=\"0.700000\"/><fWeaponDamageMult value=\"1.000000\"/><fDeformationDamageMult value=\"0.600000\"/><fEngineDamageMult value=\"1.000000\"/>\n<fPetrolTankVolume value=\"58.000000\"/><fOilVolume value=\"5.500000\"/><nMonetaryValue value=\"80000\"/><strModelFlags>440010</strModelFlags><strHandlingFlags>0</strHandlingFlags><strDamageFlags>0</strDamageFlags><AIHandling>AVERAGE</AIHandling>\n</Item></HandlingData></CHandlingDataMgr>\n""",encoding='utf-8')

(DATA/'vehicles.meta').write_text("""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<CVehicleModelInfo__InitDataList><residentTxd>vehshare</residentTxd><residentAnims/><InitDatas><Item>\n<modelName>kodiaqcs</modelName><txdName>kodiaqcs</txdName><handlingId>KODIAQCS</handlingId><gameName>KODIAQCS</gameName><vehicleMakeName>SKODA</vehicleMakeName>\n<expressionDictName>null</expressionDictName><expressionName>null</expressionName><animConvRoofDictName>null</animConvRoofDictName><animConvRoofName>null</animConvRoofName><animConvRoofWindowsAffected/>\n<ptfxAssetName>null</ptfxAssetName><audioNameHash>POLICE</audioNameHash><layout>LAYOUT_STANDARD</layout><coverBoundOffsets>LANDSTALKER_COVER_OFFSET_INFO</coverBoundOffsets><explosionInfo>EXPLOSION_INFO_DEFAULT</explosionInfo><scenarioLayout/>\n<cameraName>FOLLOW_SUV_CAMERA</cameraName><aimCameraName>BOX_VEHICLE_AIM_CAMERA</aimCameraName><bonnetCameraName>VEHICLE_BONNET_CAMERA_STANDARD_LONG</bonnetCameraName><povCameraName>FOLLOW_SUV_CAMERA</povCameraName>\n<vfxInfoName>VFXVEHICLEINFO_CAR_GENERIC</vfxInfoName><shouldUseCinematicViewMode value=\"true\"/><AllowPretendOccupants value=\"true\"/><AllowJoyriding value=\"true\"/><AllowSundayDriving value=\"true\"/><AllowBodyColorMapping value=\"true\"/>\n<wheelScale value=\"0.39\"/><wheelScaleRear value=\"0.39\"/><dirtLevelMin value=\"0.0\"/><dirtLevelMax value=\"0.45\"/><envEffScaleMin value=\"0.0\"/><envEffScaleMax value=\"1.0\"/><damageMapScale value=\"1.0\"/><damageOffsetScale value=\"1.0\"/><diffuseTint value=\"0x00FFFFFF\"/>\n<steerWheelMult value=\"1.0\"/><HDTextureDist value=\"5.0\"/><lodDistances content=\"float_array\">20.0 45.0 90.0 180.0 500.0 500.0</lodDistances><minSeatHeight value=\"0.78\"/><identicalModelSpawnDistance value=\"20\"/><maxNumOfSameColor value=\"10\"/><defaultBodyHealth value=\"1000.0\"/>\n<frequency value=\"100\"/><swankness>SWANKNESS_4</swankness><maxNum value=\"10\"/><flags>FLAG_EXTRAS_REQUIRE FLAG_LAW_ENFORCEMENT</flags><type>VEHICLE_TYPE_CAR</type><plateType>VPT_FRONT_AND_BACK_PLATES</plateType><dashboardType>VDT_RACE</dashboardType><vehicleClass>VC_EMERGENCY</vehicleClass><wheelType>VWT_SPORT</wheelType>\n<trailers/><additionalTrailers/><drivers/><extraIncludes/><doorsWithCollisionWhenClosed/><driveableDoors/><rewards/><cinematicPartCamera/><NmBraceOverrideSet/>\n</Item></InitDatas><txdRelationships/></CVehicleModelInfo__InitDataList>\n""",encoding='utf-8')

(DATA/'carvariations.meta').write_text("""<?xml version=\"1.0\" encoding=\"UTF-8\"?><CVehicleModelInfoVariation><variationData><Item><modelName>kodiaqcs</modelName><colors><Item><indices content=\"char_array\">111 111 111 111 111 111</indices><liveries/></Item></colors><kits><Item>0_default_modkit</Item></kits><windowsWithExposedEdges/><plateProbabilities><Probabilities><Item><Name>Police guv plate</Name><Value value=\"100\"/></Item></Probabilities></plateProbabilities><lightSettings value=\"1\"/><sirenSettings value=\"1\"/></Item></variationData></CVehicleModelInfoVariation>""",encoding='utf-8')
(DATA/'carcols.meta').write_text("""<?xml version=\"1.0\" encoding=\"UTF-8\"?><CVehicleModelInfoVarGlobal><Kits><Item><kitName>0_default_modkit</kitName><id value=\"0\"/><kitType>MKT_STANDARD</kitType><visibleMods/><linkMods/><statMods/><slotNames/><liveryNames/></Item></Kits><Lights/></CVehicleModelInfoVarGlobal>""",encoding='utf-8')

(CLIENT/'controls.lua').write_text(r"""local model=GetHashKey('kodiaqcs')
local flashing=false
local function veh()
 local p=PlayerPedId(); if IsPedInAnyVehicle(p,false) then local v=GetVehiclePedIsIn(p,false); if GetEntityModel(v)==model then return v end end; return 0
end
local function ex(v,n,on) if DoesExtraExist(v,n) then SetVehicleExtra(v,n,not on) end end
RegisterCommand('csstop',function() local v=veh(); if v==0 then return end ex(v,2,false); ex(v,1,true) end,false)
RegisterCommand('csfollow',function() local v=veh(); if v==0 then return end ex(v,1,false); ex(v,2,true) end,false)
RegisterCommand('cssignoff',function() local v=veh(); if v==0 then return end ex(v,1,false); ex(v,2,false) end,false)
RegisterCommand('cslights',function() local v=veh(); if v==0 then return end flashing=not flashing; if not flashing then ex(v,3,false); ex(v,4,false); SetVehicleSiren(v,false) else SetVehicleSiren(v,true); SetVehicleHasMutedSirens(v,true) end end,false)
RegisterCommand('cssiren',function() local v=veh(); if v==0 then return end if not IsVehicleSirenOn(v) then SetVehicleSiren(v,true) end SetVehicleHasMutedSirens(v,IsVehicleSirenAudioOn(v)) end,false)
CreateThread(function() local phase=false while true do Wait(180) if flashing then local v=veh(); if v~=0 then phase=not phase; ex(v,3,phase); ex(v,4,not phase) end end end end)
RegisterKeyMapping('cslights','Celní správa: majáky','keyboard','J')
RegisterKeyMapping('cssiren','Celní správa: siréna','keyboard','K')
RegisterKeyMapping('csstop','Celní správa: STOP','keyboard','NUMPAD1')
RegisterKeyMapping('csfollow','Celní správa: NÁSLEDUJ MĚ','keyboard','NUMPAD2')
RegisterKeyMapping('cssignoff','Celní správa: tabule vypnout','keyboard','NUMPAD3')
""",encoding='utf-8')

print('STREAM OUTPUT:', [p.name for p in STREAM.iterdir()])
print('BUILD COMPLETE')
