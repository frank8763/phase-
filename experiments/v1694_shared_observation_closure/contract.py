"""Measured clock and closure labels for future, unexecuted adapters only.

Integer native order decides causality. The original 1e-8 simulation-clock
tolerance handles accumulation roundoff; no packet or timestamp is edited.
Controller selection, requests, model state and memory are outside this module.
"""
import copy,hashlib,json,math,time
SCAN_KEYS=('native_tick','time','xy','yaw','ranges')
NATIVE_DT=.01
CLOCK_TOLERANCE=1e-8
CLOSURE_PHASE='ERROR_STOP_CLOSURE'

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def native_clock(native,stamp):
 assert type(native)is int and native>=0,'CLOCK_NATIVE_INTEGER'
 assert type(stamp)in(int,float)and math.isfinite(stamp),'CLOCK_FINITE'
 assert abs(stamp-NATIVE_DT*native)<=CLOCK_TOLERANCE,'CLOCK_NATIVE_BINDING'
 return stamp

def scan_only(scan,native,sim_time):
 native_clock(native,sim_time)
 clean={k:copy.deepcopy(scan[k])for k in SCAN_KEYS}
 source=clean['native_tick'];native_clock(source,clean['time'])
 assert 0<=native-source<=5,'SCAN_NATIVE_AGE'
 age=sim_time-clean['time']
 assert -CLOCK_TOLERANCE<=age<=5*NATIVE_DT+CLOCK_TOLERANCE,'SCAN_SIM_TIME_AGE'
 assert len(clean['xy'])==2 and len(clean['ranges'])==32,'SCAN_SHAPE'
 assert all(math.isfinite(x)for x in [*clean['xy'],clean['yaw'],*clean['ranges']]),'SCAN_FINITE'
 assert all(0<=x<=3.00000001 for x in clean['ranges']),'SCAN_RANGE'
 return clean

def verify_receipt(receipt,expected_native):
 assert receipt['schema']=='PHASE_CURRENT_MEASUREMENT_V1'and receipt['packet_acquisitions']==1,'RECEIPT_SCHEMA'
 p=receipt['packet'];assert receipt['packet_sha256']==digest(p),'PACKET_SHA'
 native_clock(expected_native,p['sim_time'])
 assert p['native_tick']==p['steering']['native_tick']==expected_native,'PACKET_NATIVE'
 a,b=receipt['before_monotonic'],receipt['after_monotonic'];t=p['body_measured_at']
 assert all(math.isfinite(v)for v in [a,b,t,p['sent_at'],p['steering']['measured_at']]),'MEASURED_CLOCK_FINITE'
 assert a<=t==p['sent_at']==p['steering']['measured_at']<=b,'ACQUISITION_CLOCK'
 # Use the actual recorded packet time, independently bound to its native tick.
 clean=scan_only(receipt['scan'],expected_native,p['sim_time'])
 assert clean==receipt['scan'],'SCAN_EXTRANEOUS_FIELDS'
 return copy.deepcopy(p)

def acquire(vehicle,packet_function,scan):
 before=time.monotonic();p=packet_function(vehicle);after=time.monotonic()
 receipt=dict(schema='PHASE_CURRENT_MEASUREMENT_V1',packet_acquisitions=1,packet=copy.deepcopy(p),packet_sha256=digest(p),before_monotonic=before,after_monotonic=after,scan=scan_only(scan,vehicle.count,float(vehicle.d.time)))
 verify_receipt(receipt,vehicle.count)
 return receipt

def complete_closure(vehicle,progress,original_complete):
 # Set the evidence phase BEFORE any original error-stop callback. Leave it
 # set even if the callback raises, so partially executed closure stays tagged.
 vehicle._chain_phase=CLOSURE_PHASE
 return original_complete(vehicle,progress)

def partition_journal(journal,normal_phase,goal_stop_phase=None):
 assert isinstance(normal_phase,str)and normal_phase!=CLOSURE_PHASE
 assert goal_stop_phase is None or goal_stop_phase not in {normal_phase,CLOSURE_PHASE}
 groups=dict(normal=[],goal_stop=[],error_stop=[]);state='normal'
 for i,row in enumerate(journal):
  assert row['before_native']==i and row['applied'],'JOURNAL_CONTIGUOUS_APPLIED'
  phase=row['phase']
  if phase==normal_phase:
   assert state=='normal','NORMAL_AFTER_TERMINAL_PHASE'
   groups['normal'].append(i)
  elif goal_stop_phase is not None and phase==goal_stop_phase:
   assert state!='error_stop','GOAL_STOP_AFTER_ERROR_STOP'
   assert row['request']==[0.,0.,False],'GOAL_STOP_NONZERO_REQUEST'
   state='goal_stop';groups['goal_stop'].append(i)
  else:
   assert phase==CLOSURE_PHASE,'UNDECLARED_EXECUTION_PHASE'
   assert row['request']==[0.,0.,False],'ERROR_STOP_NONZERO_REQUEST'
   state='error_stop';groups['error_stop'].append(i)
 return groups
