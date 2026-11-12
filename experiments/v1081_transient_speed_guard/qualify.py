"""Fixed saved inputs, new coupled prediction and algebraic projection tests."""
import sys,json,importlib.abc,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1081_transient_speed_guard'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();import numpy as np
from kernel import PARAMETERS,Geometry,REQUIRED,checks,ref
sys.path.insert(0,str(C));from transient_model import Predictor,initial
from governor import Adapter,kin,speed_terms,P
REC=R/'records/nav2_v1077_v1078_20261112/v1079_dual_steering_qualification';inp=json.loads((REC/'REMAINDER_INPUT.json').read_text());setup=inp['setup'];packet=inp['packet'];source=inp['source'];rr=np.load(REC/'REMAINDER_SOURCE.npz')['requests'];tasks=json.loads((R/'experiments/v1080_turn_return_remaining/TASKS.json').read_text());t0=json.loads((R/'runs/v1067_causal_replan_brake_reserve_preparation/NORTH_SOUTH_T0_METADATA.json').read_text())['packet']
def rollout(packet,rr,source=None):
 p=Predictor(setup,initial(packet),PARAMETERS);ss=[p.state.copy()];uu=[];ff=[p.front.copy()];projections=0
 for r in rr:
  s,u=p.step(*r);ss.append(s);uu.append(u);ff.append(p.front.copy());projections+=getattr(p.adapter,'last_speed_projection',{}).get('limited',False)
 ss=np.array(ss);uu=np.array(uu);low=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(ss)if source is not None else float(ref._old.Geometry(setup['known'],None).clearances(ss[:,:3])[0].min());cc,upper=checks(ss,uu,rr,packet,setup,np.asarray(setup['case']['goal_xy']),low,REQUIRED)
 if source is None:cc.pop('goal_upper')
 cc={k:bool(v)for k,v in cc.items()};return dict(passed=all(cc.values()),checks=cc,minimum_raw_m=low,goal_upper_m=upper,max_speed=float(abs(ss[:,3]).max()),projections=projections),ss,uu,np.array(ff)
rows=[]
for t in tasks[:2]:
 req=np.vstack([np.tile([.125,0.,0.],(200,1)),np.tile([.125,.125*math.tan(t['target'])/.6,0.],(80,1)),np.tile([.125,0.,0.],(125,1)),np.zeros((2200,3))]);a,ss,uu,ff=rollout(t0,req);a.update(task_id=t['task_id'],return_moving=bool(abs(ff[405]).max()<=.02 and ss[405,3]>=.10));a['passed']=a['passed']and a['return_moving'];rows.append(a)
a,ss,uu,ff=rollout(packet,rr,source);a.update(task_id='remaining3555',net_m=float(np.linalg.norm(ss[-1,:2]-ss[0,:2])));a['passed']=a['passed']and a['net_m']>=1.;rows.append(a);np.savez_compressed(O/'REMAINING_CANDIDATE.npz',states=ss,controls=uu,front_states=ff,requests=rr)
# Teacher-forced projection replays observations only; not physical response.
out=R/'runs/v858_nav2_verified/v1080/remaining3555';z=np.load(out/'physics/NATIVE_TRACE.npz');cmd=np.asarray(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));n=18074;engine=Predictor(setup,initial(packet),PARAMETERS);probes=[]
for i in range(n,len(cmd)):
 qprev=z['qpos'][i-1];vprev=z['qvel'][i-1];engine.front=qprev[setup['steering_qpos_addresses']].copy();engine.front_rate=vprev[setup['steering_qvel_addresses']].copy();engine.adapter.last=(np.array(packet['controller_memory']['last_ctrl'])if i==n else z['ctrl'][i-1,setup['actuator_ids']]).copy();engine.adapter.integral=packet['controller_memory']['integral']if i==n else engine.adapter.integral;
 try:
  u=engine.adapter.compute(*cmd[i,[1,2,3,4,5]]);proof=engine.adapter.last_speed_projection;probes.append(dict(local=i-n+1,limited=proof['limited'],projected_upper=proof['offset']+proof['gain']*proof['common']+P['empirical_one_step_error_reserve'],wheel_common=float(u[2:].mean()),rejected=False))
 except AssertionError as e:
  assert str(e)=='NO_SLEW_LEGAL_SPEED_PROJECTION';probes.append(dict(local=i-n+1,rejected=True,reason=str(e),scope='saved original ungoverned state, not a governed rollout'))
result=dict(passed=all(x['passed']for x in rows),rows=rows,saved_failure_projection=probes,model_scope='fitted observed transient, empirical uncertainty reserve, physical validation pending',models=0,integrations=0,physical_ready=False,old_failure_preserved=True);(O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
