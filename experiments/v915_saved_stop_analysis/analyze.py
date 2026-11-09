"""Saved-array diagnosis only; model/ROS imports forbidden. No new trajectories."""
import copy,gzip,hashlib,importlib.abc,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v915_saved_stop_analysis';S=R/'runs/v858_nav2_verified/v914/main_we'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(R/'experiments/v914_certified_wait_renewal'))
from command_tube import admit,nominal,NORMALS,HALF
from periodic_support import bounds_from_vertices
rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));known=json.loads((S/'physics/SETUP.json').read_text())['known']
last=rows[-1];prior=rows[-2];stop=rows[-3];assert not last['proof']['passed'] and prior['proof']['passed'] and stop['proof']['v']==0
witness=[]
for row in rows[-10:]:
 p,s,a=row['packet'],row['source'],row['proof'];now=a['issued_at'];wanted=admit(p,s,*row['wanted'],known,now);zero=admit(p,s,0.,0.,known,now)
 assert abs(zero['dynamic_lower_m']-a['dynamic_lower_m'])<1e-10 if a['v']==0 else abs(wanted['dynamic_lower_m']-a['dynamic_lower_m'])<1e-10
 times=np.arange(0.,2.21,.02);poses=nominal(p['body'],0,0,times);angles=poses[:,2];low=poses[:,:2]@NORMALS.T-HALF[0]*abs(np.c_[np.cos(angles),np.sin(angles)]@NORMALS.T)-HALF[1]*abs(np.c_[-np.sin(angles),np.cos(angles)]@NORMALS.T)
 at=s['source_scan_sim_time']+zero['source_age_s']+zero['body_age_s']+.05+times
 high=np.minimum(np.array(s['support_bounds'])[None,:]+.08*(zero['source_age_s']+zero['body_age_s']+.05+times[:,None]),bounds_from_vertices(s['periodic']['vertices'],at))+.1
 lowers=np.max(low-high,axis=1)-zero['spatial_reserve_m'];i=int(np.argmin(lowers))
 witness.append(dict(tick=p['native_tick'],wanted_dynamic=wanted['dynamic_lower_m'],stop_dynamic=zero['dynamic_lower_m'],static=zero['static_lower_m'],stop_min_time=float(times[i]),current_dynamic=float(lowers[0]),reserve=zero['spatial_reserve_m']))
# One-variable diagnostic interventions on recorded inputs, never passed to a vehicle.
p,s,a=last['packet'],last['source'],last['proof'];now=a['issued_at'];interventions={}
for name,body in [('actual',p['body']),('hold_first_stop_body',stop['packet']['body']),('hold_last_accepted_body',prior['packet']['body'])]:
 q=copy.deepcopy(p);q['body']=body;z=admit(q,s,0,0,known,now);interventions[name]={k:z[k]for k in ['passed','static_lower_m','dynamic_lower_m']}
trace=np.load(S/'physics/NATIVE_TRACE.npz');q=trace['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));body=np.c_[q[:,:2],yaw]
a=prior['proof'];tick=a['body_native_tick'];tail=body[tick-1:];elapsed=(np.arange(tick,len(body)+1)-tick)*.01;pred=nominal(a['body'],0,0,elapsed)
pos=np.linalg.norm(tail[:,:2]-pred[:,:2],axis=1);ang=abs(np.arctan2(np.sin(tail[:,2]-pred[:,2]),np.cos(tail[:,2]-pred[:,2])))
retained=dict(certificate_tick=tick,last_tick=len(body),remaining_recorded_s=float(elapsed[-1]),maximum_actual_position_error=float(pos.max()),maximum_actual_angle_error=float(ang.max()),within_original_empirical_residual=bool(pos.max()<=.04 and ang.max()<=.035),within_original_time=bool(elapsed[-1]<=2.2+a['body_age_s']+.05),original_passed=a['passed'],scope='Recorded executed brake prefix only. Does not prove any new action, unrecorded future, recursive safety or subsequent arrival.')
result=dict(models=0,integrations=0,rows=witness,one_variable_interventions=interventions,retained_original_certificate=retained,first_fault='fresh zero-command future dynamic bound below .155; static ample; no stale/expiry failure',source_hashes={n:hashlib.sha256((S/n).read_bytes()).hexdigest() for n in ['COMMAND_TUBES.json.gz','physics/NATIVE_TRACE.npz','RESULT.json']})
(O/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
