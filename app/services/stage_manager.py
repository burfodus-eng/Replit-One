from datetime import datetime
from ..models import Telemetry, StageStatus
from ..stages.led_stage import LEDStage
from ..stages.battery_stage import BatteryStage
from ..drivers import sensors_sim


class StageManager:
    def __init__(self, config):
        self.config = config
        self.stages = []
        self.stage_dict = {}
        
        for idx, arr in enumerate(config["stages"]["arrays"], start=0):
            sid = arr['id']
            stage = LEDStage(sid, sensors_sim.SensorSim(seed=idx, stage_config=arr), config=arr)
            self.stages.append(stage)
            self.stage_dict[sid] = stage
        
        battery_stage = BatteryStage("Battery", sensors_sim.SensorSim(seed=99))
        self.stages.append(battery_stage)
        self.stage_dict["Battery"] = battery_stage


    def list_status(self):
        out = []
        for st in self.stages:
            stage_id = st.id if hasattr(st, 'id') else st.stage_id
            out.append(StageStatus(stage_id=stage_id, enabled=st.enabled, mode=st.mode, duty=st.duty))
        return out


    def control(self, stage_id, mode=None, duty=None, enable=None):
        st = self.stage_dict.get(stage_id)
        if not st:
            return False
        if mode:
            st.set_mode(mode)
        st.apply_control(duty, enable)
        return True


    def snapshot(self):
        rows = []
        for st in self.stages:
            t = st.read_telemetry()
            stage_id = st.id if hasattr(st, 'id') else st.stage_id
            rows.append(Telemetry(stage_id=stage_id, ts=datetime.utcnow(), mode=st.mode, **t))
        return rows
