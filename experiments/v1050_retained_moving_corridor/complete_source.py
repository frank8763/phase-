"""Compose real-input prefix, finite departure interval, retained moving suffix.

No assertion that braking is safe at every throat state. The changed backup
contract is explicit in the certificate and cannot satisfy the old contract.
"""
import importlib.abc,json,math,sys,time,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1050_retained_moving_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1047_day_relay'))
from kernel import Predictor,PARAMETERS,Geometry,REQUIRED,ref,predict,checks,sha,dump
def main():
 begun=time.monotonic();x=json.loads((R/'runs/v1047_day_relay_20261111/INPUT_SOURCE.json').read_text());fit=json.loads((O/'FIT_ENTRY.json').read_text());assert fit['prefix_qualified'];n=sum(a['ticks']for a in fit['actions']);states=np.load(O/'ENTRY_PREDICTION.npz')['states'];mem=np.load(O/'ENTRY_PREDICTION.npz')['memories'];p=Predictor(x['setup'],dict(state=states[-1].tolist(),last_ctrl=mem[-1,:4].tolist(),integral=float(mem[-1,4]),virtual_rate=.6),PARAMETERS);suffix=[p.state.copy()]
 for request in [[.08,0.,False]]*2400+[[0.,0.,False]]*200:s,u=p.step(*request);suffix.append(s)
 suffix=np.array(suffix);g=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);static=g.static.clearances(suffix[:,:3])[0];normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];a=suffix[:,2];front=np.c_[np.cos(a),np.sin(a)];left=np.c_[-np.sin(a),np.cos(a)];support=suffix[:,:2]@normals.T-.44*abs(front@normals.T)-.375*abs(left@normals.T);rows=[]
 for wait in range(math.ceil(g.period/.01)):
  phases=(g.start+(n+wait+np.arange(len(suffix)))*.01)%g.period;ix=np.minimum((phases/g.bin).astype(int),len(g.edges)-1);dynamic=(support-g.support[ix]-.1).max(axis=1);minimum=float(np.minimum(static,dynamic).min());rows.append(dict(wait_ticks=wait,minimum_suffix_raw_m=minimum,passed=minimum>=REQUIRED))
 dump(O/'DEPARTURE_INTERVALS.json',dict(rows=rows,passing_waits=sum(z['passed']for z in rows),candidate_count=len(rows),models=0));chosen=max(rows,key=lambda z:z['minimum_suffix_raw_m']);base=dict(passed=False,models=0,integrations=0,physical_ready=False,input_source_sha256=sha(R/'runs/v1047_day_relay_20261111/INPUT_SOURCE.json'),backup_contract='RETAINED_FULL_MOVING_SUFFIX_THEN_200_STOP_AND_FULL_CYCLE_HOLD',old_all_native_brake_contract_preserved=False,departure_candidates=len(rows),passing_departures=sum(z['passed']for z in rows),best_departure=chosen,wall_s=time.monotonic()-begun)
 if not chosen['passed']:dump(O/'FULL_SOURCE.json',base);print(json.dumps(base));return
 actions=fit['actions']+([dict(kind='wait',gear=0,target=0.,ticks=chosen['wait_ticks'])]if chosen['wait_ticks']else[])+[dict(kind='move',gear=1,target=0.,ticks=2400),dict(kind='wait',gear=0,target=0.,ticks=200)];ss,uu,rr,mm=predict(x['setup'],x['packet'],actions,tail=False);low=g.complete(ss);cc,upper=checks(ss,uu,rr,x['packet'],x['setup'],np.array(x['goal']),low,REQUIRED);a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[-1:,:3]);terminal=float(min(a[0],b[0]));cc['terminal_full_cycle_hold']=terminal>=REQUIRED;cc['retained_suffix_for_every_native']=low>=REQUIRED;cc['complete_real_packet_prefix']=np.max(abs(ss[:n+1]-states))<=1e-10;cc['all_gear_changes_have_200_stop']=all(i>0 and actions[i-1]['kind']=='wait'and actions[i-1]['ticks']>=200 for i,a in enumerate(actions)if a['kind']=='move'and i>0 and a['gear']!=next((z['gear']for z in reversed(actions[:i])if z['kind']=='move'),a['gear']));cc['navigation_bound']=len(rr)<=40000
 cc={k:bool(v)for k,v in cc.items()};result=dict(base,passed=bool(all(cc.values())),checks=cc,actions=actions,state_path=ss.tolist(),predicted_actuator_controls=uu.tolist(),planned_body_requests=rr.tolist(),minimum_timed_raw_m=low,terminal_full_cycle_hold_raw_m=terminal,terminal_goal_upper_m=upper,analytical_prediction_steps=len(rr),requires_reverse=True,actual_navigation_executed=False,wall_s=time.monotonic()-begun);np.savez_compressed(O/'FULL_PREDICTION.npz',states=ss,controls=uu,requests=rr,memories=mm);dump(O/'FULL_SOURCE.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['actions','state_path','predicted_actuator_controls','planned_body_requests']}))
if __name__=='__main__':main()
