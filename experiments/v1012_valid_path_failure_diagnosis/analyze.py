"""Saved V1009 diagnosis only; no new vehicle, navigation, forecast or replay."""
import gzip,hashlib,importlib.abc,importlib.util,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1012_valid_path_failure_diagnosis';S=O/'saved';REC=R/'records/nav2_v1009_20261110'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('SAVED_DIAGNOSIS_ONLY '+name)
sys.meta_path.insert(0,NoModel())
sys.path[:0]=[str(R/'experiments'/p)for p in ['v1009_explicit_checker_navigation','v1004_planned_input_navigation','v1003_causal_recovery_execution','v891_dynamic_consistency_software','v887_exact_lidar_software','v864_diagnosis','v791_coherent_global_reference']]
def read(p):return json.loads(Path(p).read_text())
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    # In-memory path translation only: archived absolute profile paths resolve to
    # their SHA-identical restored bytes. Original metadata/source stays immutable.
    module=load('v1012_original_saved_input_auditor',R/'experiments/v1004_planned_input_navigation/audit.py')
    prefix=str(R/'runs/v858_nav2_verified/v1009/main_we')
    module.Path=lambda p:Path(str(p).replace(prefix,str(S),1))if str(p).startswith(prefix)else Path(p)
    task=read(R/'experiments/v1009_explicit_checker_navigation/TASKS.json')[0]
    setup=read(S/'physics/SETUP.json')
    with np.load(S/'physics/NATIVE_TRACE.npz')as z:q=z['qpos'];v=z['qvel'];ctrl=z['ctrl'][:,setup['actuator_ids']]
    body=module.physical_body(q,v)
    # Do not relax or relabel the frozen auditor's bitwise predictor assertion.
    # Report its 6.94e-17 numerical reconstruction mismatch separately, and check
    # measured tracking/inputs directly without upgrading original acceptance.
    from plan import predict
    timeline=read(S/'PROFILE_EXECUTION.json');commands=read(S/'physics/BODY_COMMANDS.json');reports=[]
    for item in timeline['profiles']:
        p=S/Path(item['path']).name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==item['sha256']
        record=json.loads(raw);plan=record['plan'];states,controls,requests=predict(setup,plan['initial'],plan['edge_targets'])
        state_error=float(abs(states-np.asarray(plan['state_path'])).max());control_error=float(abs(controls-np.asarray(plan['predicted_actuator_controls'])).max())
        start,end=item['start_native_tick'],item['end_native_tick'];actual=np.vstack([body[start-1],body[start:end]])
        expected=np.asarray(plan['state_path']);pe=np.linalg.norm(actual[:,:2]-expected[:,:2],axis=1);delta=actual[:,2]-expected[:,2];ae=abs(np.arctan2(np.sin(delta),np.cos(delta)))
        progress=float(np.linalg.norm(body[start-1,:2]-task['goal_xy'])-np.linalg.norm(body[end-1,:2]-task['goal_xy']))
        exact_requests=requests==plan['planned_body_requests']and all(commands[start+j][1:3]+[commands[start+j][5]]==req for j,req in enumerate(requests))
        stopped=np.linalg.norm(v[end-50:end,:2],axis=1).max()<=.03 and abs(v[end-50:end,5]).max()<=.03 and abs(v[end-50:end][:,setup['steering_qvel_addresses']]).max()<=.03
        tracking=bool(pe.max()<=.04 and ae.max()<=.035 and progress>=.4 and stopped and requests[-200:]==[[0.,0.,False]]*200)
        assert exact_requests and tracking
        reports.append(dict(profile_id=item['profile_id'],measured_tracking_and_progress_gates=tracking,complete_native_inputs_exact=exact_requests,
            actual_progress_m=progress,maximum_position_error_m=float(pe.max()),maximum_heading_error_rad=float(ae.max()),
            frozen_bitwise_predictor_reconstruction_passed=bool(np.array_equal(states,np.asarray(plan['state_path']))and np.array_equal(controls,np.asarray(plan['predicted_actuator_controls']))),
            maximum_predictor_state_reconstruction_error=state_error,maximum_predictor_control_reconstruction_error=control_error))
    from tube_audit import audit_tubes
    tube=audit_tubes(S)
    f=read(S/'COMMAND_OBSERVATION_FAULT.json');packet=f['packet'];age=f['checked_at']-packet['body_measured_at']
    profiles=read(S/'PROFILE_EXECUTION.json');rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()))
    accepted=[x for x in rows if x['proof']['passed']];last=max(x['packet']['native_tick']for x in accepted)
    assert .05<age<=.2 and packet['profile_status']['released_id']==2
    assert last<profiles['profiles'][1]['end_native_tick'],'FAULT_WAS_NOT_FIRST_POST_PROFILE_ADMISSION'
    n=read(S/'RESULT.json');replay=read(S/'physics/REPLAY.json')
    result=dict(models=0,new_integrations=0,new_physical_replays=0,original_navigation_status='NOT_PASSED',original_independent_audit_NOT_PASSED_preserved=True,
        physical_summary=dict(native=n['actual_native'],own_full_replay=n['replay_native'],private=n['private_native'],minimum_actual_clearance_m=n['minimum_actual_clearance_m'],bad_contacts=n['bad_contacts'],goal_remaining_m=n['goal_distance_m'],travel_after_actual_detection_m=n['actual_travel_after_detection_m'],full_replay=replay),
        recovered_profiles=reports,strict_frozen_additional_input_audit_not_passed=True,
        original_diagnostic_attempt_error="Frozen own_inputs bitwise state reconstruction assertion failed on first profile; numerical difference6.938893903907228e-17, controls0. Preserved without changing acceptance.",
        command_tube_audit=tube,first_fault=dict(error=f['error'],body_age_s=age,body_age_gate_s=.05,body_tick=packet['native_tick'],released_profile=packet['profile_status'],last_accepted_normal_body_tick=last,raw_wanted_not_reached=f['raw_wanted']is None),
        source_finding='supervise clears retained_proof and profile_owner before restarting normal action; first post-second-profile callback had 53.44ms body age and no newly accepted normal proof. Stale-proposal deferral requires an old accepted proof, so the gate correctly stopped.',
        unresolved='Exact callback scheduling/serialization cause of this 53.44ms gap was not separately instrumented; not attributed uniquely to vehicle tracking or planner.',
        proposed_next_source_work='Atomic stopped handoff: stay under completed-profile stop ownership until fresh measured state and a newly admitted zero-speed tube are acknowledged; then release normal control. Preserve50ms body gate and original stopping/clearance/ownership contracts; saved red/green software proof required before any new physical approval.')
    (REC/'V1012_SAVED_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(models=0,profile_progress=[x['actual_progress_m']for x in reports],profile_position_error=[x['maximum_position_error_m']for x in reports],profile_heading_error=[x['maximum_heading_error_rad']for x in reports],body_age_s=age,tube_failed_checks=[k for k,v in tube['checks'].items()if not v],last_normal_tick=last),indent=2))
if __name__=='__main__':main()
