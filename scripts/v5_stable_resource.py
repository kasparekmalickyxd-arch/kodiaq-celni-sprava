from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'build_output' / 'kodiaq_cs'
DATA = OUT / 'data'
CLIENT = OUT / 'client'
STREAM = OUT / 'stream'
for p in (DATA, CLIENT, STREAM):
    p.mkdir(parents=True, exist_ok=True)

# V5 keeps the exact crash-free V4 YFT/material/physics path and restores only
# low-risk gameplay features. No YTD, copied _hi YFT, carcols or variations yet.
(OUT / 'fxmanifest.lua').write_text("""fx_version 'cerulean'
game 'gta5'

author 'Kodiaq CS stable feature build'
version '5.0.0'

files {
 'data/vehicles.meta',
 'data/handling.meta'
}

data_file 'VEHICLE_METADATA_FILE' 'data/vehicles.meta'
data_file 'HANDLING_FILE' 'data/handling.meta'

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
      <handlingId>KODIAQCS</handlingId>
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

# Conservative AWD SUV tune. The goal here is predictable road behaviour, not
# maximum performance. It can be tuned later after spawn stability is proven.
(DATA / 'handling.meta').write_text("""<?xml version="1.0" encoding="UTF-8"?>
<CHandlingDataMgr>
  <HandlingData>
    <Item type="CHandlingData">
      <handlingName>KODIAQCS</handlingName>
      <fMass value="2050.000000" />
      <fInitialDragCoeff value="7.200000" />
      <fPercentSubmerged value="85.000000" />
      <vecCentreOfMassOffset x="0.000000" y="0.020000" z="-0.120000" />
      <vecInertiaMultiplier x="1.100000" y="1.250000" z="1.650000" />
      <fDriveBiasFront value="0.550000" />
      <nInitialDriveGears value="7" />
      <fInitialDriveForce value="0.335000" />
      <fDriveInertia value="1.050000" />
      <fClutchChangeRateScaleUpShift value="3.000000" />
      <fClutchChangeRateScaleDownShift value="3.000000" />
      <fInitialDriveMaxFlatVel value="205.000000" />
      <fBrakeForce value="0.850000" />
      <fBrakeBiasFront value="0.580000" />
      <fHandBrakeForce value="0.650000" />
      <fSteeringLock value="37.000000" />
      <fTractionCurveMax value="2.650000" />
      <fTractionCurveMin value="2.350000" />
      <fTractionCurveLateral value="22.500000" />
      <fTractionSpringDeltaMax value="0.130000" />
      <fLowSpeedTractionLossMult value="0.450000" />
      <fCamberStiffnesss value="0.000000" />
      <fTractionBiasFront value="0.500000" />
      <fTractionLossMult value="0.900000" />
      <fSuspensionForce value="2.300000" />
      <fSuspensionCompDamp value="1.450000" />
      <fSuspensionReboundDamp value="2.000000" />
      <fSuspensionUpperLimit value="0.100000" />
      <fSuspensionLowerLimit value="-0.110000" />
      <fSuspensionRaise value="0.000000" />
      <fSuspensionBiasFront value="0.520000" />
      <fAntiRollBarForce value="0.850000" />
      <fAntiRollBarBiasFront value="0.540000" />
      <fRollCentreHeightFront value="0.420000" />
      <fRollCentreHeightRear value="0.430000" />
      <fCollisionDamageMult value="0.700000" />
      <fWeaponDamageMult value="1.000000" />
      <fDeformationDamageMult value="0.650000" />
      <fEngineDamageMult value="1.000000" />
      <fPetrolTankVolume value="65.000000" />
      <fOilVolume value="5.500000" />
      <fSeatOffsetDistX value="0.000000" />
      <fSeatOffsetDistY value="0.000000" />
      <fSeatOffsetDistZ value="0.000000" />
      <nMonetaryValue value="50000" />
      <strModelFlags>440010</strModelFlags>
      <strHandlingFlags>0</strHandlingFlags>
      <strDamageFlags>0</strDamageFlags>
      <AIHandling>AVERAGE</AIHandling>
      <SubHandlingData>
        <Item type="CCarHandlingData">
          <fBackEndPopUpCarImpulseMult value="0.100000" />
          <fBackEndPopUpBuildingImpulseMult value="0.030000" />
          <fBackEndPopUpMaxDeltaSpeed value="0.600000" />
        </Item>
        <Item type="NULL" />
        <Item type="NULL" />
      </SubHandlingData>
    </Item>
  </HandlingData>
</CHandlingDataMgr>
""", encoding='utf-8')

for name in ('carcols.meta', 'carvariations.meta'):
    p = DATA / name
    if p.exists():
        p.unlink()

# No custom YTD and no copied identical _hi fragment. These were deliberately
# removed in the crash-free V4 and stay removed in V5.
for name in ('kodiaqcs_hi.yft', 'kodiaqcs.ytd'):
    p = STREAM / name
    if p.exists():
        p.unlink()

(CLIENT / 'controls.lua').write_text(r"""local MODEL = GetHashKey('kodiaqcs')
local emergencyOn = false
local phase = false

local function currentVehicle()
    local ped = PlayerPedId()
    if not IsPedInAnyVehicle(ped, false) then return 0 end
    local v = GetVehiclePedIsIn(ped, false)
    if GetEntityModel(v) ~= MODEL then return 0 end
    return v
end

local function extra(v, n, on)
    if DoesExtraExist(v, n) then
        SetVehicleExtra(v, n, not on)
    end
end

local function signsOff(v)
    extra(v, 1, false)
    extra(v, 2, false)
end

RegisterCommand('csstop', function()
    local v = currentVehicle(); if v == 0 then return end
    extra(v, 2, false)
    extra(v, 1, true)
end, false)

RegisterCommand('csfollow', function()
    local v = currentVehicle(); if v == 0 then return end
    extra(v, 1, false)
    extra(v, 2, true)
end, false)

RegisterCommand('cssignoff', function()
    local v = currentVehicle(); if v == 0 then return end
    signsOff(v)
end, false)

RegisterCommand('cslights', function()
    local v = currentVehicle(); if v == 0 then return end
    emergencyOn = not emergencyOn
    if not emergencyOn then
        extra(v, 3, false)
        extra(v, 4, false)
    end
end, false)

RegisterCommand('csdiag', function()
    local v = currentVehicle(); if v == 0 then print('[KODIAQCS] not in vehicle'); return end
    print(('[KODIAQCS] extras: 1=%s 2=%s 3=%s 4=%s'):format(
        tostring(DoesExtraExist(v,1)), tostring(DoesExtraExist(v,2)),
        tostring(DoesExtraExist(v,3)), tostring(DoesExtraExist(v,4))))
end, false)

CreateThread(function()
    while true do
        if emergencyOn then
            local v = currentVehicle()
            if v ~= 0 then
                phase = not phase
                extra(v, 3, phase)
                extra(v, 4, not phase)
                Wait(120)
            else
                emergencyOn = false
                Wait(250)
            end
        else
            Wait(250)
        end
    end
end)

RegisterKeyMapping('cslights','Celní správa: červeno-modré moduly','keyboard','J')
RegisterKeyMapping('csstop','Celní správa: STOP','keyboard','NUMPAD1')
RegisterKeyMapping('csfollow','Celní správa: NÁSLEDUJ MĚ','keyboard','NUMPAD2')
RegisterKeyMapping('cssignoff','Celní správa: tabule vypnout','keyboard','NUMPAD3')
""", encoding='utf-8')

print('V5 STABLE FEATURE RESOURCE READY', [str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()])
