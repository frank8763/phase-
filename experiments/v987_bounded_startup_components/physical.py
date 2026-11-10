"""Frozen V984 control; bounded original restore and separately timed stages."""
import importlib.util,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v987_true_t0_factory',R/'experiments/v974_daytime_binding_gate/physical.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def restore_prefix(vehicle,task,expected,commands,deadline,progress):
    count=task['origin_native_tick'];maximum=0.;progress.guard();vehicle.scan()
    for index in range(count):
        progress.guard();assert time.time()<deadline-40,'ROOT_DEADLINE_RESTORING_PREFIX'
        row=commands[index];vehicle._restore_in_step=True;vehicle.step(row[1],row[2],row[5]);vehicle._restore_in_step=False
        for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            value=np.asarray(getattr(vehicle.d,key));reference=expected[key][index]
            if value.size:maximum=max(maximum,float(abs(value-reference).max()))
        assert maximum<=1e-8,'HISTORICAL_PREFIX_STATE_OR_CONTROL_MISMATCH'
        if index%5==0:vehicle.scan()
        if (index+1)%512==0:progress.write('RESTORING_HISTORY',vehicle,maximum_all_state_control_error=maximum)
    progress.guard();progress.write('HISTORY_RESTORED',vehicle,maximum_all_state_control_error=maximum)
    return dict(passed=True,historical_prefix_replay_native=count,maximum_all_state_control_error=maximum,
        global_simulation_time=float(vehicle.d.time),global_native_tick=vehicle.count,no_root_or_time_rewrite=True,
        historical_adapter='V958',new_adapter_not_used_during_history=True)
def create_vehicle(out,task):
    from authority import root_authorized
    from budget import load,model_deadline
    from startup_progress import Progress
    from closure import dump
    root=root_authorized()['deadline_unix'];out=Path(out);record=load(out.parent,task,root);deadline=model_deadline(record)
    progress=Progress(out.parent,task,record);vehicle=None
    assert task['stage']=='component'and task['origin_native_tick']in [6083,7814]
    try:
        vehicle=progress.stage('CANONICAL_INITIALIZATION',lambda:base.create_vehicle(out,task))
        prior=R/'runs/v987_bounded_startup_components/prior_v974'
        commands=json.loads((prior/'physics/BODY_COMMANDS.json').read_text())
        with np.load(prior/'physics/NATIVE_TRACE.npz')as expected:
            proof=progress.stage('HISTORICAL_RESTORE',lambda:restore_prefix(vehicle,task,expected,commands,deadline,progress))
        saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())['rows'][task['fixed_state_index']]
        assert max(abs(np.asarray(vehicle.body())-saved['search_packet']['body']))<=1e-8,'COMPONENT_BODY_NOT_ORIGINAL'
        assert max(abs(vehicle.steering_sample()[:2]-saved['search_packet']['steering']['position']))<=1e-8
        assert abs(vehicle.d.time-task['origin_sim_time'])<=1e-9,'COMPONENT_CLOCK_CHANGED'
        dump(out/'PREFIX_RESTORE.json',proof)
        import mujoco as mj
        from actuation_binding import bind_restored
        progress.stage('ADAPTER_MEMORY_SWITCH',lambda:bind_restored(vehicle,task,out,mj))
        progress.guard();progress.write('FACTORY_RESTORED_READY',vehicle)
    except BaseException as error:
        uncertain=vehicle is None or getattr(vehicle,'_restore_in_step',False)
        failure=dict(error=repr(error),models_initialized=None if vehicle is None else 1,
            historical_restore_native=None if uncertain else vehicle.count,
            completed_native_lower_bound=0 if vehicle is None else vehicle.count,new_branch_native=0,
            new_branch_started=False,replay_of_new_branch_started=False,initialization_total_unknown=vehicle is None)
        if vehicle is not None:
            try:failure['saved_prefix']=vehicle.finish()
            except BaseException as save_error:failure['save_error']=repr(save_error)
        dump(out.parent/'STARTUP_FAILURE.json',failure)
        if out.exists():dump(out/'PREFIX_FAILURE.json',failure)
        raise
    vehicle.component_snapshot=saved['search_packet']['scan'];vehicle.component_prefix_count=task['origin_native_tick']
    return vehicle
replay=base.replay
