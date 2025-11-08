from sqlmodel import SQLModel, Field, create_engine, Session, select
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
