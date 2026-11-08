"""Saved evidence only. Async navigation repeats and exact own-control replay are distinct."""
import json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from audit_result import audit as original_audit
def audit(task):
 result=original_audit(task);result['scope']='V875_REGISTERED_NOMINAL_DEVELOPMENT_OR_CONFIRMATION';result['case_id']=task['case_id'];result['dynamic']=task['dynamic']
 out=Path(task['output'])
 if task['dynamic'] and result.get('evidence_passed'):
  native=json.loads((out/'RESULT.json').read_text());plans=json.loads((out/'PLANS.json').read_text());d=native.get('first_actor_detection');after=[]if d is None else [p for p in plans if p['at']>=native['armed_at']+d['native_tick']*.01]
  result['dynamic_reference_after_actual_detection']=bool(after);result['dynamic_reference_update_count']=len(after)
  result['functional_passed']=result['functional_passed']and bool(after);result['passed']=result['passed']and bool(after)
 (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
def repeat_check(baseline,repeat):
 b=Path(baseline);r=Path(repeat);bs=json.loads((b/'physics/SETUP.json').read_text());rs=json.loads((r/'physics/SETUP.json').read_text())
 initial_b=np.load(b/'physics/INITIAL_STATE.npz')['state'];initial_r=np.load(r/'physics/INITIAL_STATE.npz')['state']
 initial_error=float(np.max(abs(initial_b-initial_r)))if initial_b.shape==initial_r.shape else None
 audits=[json.loads((p/'INDEPENDENT_AUDIT.json').read_text())for p in [b,r]];arrays=[np.load(p/'physics/NATIVE_TRACE.npz')for p in [b,r]];n=min(len(a['time'])for a in arrays)
 metrics=[]
 for p,a in zip([b,r],arrays):
  raw=json.loads((p/'RESULT.json').read_text());xy=np.vstack([bs['case']['start_xy'],a['qpos'][:,:2]]);metrics.append(dict(native=len(a['time']),sim_s=float(a['time'][-1]),path_m=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),goal_m=raw['goal_distance_m'],min_clearance_m=raw['minimum_actual_clearance_m'],own_control_replay_max_error=raw['replay']['maximum_qpos_qvel_ctrl_mocap_error']))
 passed=bs==rs and initial_error is not None and initial_error<=1e-8 and all(a['passed']for a in audits)
 return dict(passed=passed,same_complete_setup=bs==rs,initial_state_max_error=initial_error,both_functional_safe_arrivals=all(a['passed']for a in audits),metrics=metrics,prefix_same_native_time_qpos_max_difference=float(np.max(abs(arrays[0]['qpos'][:n]-arrays[1]['qpos'][:n]))),exact_navigation_trajectory_claim=False,repeat_contract='Independent same-config full closed-loop rerun; equal initial state/model and both safe arrivals. Async ROS commands may differ; each own executed control replay must remain <=1e-8.')
