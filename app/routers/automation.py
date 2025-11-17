from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.models import ScheduledTask, ScheduledTaskRequest
from app.services.storage import ScheduledTaskRow
import json


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


@router.post("/automation/wave-modes")
async def set_wave_mode(req: WaveModeRequest, request: Request):
    automation = request.app.state.automation
    success = automation.set_wave_mode(req.mode)
    return {"success": success, "mode": req.mode if success else automation.get_current_wave_mode()}


@router.get("/system/health")
async def get_system_health(request: Request):
    health = request.app.state.health
    latest_data = [r.model_dump() for r in request.app.state.latest]
    return health.check_health(latest_data)


@router.get("/automation/scheduled")
async def get_all_scheduled_tasks(request: Request):
    store = request.app.state.store
    tasks = store.get_all_scheduled_tasks()
    return [
        ScheduledTask(
            id=t.id,
            name=t.name,
            task_type=t.task_type,
            time=t.time,
            enabled=t.enabled,
            preset_id=t.preset_id,
            days_of_week=json.loads(t.days_of_week) if t.days_of_week else None
        )
        for t in tasks
    ]


def check_schedule_conflict(store, time: str, days_of_week, exclude_task_id=None):
    """Check if a scheduled task conflicts with existing tasks at the same time"""
    all_tasks = store.get_all_scheduled_tasks()
    
    for task in all_tasks:
        if task.id == exclude_task_id:
            continue
        if not task.enabled:
            continue
        if task.time != time:
            continue
        
        task_days = json.loads(task.days_of_week) if task.days_of_week else []
        new_days = days_of_week or []
        
        if len(task_days) == 0 and len(new_days) == 0:
            return task
        if len(task_days) == 0 or len(new_days) == 0:
            return task
        
        if any(day in new_days for day in task_days):
            return task
    
    return None


@router.post("/automation/scheduled")
async def create_scheduled_task(task_req: ScheduledTaskRequest, request: Request):
    store = request.app.state.store
    
    if task_req.enabled:
        conflict = check_schedule_conflict(store, task_req.time, task_req.days_of_week)
        if conflict:
            day_text = "on selected days" if task_req.days_of_week else "every day"
            raise HTTPException(
                status_code=409,
                detail=f'Scheduling conflict: "{conflict.name}" already scheduled at {task_req.time} {day_text}'
            )
    
    task_row = ScheduledTaskRow(
        name=task_req.name,
        task_type=task_req.task_type,
        time=task_req.time,
        enabled=task_req.enabled,
        preset_id=task_req.preset_id,
        days_of_week=json.dumps(task_req.days_of_week) if task_req.days_of_week else None
    )
    created = store.create_scheduled_task(task_row)
    return ScheduledTask(
        id=created.id,
        name=created.name,
        task_type=created.task_type,
        time=created.time,
        enabled=created.enabled,
        preset_id=created.preset_id,
        days_of_week=json.loads(created.days_of_week) if created.days_of_week else None
    )


@router.put("/automation/scheduled/{task_id}")
async def update_scheduled_task(task_id: int, task_req: ScheduledTaskRequest, request: Request):
    store = request.app.state.store
    
    if task_req.enabled:
        conflict = check_schedule_conflict(store, task_req.time, task_req.days_of_week, exclude_task_id=task_id)
        if conflict:
            day_text = "on selected days" if task_req.days_of_week else "every day"
            raise HTTPException(
                status_code=409,
                detail=f'Scheduling conflict: "{conflict.name}" already scheduled at {task_req.time} {day_text}'
            )
    
    update_data = {
        "name": task_req.name,
        "task_type": task_req.task_type,
        "time": task_req.time,
        "enabled": task_req.enabled,
        "preset_id": task_req.preset_id,
        "days_of_week": json.dumps(task_req.days_of_week) if task_req.days_of_week else None
    }
    updated = store.update_scheduled_task(task_id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return ScheduledTask(
        id=updated.id,
        name=updated.name,
        task_type=updated.task_type,
        time=updated.time,
        enabled=updated.enabled,
        preset_id=updated.preset_id,
        days_of_week=json.loads(updated.days_of_week) if updated.days_of_week else None
    )


@router.delete("/automation/scheduled/{task_id}")
async def delete_scheduled_task(task_id: int, request: Request):
    store = request.app.state.store
    success = store.delete_scheduled_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}


@router.post("/feed/start")
async def start_feed_mode(request: Request):
    automation = request.app.state.automation
    result = automation.start_feed_mode()
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to start feed mode"))
    return result


@router.get("/feed/status")
async def get_feed_status(request: Request):
    automation = request.app.state.automation
    return automation.get_feed_mode_status()


@router.post("/feed/stop")
async def stop_feed_mode(request: Request):
    automation = request.app.state.automation
    result = automation.stop_feed_mode()
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to stop feed mode"))
    return result
