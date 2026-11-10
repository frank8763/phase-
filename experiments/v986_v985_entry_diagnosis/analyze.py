"""Closed-run startup cause/accounting reconstruction; zero new model work."""
import gzip,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v986_v985_entry_diagnosis'
def read(n):return json.loads((O/n).read_text())
def main():
    receipt=read('RESTORE_RECEIPT.json')
    for row in receipt['files']:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    result=read('RESULT.json');complete=read('COMPLETION.json');timing=read('RUNTIME_TIMING.json');account=read('NATIVE_ACCOUNTING.json')
    ready=read('NATIVE_READY.json');stop=read('PARENT_STOP_REQUEST.json');binding=read('physics/ACTIVE_ADAPTER_BINDING.json');prefix=read('physics/PREFIX_RESTORE.json');replay=read('physics/REPLAY.json')
    feedback=json.loads(gzip.decompress((O/'physics/YAW_FEEDBACK.json.gz').read_bytes()));repro=read('PARENT_WAIT_REPRODUCTION.json')
    checks=dict(first_parent_error_restore_timeout=complete['error']['error']=="AssertionError('CANONICAL_STATE_RESTORE_TIMEOUT')",
        actual_parent_wait_bug_reproduced=repro['passed'],factory_restore_exceeded_parent120=timing['summaries']['factory_initialize']['inclusive_wall_s']>120.,
        native_completed_original_origin=ready['native_tick']==account['historical_restore_native']==prefix['historical_prefix_replay_native']==6083,
        exact_historical_state_control=prefix['passed']and prefix['maximum_all_state_control_error']==0.,
        active_adapter_switch_reached=binding['passed']and binding['native_tick']==6083 and binding['physical_state_unchanged'],
        parent_stop_preceded_native_ready=stop['requested_monotonic']<ready['at'],
        new_branch_exactly_zero=result['new_branch_native']==account['new_branch_native_exact']==account['native_calls_completed']==0,
        no_new_controller_proofs=feedback==[],no_arm_or_ros_action=result['armed_at']is None and not result['ros_action']and not receipt['ros_console_in_original_archive'],
        replay_of_history_exact=replay['passed']and replay['replay_native']==6083 and replay['maximum_qpos_qvel_ctrl_mocap_error']==0.,
        graceful_stop_not_forced=not read('WORKER_CLOSURE.json')['forced_process_groups'],original_guard_restored=complete['guard_restored'])
    assert all(checks.values())
    factory=timing['summaries']['factory_initialize']
    diagnosis=dict(passed=True,checks=checks,models_during_diagnosis=0,integrations_during_diagnosis=0,
        original_outcome='V985_NOT_PASSED',failure_class='PARENT_CANONICAL_RESTORE_WAIT_TIMEOUT_BEFORE_ARM',
        exact_counts=dict(vehicle_tasks_initialized=1,historical_restore_native=6083,new_branch_native=0,whole_own_trace_replay_native=6083,
            private_native=0,second_component_unexecuted=True,new_navigation_trials=0,new24=0),
        primary_error=complete['error']['error'],secondary_errors=['ROS_RESULT.json absent because ROS was never launched','Actuation audit requires new rows but this prefix has exactly zero new rows'],
        source='experiments/v985_rear_yaw_components/launch_one.py:24-28',parent_wait_cap_s=120.,
        observed_factory_and_restore_wall_s=factory['inclusive_wall_s'],observed_factory_and_restore_thread_cpu_s=factory['cpu_at_maximum_s'],
        ready_after_parent_stop_s=ready['at']-stop['requested_monotonic'],
        warmup_vs_history_vs_scheduler_separately_identified=False,
        historical_prefix_minimum_clearance_m=result['minimum_actual_clearance_m'],historical_bad_contacts=result['bad_contacts'],
        new_feedback_effect_measured=False,new_controller_tracking_passed=False,
        conclusion='Parent readiness budget expired before a successfully restored original origin became ready. Frozen V984 was bound but never drove. This run cannot judge its physical benefit or failure. Source preparation missed this slow-restoration startup case.',
        next_scope='Operational startup/restore budgeting, progress and pre-ARM failure reporting only; freeze V984/reference/model/safety limits. Same two fixed components only after new entry qualifications and a new explicit bounded window.',
        no_new_physical_authority=True)
    (O/'DIAGNOSIS.json').write_text(json.dumps(diagnosis,indent=2)+'\n')
    print(json.dumps(diagnosis))
if __name__=='__main__':main()
