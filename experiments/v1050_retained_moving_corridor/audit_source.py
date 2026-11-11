"""Fresh-array, native-time interval audit and deterministic mutation checks.

No geometric guidance or cached phase occupancy is trusted by this audit.
This certifies a retained input under the empirical tracking envelope, not a
general CBF/recursive safety theorem or actuator-fault recovery guarantee.
"""
import importlib.abc,sys,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1050_retained_moving_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from kernel import predict,checks,ref,REQUIRED,sha,dump,load
interval=load('v1050_independent_interval',R/'experiments/v1035_signed_timed_input_source/time_geometry.py')
def admit(states,controls,requests,packet,setup,goal,lower):
 cc,upper=checks(states,controls,requests,packet,setup,goal,lower,REQUIRED)
 return all(cc.values()),{k:bool(v)for k,v in cc.items()},upper
def main():
 x=json.loads((O/'INPUT_SOURCE.json').read_text());plan=json.loads((O/'FULL_SOURCE.json').read_text());assert plan['passed']and plan['old_all_native_brake_contract_preserved']is False
 assert set(x['setup']).issuperset({'known','limits','slew_per_second'});ss,uu,rr,mm=predict(x['setup'],x['packet'],plan['actions'],tail=False);assert np.max(abs(ss-np.asarray(plan['state_path'])))<=1e-10;assert np.max(abs(uu-np.asarray(plan['predicted_actuator_controls'])))<=1e-10;assert np.array_equal(rr,np.array(plan['planned_body_requests']));geo=ref._old.Geometry(x['setup']['known'],None);normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];minimum=math.inf;lowers=[]
 for first in range(0,len(ss),512):
  q=ss[first:first+512];t=x['packet']['sim_time']+(first+np.arange(len(q)))*.01;support=interval.interval_support(x['source']['periodic']['vertices'],t-.055,t+.055);a=q[:,2];front=np.c_[np.cos(a),np.sin(a)];left=np.c_[-np.sin(a),np.cos(a)];body=q[:,:2]@normals.T-.44*abs(front@normals.T)-.375*abs(left@normals.T);dynamic=(body-support-.1).max(axis=1);static=geo.clearances(q[:,:3])[0];lower=np.minimum(static,dynamic);lowers.extend(lower);minimum=min(minimum,float(lower.min()))
 valid,cc,upper=admit(ss,uu,rr,x['packet'],x['setup'],np.array(x['goal']),minimum);assert valid
 a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[-1:,:3]);terminal=float(min(a[0],b[0]));assert terminal>=REQUIRED;tail_lower=np.minimum.accumulate(np.array(lowers)[::-1])[::-1];assert(tail_lower>=REQUIRED).all()
 negatives=[]
 def reject(name,s=ss,u=uu,r=rr,lower=minimum,goal=None):
  okay,_,_=admit(s,u,r,x['packet'],x['setup'],np.array(x['goal'])if goal is None else goal,lower);assert not okay,name;negatives.append(name)
 bad=uu.copy();bad[0,0]=100.;reject('actuator_cap',u=bad)
 bad=uu.copy();bad[20,0]=bad[19,0]+1.;reject('actuator_slew',u=bad)
 bad=rr.copy();bad[-1,0]=.08;reject('missing_full_stop_input',r=bad)
 bad=ss.copy();bad[-1,3]=.1;reject('terminal_not_stopped',s=bad)
 bad=ss.copy();bad[200,5]=.3;reject('body_yaw_cap',s=bad)
 reject('clearance_below_original_gate',lower=REQUIRED-1e-9)
 reject('wrong_goal',goal=np.array([-4.,-2.]))
 bad=ss.copy();bad[200,0]=np.nan;reject('nonfinite_state',s=bad)
 reject('missing_recorded_state',s=ss[:-1])
 result=dict(passed=True,checks=cc,native_intervals=len(ss),minimum_independent_timed_raw_m=minimum,terminal_full_cycle_hold_raw_m=terminal,terminal_goal_upper_m=upper,all_retained_suffixes=len(tail_lower),negative_cases_rejected=negatives,full_regeneration_equal=True,source_sha256=sha(O/'INPUT_SOURCE.json'),full_plan_sha256=sha(O/'FULL_SOURCE.json'),models=0,integrations=0,contract=plan['backup_contract'],old_brake_only_contract_preserved=False)
 dump(O/'SOURCE_INDEPENDENT_AUDIT.json',result);plan['retained_suffix_audit']=result;dump(O/'SELECTED_PLAN.json',plan);print(json.dumps(result))
if __name__=='__main__':main()
