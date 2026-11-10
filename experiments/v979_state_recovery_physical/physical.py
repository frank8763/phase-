"""Exact true-t0 factory then original-body-control prefix; no root state writes."""
import importlib.util,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v979_true_t0_factory',R/'experiments/v974_daytime_binding_gate/physical.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def restore_prefix(vehicle, task, expected, commands, deadline):
    count=task.get('origin_native_tick',0);maximum=0.
    vehicle.scan()
    for index in range(count):
        assert time.time()<deadline-40,'ROOT_DEADLINE_RESTORING_PREFIX'
        record=commands[index];vehicle._restore_in_step=True;vehicle.step(record[1],record[2],record[5]);vehicle._restore_in_step=False
        for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            value=np.asarray(getattr(vehicle.d,key));reference=expected[key][index]
            if value.size:maximum=max(maximum,float(abs(value-reference).max()))
        assert maximum<=1e-8,'HISTORICAL_PREFIX_STATE_OR_CONTROL_MISMATCH'
        if index%5==0:vehicle.scan()
    return dict(passed=True,historical_prefix_replay_native=count,maximum_all_state_control_error=maximum,
                global_simulation_time=float(vehicle.d.time),global_native_tick=vehicle.count,no_root_or_time_rewrite=True)

def create_vehicle(out,task):
    vehicle=base.create_vehicle(out,task);origin=task.get('origin_native_tick',0)
    if not origin:return vehicle
    from authority import root_authorized
    deadline=root_authorized()['deadline_unix']
    prior=R/'runs/v979_state_recovery_physical/prior_v974'
    commands=json.loads((prior/'physics/BODY_COMMANDS.json').read_text())
    try:
        with np.load(prior/'physics/NATIVE_TRACE.npz')as data:
            proof=restore_prefix(vehicle,task,data,commands,deadline)
    except BaseException as error:
        failure=dict(error=repr(error),models_initialized=1,historical_restore_native=None if getattr(vehicle,'_restore_in_step',False)else vehicle.count,
                     completed_native_lower_bound=vehicle.count,new_branch_native=0,new_branch_started=False,replay_of_new_branch_started=False)
        try:failure['saved_prefix']=vehicle.finish()
        except Exception as save_error:failure['save_error']=repr(save_error)
        (Path(out)/'PREFIX_FAILURE.json').write_text(json.dumps(failure,indent=2)+'\n')
        raise
    saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())['rows'][task['fixed_state_index']]
    assert max(abs(np.asarray(vehicle.body())-saved['search_packet']['body']))<=1e-8,'COMPONENT_BODY_NOT_ORIGINAL'
    assert max(abs(vehicle.steering_sample()[:2]-saved['search_packet']['steering']['position']))<=1e-8
    assert abs(vehicle.d.time-task['origin_sim_time'])<=1e-9,'COMPONENT_CLOCK_CHANGED'
    vehicle.component_snapshot=saved['search_packet']['scan']
    vehicle.component_prefix_count=origin
    (Path(out)/'PREFIX_RESTORE.json').write_text(json.dumps(proof,indent=2)+'\n')
    return vehicle

replay=base.replay
