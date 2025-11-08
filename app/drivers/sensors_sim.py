import random
import time


class SensorSim:
    def __init__(self, seed=None):
        self.rng = random.Random(seed or time.time())
        self.base_vin = 36.0
        self.base_vout = 30.0
    
    def read(self, duty=0.0, enabled=True):
        """
        Simulate realistic sensor readings based on duty cycle
        duty: 0.0 to 1.0 (0% to 100%)
        enabled: whether the stage is enabled
        """
        if not enabled:
            # Stage disabled - minimal readings
            vin = self.base_vin + self.rng.uniform(-1, 1)
            iin = self.rng.uniform(0.0, 0.1)
            vout = self.base_vout + self.rng.uniform(-1, 1)
            iout = 0.0
            return vin, iin, vout, iout
        
        # Calculate current based on duty cycle (0-100% = 0-2A)
        base_current = duty * 2.0
        iout = base_current + self.rng.uniform(-0.1, 0.1)
        iout = max(0.0, iout)
        
        # Voltage drops slightly under load (up to 10% drop at full load)
        voltage_drop_factor = 1.0 - (duty * 0.1)
        vout = (self.base_vout * voltage_drop_factor) + self.rng.uniform(-0.5, 0.5)
        
        # Input current is slightly higher than output (efficiency factor ~90%)
        iin = (iout * 1.1) + self.rng.uniform(-0.05, 0.05)
        iin = max(0.0, iin)
        
        # Input voltage varies slightly
        vin = self.base_vin + self.rng.uniform(-2, 2)
        
        return vin, iin, vout, iout
