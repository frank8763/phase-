"""Incremental byte account for the existing canonical physical prefix."""
import json
from pathlib import Path
import numpy as np

def packed(value):return json.dumps(value,separators=(',',':'),allow_nan=False,default=lambda x:x.tolist()).encode()

class CaptureBudget:
 def __init__(self,quota):
  self.quota=quota;self.key='canonical-physical-prefix';self.rows=0;self.contacts=0;self.commands=0;self.sensors=0;self.raw=0;self.encoded=0;self.quota.hold(self.key,262144)

 def update(self,vehicle,*,requested_native=0):
  # Capture actual N+1 arrays and JSON exactly once in order. No simulated
  # future contact count or initializer-internal work is invented here.
  assert len(vehicle.rows)>=self.rows and len(vehicle.contacts)>=self.contacts and len(vehicle.commands)>=self.commands and len(vehicle.sensor_rows)>=self.sensors
  for row in vehicle.rows[self.rows:]:self.raw+=sum(np.asarray(value).nbytes for value in row.values())
  for sequence,start in [(vehicle.contacts,self.contacts),(vehicle.commands,self.commands),(vehicle.sensor_rows,self.sensors)]:
   for item in sequence[start:]:self.encoded+=len(packed(item))+16
  self.rows=len(vehicle.rows);self.contacts=len(vehicle.contacts);self.commands=len(vehicle.commands);self.sensors=len(vehicle.sensor_rows)
  # Original finish writes one NPZ and two gzip streams plus JSON. Factor2
  # admits uncompressed bytes and container/temporary overhead conservatively.
  pending=2*(self.raw+self.encoded)+262144
  self.quota.hold(self.key,pending)
  if requested_native:self.quota.admit(262144,'NEXT_NATIVE_CAPTURE_HEADROOM')
  return pending

 def finish(self,vehicle):
  pending=self.update(vehicle)
  with self.quota.spend(self.key):
   self.quota.admit(pending,'SAVE_COMPLETE_CANONICAL_PHYSICAL_PREFIX')
   result=vehicle.finish()
  self.quota.release(self.key);return result
