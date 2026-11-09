"""Actual failed waiting prefix, original independent geometry, zero-model diagnosis."""
import copy,gzip,importlib.abc,json,math,sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v914_certified_wait_renewal';S=R/'runs/v858_nav2_verified/v913/main_we'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(C));from renewal_policy import due
sys.path.insert(0,str(R/'experiments/v913_periodic_startup_complete'))
from periodic_support import PeriodicSupport
from command_tube import admit
from tube_audit import independent_lower
j=json.loads(gzip.decompress((S/'MOTION_ENVELOPE.json.gz').read_bytes()));tubes=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));last=tubes[-1]
a=np.load(S/'physics/NATIVE_TRACE.npz');q=a['qpos'];v=a['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
known=json.loads((S/'physics/SETUP.json').read_text())['known'];prior=PeriodicSupport();witness=[]
for st in j['states']:
 prior.update(st['time'],st['native_tick'],st['support_bounds'])
 if st['native_tick']<=last['packet']['native_tick']:continue
 now=100.+st['time'];p=dict(native_tick=st['native_tick'],body=body[st['native_tick']-1].tolist(),sent_at=now,body_measured_at=now)
 s=dict(source_native_tick=st['native_tick'],source_scan_sim_time=st['time'],source_age_s=0.,decision_at=now,support_bounds=st['support_bounds'],periodic=prior.snapshot())
 proof=admit(p,s,0.,0.,known,now);sl,dl=independent_lower(p['body'],0.,0.,0.,s['support_bounds'],.05,known,s)
 witness.append(dict(tick=st['native_tick'],passed=proof['passed']and sl>=.155 and dl>=.155,online=proof,independent_static=sl,independent_dynamic=dl))
checks=dict(actual_original_last_command_is_stop=last['wanted']==[0.,0.],fresh_waiting_sources_all_permit_zero=bool(witness)and all(w['passed']for w in witness),waiting_not_a_vehicle_model=True,prearm_never_renews=not due('WAITING',100,None),recent_nominal_not_overridden=not due('RUNNING',100,99.86),stale_nominal_requests_zero=due('RUNNING',100,99.84),absent_nominal_requests_zero=due('RUNNING',100,None))
for key,now,last_at in [('reversed_clock',99,100),('nonfinite_clock',float('nan'),100),('nonfinite_nominal',100,float('nan'))]:
 try:due('RUNNING',now,last_at)
 except ValueError:checks[key+'_rejected']=True
 else:checks[key+'_rejected']=False
checks['original_native_expiry_reproduced']=(5225-last['proof']['body_native_tick'])*.01>.2+2.+last['proof']['body_age_s']+.05
result=dict(passed=all(checks.values()),checks=checks,witnesses=witness,last_command_tick=last['packet']['native_tick'],last_source_tick=last['source']['source_native_tick'],last_command_issued_at=last['proof']['issued_at'],last_scan_tick=j['states'][-1]['native_tick'],models=0,integrations=0,scope='Retrospective zero-command admission on saved actual waiting prefix; not executed renewals or continued-navigation success. Root cause: Nav2 planner recovery stops publication; old bridge only certifies upon incoming Twist.')
(O/'SAVED_WAIT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='witnesses'}));assert result['passed']
