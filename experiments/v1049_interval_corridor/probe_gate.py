"""Counterfactual lane pose diagnostic, never a measured-state certificate."""
import importlib.abc,sys,json,math,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1049_interval_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1047_day_relay'))
from kernel import Predictor,PARAMETERS,Geometry,Expander,REQUIRED,initial,ref,stop_witness

def main():
 assert not(O/'GATE_RESULT.json').exists();x=json.loads((R/'runs/v1047_day_relay_20261111/INPUT_SOURCE.json').read_text());rect=x['setup']['known']['known_rectangles'][9];pose=[float(rect[0]-rect[2]-.45),float(rect[1]+rect[3]+.375+REQUIRED+.03),0.];origin=dict(state=[*pose,0.,0.,0.,0.,0.],last_ctrl=[0.]*4,integral=0.,virtual_rate=.6);p=Predictor(x['setup'],origin,PARAMETERS);states=[p.state.copy()];mem=[np.r_[p.adapter.last,p.adapter.integral]];ctrl=[];requests=[[.08,0.,False]]*2400+[[0.,0.,False]]*200
 for request in requests:s,u=p.step(*request);states.append(s);mem.append(np.r_[p.adapter.last,p.adapter.integral]);ctrl.append(u)
 states=np.asarray(states);mem=np.asarray(mem);geometry=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);full=ref._old.Geometry(x['setup']['known'],x['source']['periodic']);a,b=full.clearances(states[:1,:3]);startfull=float(min(a[0],b[0]));upper=float(np.linalg.norm(states[-1,:2]-x['goal']))+.08;ticks=np.arange(len(states));trials=[];start=time.monotonic()
 for slot in range(200):
  wait=int(round(slot*geometry.period/.01/200));low=geometry.clearances(states[:,:3],ticks+wait,.005);trials.append(dict(slot=slot,wait_ticks=wait,minimum_timed_raw_m=float(low.min()),path_geometry_passed=bool(low.min()>=REQUIRED)))
 good=sorted([r for r in trials if r['path_geometry_passed']],key=lambda r:-r['minimum_timed_raw_m'])[:5];engine=Expander(x['setup']);proofs=[]
 for row in good:
  minimum=math.inf;failed=None
  for i in range(len(states)):
   safe,lower=stop_witness(engine,geometry,states[i],mem[i],row['wait_ticks']+i);minimum=min(minimum,lower)
   if not safe:failed=i;break
  proofs.append(dict(**row,all_native_brake_passed=failed is None,first_failed_native=failed,minimum_brake_raw_m=minimum))
 result=dict(counterfactual_proposal_only=True,actual_source_qualified=False,pose_from_public_static_map=pose,synthetic_stopped_state=origin,original_saved_native=x['packet']['native_tick'],full_cycle_start_hold_raw_m=startfull,terminal_goal_upper_m=upper,phase_candidates=200,path_geometry_passed_count=sum(r['path_geometry_passed']for r in trials),top_five_native_brake_audits=proofs,full_native_gate_candidate_exists=any(r['all_native_brake_passed']for r in proofs)and upper<=.45 and startfull>=REQUIRED,models=0,integrations=0,wall_s=time.monotonic()-start)
 (O/'PHASE_TRIALS.json').write_text(json.dumps(trials,indent=2)+'\n');(O/'GATE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
