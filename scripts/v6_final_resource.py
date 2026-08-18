from pathlib import Path

ROOT=Path.cwd(); OUT=ROOT/'build_output'/'kodiaq_cs'; DATA=OUT/'data'; CLIENT=OUT/'client'; STREAM=OUT/'stream'
for p in (DATA,CLIENT,STREAM): p.mkdir(parents=True,exist_ok=True)

(OUT/'fxmanifest.lua').write_text("""fx_version 'cerulean'
game 'gta5'

author 'Kodiaq CS Final'
description 'Skoda Kodiaq RS Celni sprava - Warehouse visual base, crash-safe FiveM fragment path'
version '7.0.0'

files {
 'data/vehicles.meta',
 'data/handling.meta'
}

data_file 'VEHICLE_METADATA_FILE' 'data/vehicles.meta'
data_file 'HANDLING_FILE' 'data/handling.meta'

client_script 'client/controls.lua'
""",encoding='utf-8')

(DATA/'vehicles.meta').write_text("""<?xml version="1.0" encoding="UTF-8"?>
<CVehicleModelInfo__InitDataList>
 <residentTxd>vehshare</residentTxd><residentAnims/>
 <InitDatas><Item>
  <modelName>kodiaqcs</modelName><txdName>vehshare</txdName><handlingId>KODIAQCS</handlingId>
  <gameName>KODIAQCS</gameName><vehicleMakeName>SKODA</vehicleMakeName>
  <expressionDictName>null</expressionDictName><expressionName>null</expressionName>
  <animConvRoofDictName>null</animConvRoofDictName><animConvRoofName>null</animConvRoofName><animConvRoofWindowsAffected/>
  <ptfxAssetName>null</ptfxAssetName><audioNameHash>POLICE</audioNameHash>
  <layout>LAYOUT_STANDARD</layout><coverBoundOffsets>LANDSTALKER_COVER_OFFSET_INFO</coverBoundOffsets>
  <explosionInfo>EXPLOSION_INFO_DEFAULT</explosionInfo><scenarioLayout/>
  <cameraName>FOLLOW_SUV_CAMERA</cameraName><aimCameraName>BOX_VEHICLE_AIM_CAMERA</aimCameraName>
  <bonnetCameraName>VEHICLE_BONNET_CAMERA_STANDARD_LONG</bonnetCameraName><povCameraName>FOLLOW_SUV_CAMERA</povCameraName>
  <vfxInfoName>VFXVEHICLEINFO_CAR_GENERIC</vfxInfoName><shouldUseCinematicViewMode value="true"/>
  <AllowPretendOccupants value="true"/><AllowJoyriding value="true"/><AllowSundayDriving value="true"/><AllowBodyColorMapping value="false"/>
  <wheelScale value="0.390000"/><wheelScaleRear value="0.390000"/>
  <dirtLevelMin value="0.000000"/><dirtLevelMax value="0.150000"/>
  <envEffScaleMin value="0.000000"/><envEffScaleMax value="1.000000"/>
  <damageMapScale value="1.000000"/><damageOffsetScale value="1.000000"/><diffuseTint value="0x00FFFFFF"/>
  <steerWheelMult value="1.000000"/><HDTextureDist value="5.000000"/>
  <lodDistances content="float_array">35.0 70.0 140.0 280.0 500.0 500.0</lodDistances>
  <minSeatHeight value="0.780000"/><identicalModelSpawnDistance value="20"/><maxNumOfSameColor value="10"/>
  <defaultBodyHealth value="1000.000000"/><frequency value="100"/><swankness>SWANKNESS_4</swankness><maxNum value="10"/>
  <flags>FLAG_LAW_ENFORCEMENT</flags><type>VEHICLE_TYPE_CAR</type><plateType>VPT_FRONT_AND_BACK_PLATES</plateType>
  <dashboardType>VDT_RACE</dashboardType><vehicleClass>VC_EMERGENCY</vehicleClass><wheelType>VWT_SUV</wheelType>
  <trailers/><additionalTrailers/><drivers/><extraIncludes/><doorsWithCollisionWhenClosed/><driveableDoors/>
  <rewards/><cinematicPartCamera/><NmBraceOverrideSet/>
 </Item></InitDatas><txdRelationships/>
</CVehicleModelInfo__InitDataList>
""",encoding='utf-8')

