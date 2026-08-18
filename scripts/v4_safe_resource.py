from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'build_output' / 'kodiaq_cs'
DATA = OUT / 'data'
CLIENT = OUT / 'client'
STREAM = OUT / 'stream'

# This build intentionally removes siren, carcols, variations and custom
# handling from the equation. It is a spawn-stability diagnostic first.
(OUT / 'fxmanifest.lua').write_text("""fx_version 'cerulean'
game 'gta5'

author 'Kodiaq CS safe-spawn diagnostic'
version '4.0.0'

files {
 'data/vehicles.meta'
}

data_file 'VEHICLE_METADATA_FILE' 'data/vehicles.meta'

client_script 'client/controls.lua'
""", encoding='utf-8')

(DATA / 'vehicles.meta').write_text("""<?xml version="1.0" encoding="UTF-8"?>
<CVehicleModelInfo__InitDataList>
  <residentTxd>vehshare</residentTxd>
  <residentAnims/>
  <InitDatas>
    <Item>
      <modelName>kodiaqcs</modelName>
      <txdName>vehshare</txdName>
      <handlingId>LANDSTALKER</handlingId>
      <gameName>KODIAQCS</gameName>
      <vehicleMakeName>SKODA</vehicleMakeName>
      <expressionDictName>null</expressionDictName>
      <expressionName>null</expressionName>
      <animConvRoofDictName>null</animConvRoofDictName>
      <animConvRoofName>null</animConvRoofName>
      <animConvRoofWindowsAffected/>
      <ptfxAssetName>null</ptfxAssetName>
      <audioNameHash>LANDSTALKER</audioNameHash>
      <layout>LAYOUT_STANDARD</layout>
      <coverBoundOffsets>LANDSTALKER_COVER_OFFSET_INFO</coverBoundOffsets>
      <explosionInfo>EXPLOSION_INFO_DEFAULT</explosionInfo>
      <scenarioLayout/>
      <cameraName>FOLLOW_SUV_CAMERA</cameraName>
      <aimCameraName>BOX_VEHICLE_AIM_CAMERA</aimCameraName>
      <bonnetCameraName>VEHICLE_BONNET_CAMERA_STANDARD_LONG</bonnetCameraName>
      <povCameraName>FOLLOW_SUV_CAMERA</povCameraName>
      <vfxInfoName>VFXVEHICLEINFO_CAR_GENERIC</vfxInfoName>
      <shouldUseCinematicViewMode value="true"/>
      <AllowPretendOccupants value="true"/>
      <AllowJoyriding value="true"/>
      <AllowSundayDriving value="true"/>
      <AllowBodyColorMapping value="false"/>
      <wheelScale value="0.39"/>
      <wheelScaleRear value="0.39"/>
      <dirtLevelMin value="0.0"/>
      <dirtLevelMax value="0.0"/>
      <envEffScaleMin value="0.0"/>
      <envEffScaleMax value="1.0"/>
      <damageMapScale value="1.0"/>
      <damageOffsetScale value="1.0"/>
      <diffuseTint value="0x00FFFFFF"/>
      <steerWheelMult value="1.0"/>
      <HDTextureDist value="5.0"/>
      <lodDistances content="float_array">30.0 60.0 120.0 240.0 500.0 500.0</lodDistances>
      <minSeatHeight value="0.78"/>
      <identicalModelSpawnDistance value="20"/>
      <maxNumOfSameColor value="10"/>
      <defaultBodyHealth value="1000.0"/>
      <frequency value="100"/>
      <swankness>SWANKNESS_4</swankness>
      <maxNum value="10"/>
      <flags></flags>
      <type>VEHICLE_TYPE_CAR</type>
      <plateType>VPT_FRONT_AND_BACK_PLATES</plateType>
      <dashboardType>VDT_RACE</dashboardType>
      <vehicleClass>VC_SUV</vehicleClass>
      <wheelType>VWT_SUV</wheelType>
      <trailers/>
      <additionalTrailers/>
      <drivers/>
      <extraIncludes/>
      <doorsWithCollisionWhenClosed/>
      <driveableDoors/>
      <rewards/>
      <cinematicPartCamera/>
      <NmBraceOverrideSet/>
    </Item>
  </InitDatas>
  <txdRelationships/>
</CVehicleModelInfo__InitDataList>
""", encoding='utf-8')

for name in ('handling.meta', 'carcols.meta', 'carvariations.meta'):
    p = DATA / name
    if p.exists():
        p.unlink()

# No siren calls in V4. Extras are still testable as static geometry after the
# vehicle can spawn reliably.
(CLIENT / 'controls.lua').write_text(r"""local model = GetHashKey('kodiaqcs')
local function veh()
  local p = PlayerPedId()
  if IsPedInAnyVehicle(p, false) then
    local v = GetVehiclePedIsIn(p, false)
    if GetEntityModel(v) == model then return v end
  end
  return 0
end
local function ex(v,n,on)
  if DoesExtraExist(v,n) then SetVehicleExtra(v,n,not on) end
end
RegisterCommand('csstop', function()
  local v=veh(); if v==0 then return end
  ex(v,2,false); ex(v,1,true)
end, false)
RegisterCommand('csfollow', function()
  local v=veh(); if v==0 then return end
  ex(v,1,false); ex(v,2,true)
end, false)
RegisterCommand('cssignoff', function()
  local v=veh(); if v==0 then return end
  ex(v,1,false); ex(v,2,false)
end, false)
RegisterCommand('cslights', function()
  local v=veh(); if v==0 then return end
  local on = not IsVehicleExtraTurnedOn(v,3)
  ex(v,3,on); ex(v,4,on)
end, false)
RegisterKeyMapping('cslights','Celní správa: světelné moduly','keyboard','J')
RegisterKeyMapping('csstop','Celní správa: STOP','keyboard','NUMPAD1')
RegisterKeyMapping('csfollow','Celní správa: NÁSLEDUJ MĚ','keyboard','NUMPAD2')
RegisterKeyMapping('cssignoff','Celní správa: tabule vypnout','keyboard','NUMPAD3')
""", encoding='utf-8')

# Deliberately omit a copied _hi YFT in the safe-spawn build. The previous V3
# used an identical full fragment for base and _hi. Removing it gives the game
# only one fragment representation to instantiate while we isolate the crash.
hi = STREAM / 'kodiaqcs_hi.yft'
if hi.exists():
    hi.unlink()

print('V4 SAFE RESOURCE READY', [str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()])
