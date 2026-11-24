"""Original200zero actions plus actual closure-only5native sensor receipts."""
def complete(vehicle,progress):
 assert not progress.get('attempted',False),'ERROR_STOP_CAPTURE_NO_RETRY'
 progress.update(attempted=True,origin_native=vehicle.count,applied=0,scan_native_ticks=[],closed=False)
 def record():
  before=vehicle.count;rows=len(vehicle.sensor_rows)
  value=vehicle.scan()
  assert vehicle.count==before and value['native_tick']==before and len(vehicle.sensor_rows)==rows+1,'ERROR_STOP_CURRENT_SCAN_BINDING'
  progress['scan_native_ticks'].append(before)
 try:
  if vehicle.count%5==0 and not any(row['native_tick']==vehicle.count for row in vehicle.sensor_rows):record()
  for _ in range(200):
   before=vehicle.count;progress['step_inflight_unknown']=True
   vehicle.step(0.,0.,False)
   progress['step_inflight_unknown']=False
   assert vehicle.count==before+1,'ERROR_STOP_SINGLE_NATIVE_REQUIRED'
   progress['applied']+=1
   if vehicle.count%5==0:record()
  progress.update(closed=True,complete200=True)
  return dict(applied=200,current_sensor_rows=len(progress['scan_native_ticks']),closure_only_observations=True)
 except BaseException as error:
  progress.update(closed=True,complete200=False,error=repr(error),last_actual_native=vehicle.count)
  raise
