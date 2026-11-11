"""Saved-only independent original-controller reconstruction and full native gates."""
import importlib.util,json,sys,math
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path[:0]=[str(C),str(R/'experiments/v1023_dense_input_route')]
from whole_input import Predictor,PARAMETERS
from geometry_model import REQUIRED

def audit(task):
 out=Path(task['output']);result=json.loads((out/'RESULT.json').read_text());checks={};metrics={}
 if not result.get('evidence_saved'):return dict(passed=False,error='EVIDENCE_NOT_SAVED',models=0)
 if not(out/'physics/NATIVE_TRACE.npz').exists():return dict(passed=False,error='NO_COMPLETED_NATIVE_TRACE',models=0)
 setup=json.loads((out/'physics/SETUP.json').read_text());d=np.load(out/'physics/NATIVE_TRACE.npz');commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());n=len(commands)
 p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);maximum=0.
 for command,actual in zip(commands,d['ctrl']):
  _,v,w,mv,mw,stale=command;u=p.adapter.compute(v,w,mv,mw,stale);maximum=max(maximum,float(abs(u-actual[setup['actuator_ids']]).max()))
 qv=d['qvel'];limits=np.asarray(setup['limits']);ctrl=d['ctrl'][:,setup['actuator_ids']];rates=np.asarray(setup['slew_per_second'])*.01
 checks.update(all_native_and_commands_accounted=n==result['navigation_native']==len(d['qpos']),native_controller_reconstruction=maximum<=1e-10,
  full_native_clearance=float(d['clearance'].min())>=.15-1e-8,full_self_containment=float(d['self_margin'].min())>=-1e-10,
  legal_actual_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all()),
  no_bad_contacts=result['physical']['bad_contacts']==0,actual_own_replay=result.get('replay',{}).get('passed')is True and result.get('own_replay_native')==n)
 goal=float(np.linalg.norm(d['qpos'][-1,:2]-task['goal_xy']));stopped=bool(np.linalg.norm(qv[-50:,:2],axis=1).max()<=.03 and abs(qv[-50:,5]).max()<=.03 and abs(qv[-50:][:,setup['steering_qvel_addresses']]).max()<=.03)
 checks['actual_arrival_and_stop']=goal<=.45 and stopped
 if task['dynamic']:
  ep=out/'DYNAMIC_EXECUTION.json';discovery=out/'DISCOVERY_STOP_AND_OBSERVE.json';checks['complete_discovery_stop_full_dynamic_route']=ep.exists()and discovery.exists()
  if discovery.exists():
   r=json.loads(discovery.read_text());checks['causal_first_discovery_present']=r['first_causal_scan']is not None
  checks['actual_dynamic_goal_after_detection']=result.get('passed')is True
 else:checks['complete_static_route']=json.loads((out/'STATIC_EXECUTION.json').read_text())['completed']
 metrics.update(native_steps=n,maximum_actual_controller_reconstruction_error=maximum,minimum_native_clearance_m=float(d['clearance'].min()),goal_distance_m=goal)
 if task['dynamic']and(out/'DYNAMIC_COMPLETE_PLAN.json').exists():
  plan_record=json.loads((out/'DYNAMIC_COMPLETE_PLAN.json').read_text());source=plan_record['source'];source_tick=plan_record['packet']['native_tick']
  import sys;sys.path.insert(0,str(R/'experiments/v1020_terminal_two_route_development'));from cycle_backup import cycle_upper
  bounds=cycle_upper(source['periodic'])+1e-6;normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];actual=d['mocap_pos'][source_tick:,setup['actor']['mocap_id'],:2]
  checks['all_actual_future_actor_centers_covered']=bool((actual@normals.T<=bounds+1e-8).all())
  checks['declared_scene_binding']=json.loads((out/'physics/DECLARED_SCENE_BINDING.json').read_text())['passed']
 proof=dict(passed=all(checks.values())and result['passed'],checks=checks,metrics=metrics,models=0,integrations=0,qualification_scope='actual full route only; no statistical confirmation')
 (out/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');return proof
