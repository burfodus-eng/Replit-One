from sqlmodel import SQLModel, Field, create_engine, Session, select, Column, JSON
from datetime import datetime
from typing import Optional, List


class TelemetryRow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime
    stage_id: str
    vin_v: float
    iin_a: float
    vout_v: float
    iout_a: float
    mode: str
    power_w: float = 0.0


class WavemakerPreset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    cycle_duration_sec: int = 60
    is_built_in: bool = False
    flow_curves: dict = Field(default={}, sa_column=Column(JSON))


class ScheduledTaskRow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    task_type: str
    time: str
    enabled: bool = True
    preset_id: Optional[int] = None
    days_of_week: Optional[str] = None


def make_db(db_url: str):
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)
    return engine


class Store:
    def __init__(self, engine):
        self.engine = engine
    
    def persist(self, rows):
        with Session(self.engine) as s:
            for r in rows:
                data = r.model_dump()
                if 'power_w' not in data and 'vout_v' in data and 'iout_a' in data:
                    data['power_w'] = data['vout_v'] * data['iout_a']
                s.add(TelemetryRow(**data))
            s.commit()
    
    def get_history(self, stage_id: str, since: datetime, limit: int = 1000) -> List[TelemetryRow]:
        with Session(self.engine) as s:
            statement = (
                select(TelemetryRow)
                .where(TelemetryRow.stage_id == stage_id)
                .where(TelemetryRow.ts >= since)
                .order_by(TelemetryRow.ts.desc())
                .limit(limit)
            )
            results = s.exec(statement).all()
            return list(results)
    
    def query_telemetry_range(self, stage_id: str, start: datetime, end: datetime) -> List:
        with Session(self.engine) as s:
            statement = (
                select(TelemetryRow)
                .where(TelemetryRow.stage_id == stage_id)
                .where(TelemetryRow.ts >= start)
                .where(TelemetryRow.ts <= end)
                .order_by(TelemetryRow.ts.asc())
            )
            results = s.exec(statement).all()
            return [{"timestamp": r.ts, "vout_v": r.vout_v, "iout_a": r.iout_a, "power_w": r.power_w} for r in results]
    
    def get_all_presets(self) -> List[WavemakerPreset]:
        with Session(self.engine) as s:
            statement = select(WavemakerPreset).order_by(WavemakerPreset.name)
            results = s.exec(statement).all()
            return list(results)
    
    def get_preset(self, preset_id: int) -> Optional[WavemakerPreset]:
        with Session(self.engine) as s:
            return s.get(WavemakerPreset, preset_id)
    
    def create_preset(self, preset: WavemakerPreset) -> WavemakerPreset:
        with Session(self.engine) as s:
            s.add(preset)
            s.commit()
            s.refresh(preset)
            return preset
    
    def update_preset(self, preset_id: int, **kwargs) -> Optional[WavemakerPreset]:
        with Session(self.engine) as s:
            preset = s.get(WavemakerPreset, preset_id)
            if not preset:
                return None
            if preset.is_built_in:
                return None
            for key, value in kwargs.items():
                if hasattr(preset, key):
                    setattr(preset, key, value)
            s.add(preset)
            s.commit()
            s.refresh(preset)
            return preset
    
    def delete_preset(self, preset_id: int) -> bool:
        with Session(self.engine) as s:
            preset = s.get(WavemakerPreset, preset_id)
            if not preset or preset.is_built_in:
                return False
            s.delete(preset)
            s.commit()
            return True
    
    def get_all_scheduled_tasks(self) -> List[ScheduledTaskRow]:
        with Session(self.engine) as s:
            statement = select(ScheduledTaskRow).order_by(ScheduledTaskRow.time)
            results = s.exec(statement).all()
            return list(results)
    
    def get_scheduled_task(self, task_id: int) -> Optional[ScheduledTaskRow]:
        with Session(self.engine) as s:
            return s.get(ScheduledTaskRow, task_id)
    
    def create_scheduled_task(self, task: ScheduledTaskRow) -> ScheduledTaskRow:
        with Session(self.engine) as s:
            s.add(task)
            s.commit()
            s.refresh(task)
            return task
    
    def update_scheduled_task(self, task_id: int, **kwargs) -> Optional[ScheduledTaskRow]:
        with Session(self.engine) as s:
            task = s.get(ScheduledTaskRow, task_id)
            if not task:
                return None
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            s.add(task)
            s.commit()
            s.refresh(task)
            return task
    
    def delete_scheduled_task(self, task_id: int) -> bool:
        with Session(self.engine) as s:
            task = s.get(ScheduledTaskRow, task_id)
            if not task:
                return False
            s.delete(task)
            s.commit()
            return True
