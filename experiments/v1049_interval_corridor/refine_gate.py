"""Finite public-map lane proposals and integer-native departure intervals."""
import importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1049_interval_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1047_day_relay'))
from kernel import Predictor,PARAMETERS,Geometry,Expander,REQUIRED,ref,stop_witness
N=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]

def main():
 assert not(O/'LANE_INTERVAL_RESULT.json').exists();x=json.loads((R/'runs/v1047_day_relay_20261111/INPUT_SOURCE.json').read_text());rect=x['setup']['known']['known_rectangles'][9];entryx=float(rect[0]-rect[2]-.45);basey=float(rect[1]+rect[3]+.375+REQUIRED);p=Predictor(x['setup'],dict(state=[entryx,basey+.03,0.,0.,0.,0.,0.,0.],last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);ss=[p.state.copy()];mm=[np.r_[p.adapter.last,p.adapter.integral]]
 for request in [[.08,0.,False]]*2400+[[0.,0.,False]]*200:s,u=p.step(*request);ss.append(s);mm.append(np.r_[p.adapter.last,p.adapter.integral])
 ss=np.asarray(ss);mm=np.asarray(mm);engine=Expander(x['setup']);g=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);brake_x=[]
 for s,m in zip(ss,mm):
  q,u,z=engine.expand(s,m,np.array([0.]),200,np.array([0.]));assert abs(q[0,:,2]).max()<=1e-10;brake_x.append(np.r_[s[0],q[0,:,0]])
 brake_x=np.asarray(brake_x);times=np.arange(len(ss))[:,None]+np.arange(201)[None,:];shape=.44*abs(N[:,0])+.375*abs(N[:,1]);results=[];start=time.monotonic()
 for extra in [.03,.02,.01]:
  y=basey+extra;states=ss.copy();states[:,1]=y;static=float(g.static.clearances(np.c_[brake_x.ravel(),np.full(brake_x.size,y),np.zeros(brake_x.size)])[0].min());coarse=[]
  for slot in range(200):
   wait=int(round(slot*g.period/.01/200));minimum=float(g.clearances(states[:,:3],np.arange(len(states))+wait,.005).min());coarse.append(dict(slot=slot,wait_ticks=wait,minimum_path_raw_m=minimum))
  promising=[z for z in coarse if z['minimum_path_raw_m']>=REQUIRED];waits=sorted(set((z['wait_ticks']+d)%round(g.period/.01)for z in promising for d in range(-10,11)));audits=[]
  for wait in waits:
   phases=(g.start+(times+wait)*.01)%g.period;ix=np.minimum((phases/g.bin).astype(int),len(g.edges)-1);lower=np.full(brake_x.shape,-np.inf)
   for k,n in enumerate(N):lower=np.maximum(lower,brake_x*n[0]+y*n[1]-shape[k]-.1-g.support[ix,k])
   minimum=min(static,float(lower.min()));audits.append(dict(wait_ticks=wait,minimum_all_native_brake_raw_m=minimum,passed=minimum>=REQUIRED))
  best=max(audits,key=lambda z:z['minimum_all_native_brake_raw_m'])if audits else None
  row=dict(extra_reference_offset_m=extra,entry_pose=[entryx,y,0.],coarse_path_pass_count=len(promising),fine_wait_candidates=len(waits),best=best,full_cycle_start_hold_raw_m=float(min(a[0]for a in ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[:1,:3]))));results.append(row)
  (O/('LANE_'+str(extra)+'.json')).write_text(json.dumps(dict(coarse=coarse,all_native_brake_audits=audits),indent=2)+'\n')
  if best and best['passed']:
   exact=math.inf;end_pose=None
   for i,s in enumerate(states):safe,minimum=stop_witness(engine,g,s,mm[i],best['wait_ticks']+i);assert safe;exact=min(exact,minimum)
   assert abs(exact-best['minimum_all_native_brake_raw_m'])<=1e-10;row['independent_all_native_stop_minimum']=exact;row['independent_all_native_stops']=len(states);row['terminal_goal_upper_m']=float(np.linalg.norm(states[-1,:2]-x['goal']))+.08
 result=dict(counterfactual_proposals_only=True,actual_prefix_still_required=True,full_actual_source_qualified=False,lanes=results,any_complete_lane_and_native_brake_passed=any(z.get('independent_all_native_stops')for z in results),models=0,integrations=0,required_raw_clearance_m=REQUIRED,wall_s=time.monotonic()-start)
 (O/'LANE_INTERVAL_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
