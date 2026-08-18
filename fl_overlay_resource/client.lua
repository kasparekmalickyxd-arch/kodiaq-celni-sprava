local VEHICLE_MODEL = GetHashKey('civkodiaqfl')
local OVERLAY_MODEL = GetHashKey('civkodiaqfl_cs_overlay')
local overlays = {}
local enabled = true
local modelRequested = false

local function loadOverlayModel()
    if HasModelLoaded(OVERLAY_MODEL) then return true end
    if not modelRequested then
        RequestModel(OVERLAY_MODEL)
        modelRequested = true
    end
    return HasModelLoaded(OVERLAY_MODEL)
end

local function forceCustomsBasePaint(vehicle)
    -- The protected FL model itself is not edited. Make its paint a clean white base
    -- and lay the Customs graphics over it with the attached drawable.
    SetVehicleColours(vehicle, 111, 111)
    SetVehicleCustomPrimaryColour(vehicle, 245, 247, 250)
    SetVehicleCustomSecondaryColour(vehicle, 245, 247, 250)
    SetVehicleDirtLevel(vehicle, 0.0)
end

local function attachOverlay(vehicle)
    if overlays[vehicle] and DoesEntityExist(overlays[vehicle]) then
        return
    end
    if not loadOverlayModel() then return end

    local c = GetEntityCoords(vehicle)
    local obj = CreateObjectNoOffset(OVERLAY_MODEL, c.x, c.y, c.z, false, false, false)
    if obj == 0 then return end

    SetEntityCollision(obj, false, false)
    SetEntityCanBeDamaged(obj, false)
    SetEntityInvincible(obj, true)
    SetEntityLodDist(obj, 250)
    SetEntityAlpha(obj, 255, false)

    -- Overlay geometry was authored in civkodiaqfl local vehicle coordinates.
    AttachEntityToEntity(
        obj, vehicle, 0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        false, false, false, false, 2, true
    )

    overlays[vehicle] = obj
    forceCustomsBasePaint(vehicle)
end

local function deleteOverlay(vehicle)
    local obj = overlays[vehicle]
    if obj and DoesEntityExist(obj) then
        DetachEntity(obj, true, true)
        DeleteEntity(obj)
    end
    overlays[vehicle] = nil
end

local function vehiclesInWorld()
    return coroutine.wrap(function()
        local handle, vehicle = FindFirstVehicle()
        if handle == -1 then return end
        local ok = true
        repeat
            if vehicle and vehicle ~= 0 then coroutine.yield(vehicle) end
            ok, vehicle = FindNextVehicle(handle)
        until not ok
        EndFindVehicle(handle)
    end)
end

RegisterCommand('cslivery', function()
    enabled = not enabled
    if not enabled then
        for vehicle, _ in pairs(overlays) do deleteOverlay(vehicle) end
        print('[CIVKODIAQFL CS] polep vypnut')
    else
        print('[CIVKODIAQFL CS] polep zapnut')
    end
end, false)

RegisterCommand('csliveryreset', function()
    for vehicle, _ in pairs(overlays) do deleteOverlay(vehicle) end
    modelRequested = false
    RequestModel(OVERLAY_MODEL)
    print('[CIVKODIAQFL CS] overlay reset')
end, false)

CreateThread(function()
    RequestModel(OVERLAY_MODEL)
    modelRequested = true

    while true do
        if enabled and loadOverlayModel() then
            local seen = {}
            for vehicle in vehiclesInWorld() do
                if DoesEntityExist(vehicle) and GetEntityModel(vehicle) == VEHICLE_MODEL then
                    seen[vehicle] = true
                    attachOverlay(vehicle)
                    forceCustomsBasePaint(vehicle)
                end
            end

            for vehicle, _ in pairs(overlays) do
                if not seen[vehicle] or not DoesEntityExist(vehicle) or GetEntityModel(vehicle) ~= VEHICLE_MODEL then
                    deleteOverlay(vehicle)
                end
            end
        end
        Wait(750)
    end
end)

AddEventHandler('onResourceStop', function(resource)
    if resource ~= GetCurrentResourceName() then return end
    for vehicle, _ in pairs(overlays) do deleteOverlay(vehicle) end
    if HasModelLoaded(OVERLAY_MODEL) then SetModelAsNoLongerNeeded(OVERLAY_MODEL) end
end)
