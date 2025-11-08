from datetime import datetime
from ..models import Telemetry, StageStatus
from ..stages.led_stage import LEDStage
from ..stages.battery_stage import BatteryStage
from ..drivers import sensors_sim


class StageManager:
def __init__(self, config):
self.config = config
self.stages = {}
# build stages A/B/C + battery
for idx, arr in enumerate(config["stages"]["arrays"], start=0):
sid = f"Array-{arr['id']}"
self.stages[sid] = LEDStage(sid, sensors_sim.SensorSim(seed=idx))
self.stages["Battery"] = BatteryStage("Battery", sensors_sim.SensorSim(seed=99))


def list_status(self):
out = []
for sid, st in self.stages.items():
out.append(StageStatus(stage_id=sid, enabled=st.enabled, mode=st.mode, duty=st.duty))
return out


def control(self, stage_id, mode=None, duty=None, enable=None):
st = self.stages[stage_id]
if mode:
st.set_mode(mode)
st.apply_control(duty, enable)
return True


def snapshot(self):
rows = []
for sid, st in self.stages.items():
t = st.read_telemetry()
rows.append(Telemetry(stage_id=sid, ts=datetime.utcnow(), mode=st.mode, **t))
return rows