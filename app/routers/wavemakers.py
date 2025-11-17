"""
Wavemaker API Endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List
from ..models import WavemakerChannel, WavemakerControlRequest, WavemakerHistoryPoint

router = APIRouter()


@router.get('/wavemakers', response_model=List[WavemakerChannel])
async def get_all_wavemakers(request: Request):
    """Get status of all 6 wavemaker channels"""
    manager = request.app.state.wavemaker_manager
    return manager.get_all_status()


@router.get('/wavemakers/{channel_id}', response_model=WavemakerChannel)
async def get_wavemaker(channel_id: int, request: Request):
    """Get status of a specific wavemaker channel"""
    try:
        manager = request.app.state.wavemaker_manager
        return manager.get_channel_status(channel_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put('/wavemakers/{channel_id}', response_model=WavemakerChannel)
async def update_wavemaker(channel_id: int, update: WavemakerControlRequest, request: Request):
    """Update wavemaker channel mode and/or target power"""
    try:
        manager = request.app.state.wavemaker_manager
        manager.update_channel(
            channel_id,
            mode=update.mode,
            target_pct=update.target_power_pct,
            pulse_duty_ratio=update.pulse_duty_ratio
        )
        return manager.get_channel_status(channel_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get('/wavemakers/{channel_id}/history', response_model=List[WavemakerHistoryPoint])
async def get_wavemaker_history(channel_id: int, request: Request, window: int = 900):
    """
    Get power history for a wavemaker channel
    
    Args:
        channel_id: Channel ID (0-5)
        window: Time window in seconds (default 900 = 15 minutes)
    """
    if not (0 <= channel_id < 6):
        raise HTTPException(status_code=404, detail=f"Invalid channel ID: {channel_id}")
        
    manager = request.app.state.wavemaker_manager
    return manager.get_channel_history(channel_id, window_s=window)


@router.post('/wavemakers/emergency-stop')
async def emergency_stop(request: Request):
    """Emergency stop all wavemaker channels"""
    manager = request.app.state.wavemaker_manager
    manager.emergency_stop()
    return {"status": "all channels stopped"}
