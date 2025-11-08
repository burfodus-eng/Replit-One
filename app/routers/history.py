from fastapi import APIRouter, Query, HTTPException, Request
from typing import List, Dict, Any
from datetime import datetime, timedelta
import math
import math as m

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("/array/{array_id}")
async def get_array_history(
    request: Request,
    array_id: str,
    time_range: str = Query("1h", regex="^(1h|6h|24h)$", alias="range")
):
    store = request.app.state.store
    
    range_minutes = {
        "1h": 60,
        "6h": 360,
        "24h": 1440
    }
    
    minutes = range_minutes.get(time_range, 60)
    start_time = datetime.now() - timedelta(minutes=minutes)
    
    try:
        rows = store.query_telemetry_range(array_id, start_time, datetime.now())
        
        downsample_factor = max(1, m.ceil(len(rows) / 100))
        sampled = rows[::downsample_factor]
        
        history = []
        for row in sampled:
            history.append({
                "t": row["timestamp"].isoformat(),
                "v": round(row["vout_v"], 2),
                "i": round(row["iout_a"], 3),
                "p": round(row["power_w"], 1)
            })
        
        return {"array_id": array_id, "range": time_range, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system")
async def get_system_history(
    request: Request,
    time_range: str = Query("1h", regex="^(1h|6h|24h)$", alias="range")
):
    store = request.app.state.store
    
    range_minutes = {
        "1h": 60,
        "6h": 360,
        "24h": 1440
    }
    
    minutes = range_minutes.get(time_range, 60)
    start_time = datetime.now() - timedelta(minutes=minutes)
    
    try:
        all_data = {}
        for array_id in ["A1", "A2", "A3"]:
            rows = store.query_telemetry_range(array_id, start_time, datetime.now())
            all_data[array_id] = rows
        
        max_len = max((len(v) for v in all_data.values()), default=0)
        downsample_factor = max(1, m.ceil(max_len / 100))
        
        history = []
        if max_len > 0:
            for i in range(0, max_len, downsample_factor):
                entry = {"t": None, "arrays": {}, "battery_w": 0}
                total_load = 0
                for array_id, rows in all_data.items():
                    if i < len(rows):
                        row = rows[i]
                        if entry["t"] is None:
                            entry["t"] = row["timestamp"].isoformat()
                        entry["arrays"][array_id] = {
                            "p": round(row["power_w"], 1)
                        }
                        total_load += row["power_w"]
                
                pv_power = request.app.state.latest.get("pv_power", 0) if hasattr(request.app.state, "latest") else 0
                entry["battery_w"] = round(pv_power - total_load, 1)
                
                if entry["t"]:
                    history.append(entry)
        
        return {"range": time_range, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
