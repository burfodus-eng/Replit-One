from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/status")
async def status(request: Request):
    mgr = request.app.state.mgr
    return [s.model_dump() for s in mgr.list_status()]


@router.get("/snapshot")
async def snapshot(request: Request):
    return [r.model_dump() for r in request.app.state.latest]
