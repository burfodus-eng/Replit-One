from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class WaveModeRequest(BaseModel):
    mode: str


@router.get("/automation/tasks/completed")
async def get_completed_tasks(request: Request):
    automation = request.app.state.automation
    return automation.get_completed_tasks()


@router.get("/automation/tasks/upcoming")
async def get_upcoming_tasks(request: Request):
    automation = request.app.state.automation
    return automation.get_upcoming_tasks()


@router.get("/automation/wave-modes")
async def get_wave_modes(request: Request):
    automation = request.app.state.automation
    return {
        "modes": automation.get_wave_modes(),
        "current": automation.get_current_wave_mode()
    }


@router.post("/automation/wave-mode")
async def set_wave_mode(req: WaveModeRequest, request: Request):
    automation = request.app.state.automation
    success = automation.set_wave_mode(req.mode)
    return {"success": success, "mode": req.mode if success else automation.get_current_wave_mode()}


@router.get("/system/health")
async def get_system_health(request: Request):
    health = request.app.state.health
    latest_data = [r.model_dump() for r in request.app.state.latest]
    return health.check_health(latest_data)
