from fastapi import APIRouter


router = APIRouter()


@router.get("/status")
async def status(request):
mgr = request.app.state.mgr
return [s.model_dump() for s in mgr.list_status()]


@router.get("/snapshot")
async def snapshot(request):
return [r.model_dump() for r in request.app.state.latest]