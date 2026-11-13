"""Saved native evidence audit only. No MuJoCo or physical construction."""
import sys,json,math,hashlib,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('AUDIT_NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));sys.path.insert(0,str(C))
import numpy as np,stop
from kernel import load,virtual
def audit(O):
    task=json.loads((O/'TASK.json').read_text());out=Path(task['output']);a=out/'physics';old=R/'runs/v858_nav2_verified/v1090/main_west_east/physics'
    result=json.loads((out/'RESULT.json').read_text());setup=json.loads((a/'SETUP.json').read_text());inp=json.loads((out/'ACTUAL_EXIT_INPUT.json').read_text());exit=json.loads((out/'CERTIFIED_EXIT.json').read_text())
    contract=load('audit_exit_scene',R/'experiments/v1089_route_scene_contract/contract.py');contract.verify_saved(a,task)
    with np.load(a/'NATIVE_TRACE.npz')as z:trace={key:z[key]for key in z.files}
    with np.load(old/'NATIVE_TRACE.npz')as z:prior={key:z[key]for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    prefix=max(float(abs(trace[k][:24535]-v).max())if v.size else 0. for k,v in prior.items())
    proof,states,controls,requests=stop.plan(setup,inp['packet'],inp['source'])
    with np.load(out/'CERTIFIED_EXIT_PLAN.npz')as z:
        exact=all(np.max(abs(z[k]-v))<=1e-10 for k,v in [('states',states),('controls',controls),('requests',requests)])
    commands=np.asarray(json.loads((a/'BODY_COMMANDS.json').read_text()));ids=setup['actuator_ids']
    from prediction import Predictor,initial
    from kernel import PARAMETERS
    from braking_reserve import signed
    meta=json.loads((old.parent/'INITIAL_METADATA.json').read_text())
    engine=Predictor(setup,initial(meta['packet']),PARAMETERS)
    engine.adapter.__class__=signed.Adapter
    engine.adapter.last=np.zeros(4);engine.adapter.integral=0.
    control_error=0.
    for command,actual in zip(commands,trace['ctrl'][:,ids]):
        rebuilt=engine.adapter.compute(*command[[1,2,3,4,5]])
        control_error=max(control_error,float(abs(rebuilt-actual).max()))
    slew=float((abs(np.diff(np.vstack([np.zeros(len(ids)),trace['ctrl'][:,ids]]),axis=0))-np.array(setup['slew_per_second'])*.01).max())
    bounds=np.array(setup['limits']);ctrl=trace['ctrl'][:,ids]
    errors=np.zeros(3);speed=0.;yaw=0.
    for j,i in enumerate(range(24535,26735)):
        q=trace['qpos'][i];v=trace['qvel'][i]
        angle=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
        difference=angle-states[j+1,2]
        steering=virtual(q[setup['steering_qpos_addresses']])
        errors=np.maximum(errors,[np.linalg.norm(q[:2]-states[j+1,:2]),abs(math.atan2(math.sin(difference),math.cos(difference))),abs(steering-states[j+1,6])])
        speed=max(speed,abs(v[0]*math.cos(angle)+v[1]*math.sin(angle)));yaw=max(yaw,abs(v[5]))
    original=json.loads((out/'ORIGINAL_REJECTION.json').read_text())
    checks=dict(component_result=result['passed']and not result['navigation_passed'],
        full_length=len(commands)==len(trace['qpos'])==26735,
        history_full_state_ctrl_mocap=prefix<=1e-8,
        original_proposal_rejected=not original['passed']and not original['checks']['full_raw_geometry'],
        independent_stop_proof=proof==exit['proof']and proof['passed']and exact,
        actual_full_stop_requests=np.array_equal(commands[24535:,[1,2,5]],np.zeros((2200,3))),
        actual_control_full_slew=slew<=1e-8,
        full_actual_controller_reconstruction=control_error<=1e-8,
        actual_control_bounds=bool(np.all(ctrl>=bounds[:,0]-1e-8)and np.all(ctrl<=bounds[:,1]+1e-8)),
        actual_stop_tracking=bool(np.all(errors<=[.04,.035,.015])),
        actual_stop_speed_yaw=speed<=.13 and yaw<=.16,
        actual_full_geometry=bool(np.min(trace['clearance'])>=.15-1e-8 and np.min(trace['self_margin'])>=-1e-10 and result['physical']['bad_contacts']==0),
        actual_terminal_stop=bool(np.linalg.norm(trace['qvel'][-1,:2])<=.03 and abs(trace['qvel'][-1,5])<=.03 and exit['executed_native']==2200 and exit['completed']),
        full_own_replay=result['replay']['passed']and result['own_replay_native']==26735)
    checks={k:bool(v)for k,v in checks.items()}
    answer=dict(passed=all(checks.values()),scope='EXIT_COMPONENT_NOT_ROUTE',checks=checks,
        history_error=prefix,maximum_exit_tracking=errors.tolist(),maximum_control_slew_excess=slew,
        maximum_controller_reconstruction_error=control_error,
        minimum_actual_clearance_m=float(trace['clearance'].min()),final_translation_speed_m_s=float(np.linalg.norm(trace['qvel'][-1,:2])),
        models=0,integrations=0)
    (out/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(answer,indent=2)+'\n');return answer
if __name__=='__main__':
    answer=audit(Path(sys.argv[1]));print(json.dumps(answer),flush=True);sys.exit(0 if answer['passed']else 1)