(DATA/'handling.meta').write_text("""<?xml version="1.0" encoding="UTF-8"?>
<CHandlingDataMgr><HandlingData><Item type="CHandlingData">
 <handlingName>KODIAQCS</handlingName><fMass value="2050.000000"/><fInitialDragCoeff value="7.100000"/><fPercentSubmerged value="85.000000"/>
 <vecCentreOfMassOffset x="0.000000" y="0.015000" z="-0.115000"/><vecInertiaMultiplier x="1.100000" y="1.260000" z="1.620000"/>
 <fDriveBiasFront value="0.550000"/><nInitialDriveGears value="7"/><fInitialDriveForce value="0.335000"/><fDriveInertia value="1.050000"/>
 <fClutchChangeRateScaleUpShift value="3.000000"/><fClutchChangeRateScaleDownShift value="3.000000"/><fInitialDriveMaxFlatVel value="205.000000"/>
 <fBrakeForce value="0.880000"/><fBrakeBiasFront value="0.590000"/><fHandBrakeForce value="0.650000"/><fSteeringLock value="37.000000"/>
 <fTractionCurveMax value="2.650000"/><fTractionCurveMin value="2.350000"/><fTractionCurveLateral value="22.500000"/>
 <fTractionSpringDeltaMax value="0.130000"/><fLowSpeedTractionLossMult value="0.450000"/><fCamberStiffnesss value="0.000000"/>
 <fTractionBiasFront value="0.500000"/><fTractionLossMult value="0.900000"/>
 <fSuspensionForce value="2.300000"/><fSuspensionCompDamp value="1.450000"/><fSuspensionReboundDamp value="2.000000"/>
 <fSuspensionUpperLimit value="0.100000"/><fSuspensionLowerLimit value="-0.110000"/><fSuspensionRaise value="0.000000"/><fSuspensionBiasFront value="0.520000"/>
 <fAntiRollBarForce value="0.850000"/><fAntiRollBarBiasFront value="0.540000"/><fRollCentreHeightFront value="0.420000"/><fRollCentreHeightRear value="0.430000"/>
 <fCollisionDamageMult value="0.700000"/><fWeaponDamageMult value="1.000000"/><fDeformationDamageMult value="0.650000"/><fEngineDamageMult value="1.000000"/>
 <fPetrolTankVolume value="65.000000"/><fOilVolume value="5.500000"/><fSeatOffsetDistX value="0.000000"/><fSeatOffsetDistY value="0.000000"/><fSeatOffsetDistZ value="0.000000"/>
 <nMonetaryValue value="50000"/><strModelFlags>440010</strModelFlags><strHandlingFlags>0</strHandlingFlags><strDamageFlags>0</strDamageFlags><AIHandling>AVERAGE</AIHandling>
 <SubHandlingData><Item type="CCarHandlingData"><fBackEndPopUpCarImpulseMult value="0.100000"/><fBackEndPopUpBuildingImpulseMult value="0.030000"/><fBackEndPopUpMaxDeltaSpeed value="0.600000"/></Item><Item type="NULL"/><Item type="NULL"/></SubHandlingData>
</Item></HandlingData></CHandlingDataMgr>
""",encoding='utf-8')

# Deliberately keep the proven embedded-texture / no-custom-carcols path. Custom
# YTD and carcols were previously implicated in unstable builds.
for name in ('carcols.meta','carvariations.meta'):
    p=DATA/name
    if p.exists(): p.unlink()
for name in ('kodiaqcs_hi.yft','kodiaqcs.ytd'):
    p=STREAM/name
    if p.exists(): p.unlink()

(CLIENT/'controls.lua').write_text(r"""local MODEL=GetHashKey('kodiaqcs')
local flashing=false
local phase=false
local sirenAudio=false
local initialized={}

local function veh()
 local p=PlayerPedId()
 if not IsPedInAnyVehicle(p,false) then return 0 end
 local v=GetVehiclePedIsIn(p,false)
 if GetEntityModel(v)~=MODEL then return 0 end
 return v
end
local function ex(v,n,on)
 if DoesExtraExist(v,n) then SetVehicleExtra(v,n,not on) end
end
local function signsOff(v) ex(v,1,false); ex(v,2,false) end
local function lightsOff(v) ex(v,3,false); ex(v,4,false) end
local function syncSiren(v)
 if flashing or sirenAudio then
  SetVehicleSiren(v,true)
  SetVehicleHasMutedSirens(v,not sirenAudio)
 else
  SetVehicleSiren(v,false)
  SetVehicleHasMutedSirens(v,true)
 end
end

RegisterCommand('csstop',function()
 local v=veh(); if v==0 then return end
 ex(v,2,false); ex(v,1,true)
end,false)
RegisterCommand('csfollow',function()
 local v=veh(); if v==0 then return end
 ex(v,1,false); ex(v,2,true)
end,false)
RegisterCommand('cssignoff',function()
 local v=veh(); if v==0 then return end
 signsOff(v)
end,false)
RegisterCommand('cslights',function()
 local v=veh(); if v==0 then return end
 flashing=not flashing
 if not flashing then lightsOff(v) end
 syncSiren(v)
end,false)
RegisterCommand('cssiren',function()
 local v=veh(); if v==0 then return end
 sirenAudio=not sirenAudio
 syncSiren(v)
end,false)
RegisterCommand('csdiag',function()
 local v=veh(); if v==0 then print('[KODIAQCS FINAL] not in vehicle'); return end
 print(('[KODIAQCS FINAL] extras 1=%s 2=%s 3=%s 4=%s lights=%s siren=%s'):format(
  tostring(DoesExtraExist(v,1)),tostring(DoesExtraExist(v,2)),tostring(DoesExtraExist(v,3)),tostring(DoesExtraExist(v,4)),tostring(flashing),tostring(sirenAudio)))
end,false)

CreateThread(function()
 while true do
  local v=veh()
  if v~=0 and not initialized[v] then
   signsOff(v); lightsOff(v); SetVehicleSiren(v,false); SetVehicleHasMutedSirens(v,true)
   initialized[v]=true
  end
  if flashing and v~=0 then
   phase=not phase
   ex(v,3,phase); ex(v,4,not phase)
   Wait(115)
  else
   Wait(250)
  end
 end
end)

RegisterKeyMapping('cslights','Celni sprava: cerveno-modre majaky','keyboard','J')
RegisterKeyMapping('cssiren','Celni sprava: sirena','keyboard','K')
RegisterKeyMapping('csstop','Celni sprava: STOP','keyboard','NUMPAD1')
RegisterKeyMapping('csfollow','Celni sprava: NASLEDUJ ME','keyboard','NUMPAD2')
RegisterKeyMapping('cssignoff','Celni sprava: tabule vypnout','keyboard','NUMPAD3')
""",encoding='utf-8')
print('FINAL RESOURCE READY', [str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()])
