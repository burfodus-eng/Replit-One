from fastapi import APIRouter, HTTPException, Request
from ..models import ControlRequest


router = APIRouter()


@router.post("/control")
async def control(req: ControlRequest, request: Request):
    mgr = request.app.state.mgr
    if req.stage_id not in mgr.stages:
        raise HTTPException(404, "stage not found")
    mgr.control(req.stage_id, mode=req.mode, duty=req.duty, enable=req.enable)
    return {"ok": True}
