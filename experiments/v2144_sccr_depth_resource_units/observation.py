"""Pure causal scan and exact current acquisition; no actor metadata accepted."""
import copy,math,time
from context import digest
KEYS=('native_tick','time','xy','yaw','ranges')

# Reuse exact already SOURCE-qualified contract (no timestamp edits).
from context import R,load
_shared=load('v1806_shared_actual_clock',R/'experiments/v1694_shared_observation_closure/contract.py')
scan_only=_shared.scan_only

def points(scan):
 # Original 32 equally-spaced rays. No evaluator hit labels or actor truth.
 out=[]
 for i,r in enumerate(scan['ranges']):
  if r<3.-1e-8:
   a=scan['yaw']+2*math.pi*i/32
   out.append([scan['xy'][0]+r*math.cos(a),scan['xy'][1]+r*math.sin(a)])
 return out

def verify(receipt,expected_native,expected_sim_time):
 assert receipt['schema']=='DWA_CURRENT_ACQUISITION_V1'and receipt['packet_acquisitions']==1
 p=receipt['packet'];assert receipt['packet_sha256']==digest(p),'PACKET_SHA'
 assert p['native_tick']==p['steering']['native_tick']==expected_native and abs(p['sim_time']-expected_sim_time)<=1e-8,'PACKET_NATIVE_TIME'
 a,b=receipt['before_monotonic'],receipt['after_monotonic'];t=p['body_measured_at']
 assert all(math.isfinite(v)for v in [a,b,t,p['sent_at'],p['steering']['measured_at']])
 assert a<=t==p['sent_at']==p['steering']['measured_at']<=b,'ACQUISITION_CLOCK'
 clean=scan_only(receipt['scan'],expected_native,expected_sim_time)
 assert clean==receipt['scan'],'SCAN_EXTRANEOUS_FIELDS'
 return copy.deepcopy(p)

def acquire(v,binding,scan):
 before=time.monotonic();p=binding['packet'](v);after=time.monotonic()
 r=dict(schema='DWA_CURRENT_ACQUISITION_V1',packet_acquisitions=1,packet=copy.deepcopy(p),packet_sha256=digest(p),before_monotonic=before,after_monotonic=after,scan=scan_only(scan,v.count,float(v.d.time)))
 verify(r,v.count,float(v.d.time));return r
