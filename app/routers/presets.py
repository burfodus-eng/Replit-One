from fastapi import APIRouter, HTTPException, Request
from typing import List
from ..models import WavemakerPresetResponse, WavemakerPresetRequest
from ..services.storage import WavemakerPreset

router = APIRouter()


@router.get('/presets', response_model=List[WavemakerPresetResponse])
async def list_presets(request: Request):
    presets = request.app.state.store.get_all_presets()
    return [WavemakerPresetResponse(**p.model_dump()) for p in presets]


@router.get('/presets/{preset_id}', response_model=WavemakerPresetResponse)
async def get_preset(preset_id: int, request: Request):
    preset = request.app.state.store.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return WavemakerPresetResponse(**preset.model_dump())


@router.post('/presets', response_model=WavemakerPresetResponse)
async def create_preset(data: WavemakerPresetRequest, request: Request):
    preset = WavemakerPreset(
        name=data.name,
        description=data.description or "",
        cycle_duration_sec=data.cycle_duration_sec or 60,
        is_built_in=False,
        flow_curves=data.flow_curves or {}
    )
    created = request.app.state.store.create_preset(preset)
    return WavemakerPresetResponse(**created.model_dump())


@router.put('/presets/{preset_id}', response_model=WavemakerPresetResponse)
async def update_preset(preset_id: int, data: WavemakerPresetRequest, request: Request):
    updates = {}
    if data.name:
        updates['name'] = data.name
    if data.description is not None:
        updates['description'] = data.description
    if data.cycle_duration_sec is not None:
        updates['cycle_duration_sec'] = data.cycle_duration_sec
    if data.flow_curves is not None:
        updates['flow_curves'] = data.flow_curves
    
    updated = request.app.state.store.update_preset(preset_id, **updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Preset not found")
    return WavemakerPresetResponse(**updated.model_dump())


@router.delete('/presets/{preset_id}')
async def delete_preset(preset_id: int, request: Request):
    success = request.app.state.store.delete_preset(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found or is built-in")
    return {"success": True}


@router.post('/presets/{preset_id}/activate')
async def activate_preset(preset_id: int, request: Request):
    success = request.app.state.preset_manager.set_active_preset(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"success": True, "active_preset_id": preset_id}


@router.get('/presets/active/status')
async def get_active_preset_status(request: Request):
    preset = request.app.state.preset_manager.get_active_preset()
    if not preset:
        return {"active_preset": None, "power_levels": {}}
    
    power_levels = request.app.state.preset_manager.get_current_power_levels()
    
    return {
        "active_preset": WavemakerPresetResponse(**preset.model_dump()),
        "power_levels": power_levels
    }
