import random, time


class SensorSim:
def __init__(self, seed=None):
self.rng = random.Random(seed or time.time())
def read(self):
# returns (vin, iin, vout, iout)
vin = self.rng.uniform(30, 42) # panel V (2S)
iin = self.rng.uniform(0.2, 3.0)
vout = self.rng.uniform(24, 36)
iout = self.rng.uniform(0.1, 2.0)
return vin, iin, vout, iout