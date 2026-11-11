"""Parked pre-publication admission, bounded observation reacquisition only.

No model/controls/physics calls. A stale packet is discarded; all geometry,
source containment, original50ms and pose/memory gates remain strict. Invalid
source or state is never retried. No promise about operating-system scheduling.
"""
import time
from dataclasses import dataclass
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v1058_fresh_repeat_entry'))
from atomic import publish
@dataclass(frozen=True)
class Capture:
 view:object
 packet:dict
 source:dict
 attempts:tuple
 elapsed:float

def capture(buffers,vehicle,evidence,packet_fn,deadline):
 # Potentially expensive domain materialization happens BEFORE the new body
 # and encoder timestamp, with the existing certified parked hold in force.
 origin=vehicle.count;source=evidence.source(vehicle);attempts=[]
 for attempt in range(2):
  assert time.time()<deadline,'CAPTURE_WALL_DEADLINE'
  packet=packet_fn(vehicle,True);now=time.monotonic();age=now-packet['body_measured_at'];assert vehicle.count==origin,'CAPTURE_CANNOT_ADVANCE_NATIVE';assert age>=0,'MEASUREMENT_FROM_FUTURE'
  try:
   view=publish(buffers,packet,source,now);elapsed=time.monotonic()-packet['body_measured_at']
   if elapsed>.05:raise AssertionError('PUBLICATION_TO_FIRST_CONTROL_EXPIRED')
  except AssertionError as e:
   reason=str(e);attempts.append(dict(attempt=attempt+1,accepted=False,reason=reason,measured_age_s=age,native_tick=packet['native_tick'],source_native_tick=source['source_native_tick']))
   # Geometry, steering, controller, clocks, source or freshness problems
   # other than this two measured-body wall-age rejection stop immediately.
   if reason not in ['STALE_MEASURED_BODY','PUBLICATION_TO_FIRST_CONTROL_EXPIRED']or attempt==1:raise
   continue
  attempts.append(dict(attempt=attempt+1,accepted=True,measured_age_s=age,native_tick=packet['native_tick'],source_native_tick=source['source_native_tick']))
  return Capture(view,packet,source,tuple(attempts),elapsed)
 raise AssertionError('FIXED_CAPTURE_ATTEMPTS_EXHAUSTED')
