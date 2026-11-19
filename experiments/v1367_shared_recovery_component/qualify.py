"""Saved-data origin, count/permission, controls and unchanged software receipts."""
import ast
import importlib.util
import os
import sys
import time
from types import SimpleNamespace
import numpy as np
from component_context import *
from audit import accounting
from prefix_restore import restore


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    tasks=read(C/'TASKS.json');checks={};old=R/'runs/v1366_canonical_timed_lattice';software=read(old/'software/COMPLETION.json')
    assert software['passed'] and read(old/'software/INDEPENDENT_AUDIT.json')['paired_actual_costmaps_equal']
    assert read(old/'INDEPENDENT_GRAPH_AUDIT.json')['safe_prefix_minimum_m']>=.32
    for method in ['rpp','mppi']:assert sha(C/(method+'_params.json'))==sha(R/'experiments/v1366_canonical_timed_lattice'/(method+'_params.json'))
    assert all(t['reference_path']==tasks[0]['reference_path'] and t['causal_ball']==tasks[0]['causal_ball'] and t['origin_body']==tasks[0]['origin_body'] for t in tasks)
    checks['same_safe_path_and_actual_software_params_pair_reused']=True
    for t in tasks:task_check(t)
    bad=dict(tasks[0]);bad['origin_native_tick']=0
    try:task_check(bad)
    except AssertionError:pass
    else:raise AssertionError('ORIGIN_TAMPER_ACCEPTED')
    checks['unregistered_or_zero_origin_task_refused']=True
    assert not (O/'USER_WINDOW.json').exists() and not (O/'APPROVAL.json').exists() and not (O/'ROUND_WINDOW.json').exists()
    try:authorize(tasks[0],{})
    except (AssertionError,FileNotFoundError):pass
    else:raise AssertionError('PHYSICAL_AUTHORITY_NOT_DENIED')
    checks['models_denied_without_new_human_window']=True
    assert accounting(0,15105,False)==dict(actual_total_native=0,historical_prefix_replay_native=0,new_component_native=0)
    assert accounting(15105,15105,False)==dict(actual_total_native=15105,historical_prefix_replay_native=15105,new_component_native=0)
    assert accounting(15305,15105,False)==dict(actual_total_native=15305,historical_prefix_replay_native=15105,new_component_native=200)
    assert accounting(14000,15105,True)==dict(actual_total_native=None,historical_prefix_replay_native=None,new_component_native=None)
    assert accounting(16000,15105,True)==dict(actual_total_native=None,historical_prefix_replay_native=15105,new_component_native=None)
    checks['prefix_branch_full_and_unknown_counts_separate']=True
    task=tasks[0];prior=Path(task['prior_raw']);journal=read(prior/'APPLIED_JOURNAL.json');setup=read(prior/'physics/SETUP.json')
    with np.load(prior/'physics/NATIVE_TRACE.npz') as z:expected={k:z[k].copy() for k in z.files}
    # This peer is EXPLICIT recorded-data metadata, not a simulated/restored
    # physical vehicle. Test the actual prefix wrapper boundary and assertions.
    fixture=O/'metadata_prefix_fixture';fixture.mkdir(exist_ok=True);dump(fixture/'SETUP.json',setup)
    peer=SimpleNamespace(out=fixture,count=0,d=SimpleNamespace(time=0.),adapter=SimpleNamespace(last=np.array(journal[0]['last_ctrl']),integral=journal[0]['integral']),scan=lambda:None,body=lambda:task['origin_body'])
    def step(v,w,phase):
        i=peer.count;row=journal[i];assert [v,w]==row['upstream_request'][:2] and phase=='HISTORICAL_PREFIX'
        for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:setattr(peer.d,key,expected[key][i])
        peer.count+=1;peer.d.time=float(expected['time'][i]);nextrow=journal[peer.count]
        peer.adapter.last=np.asarray(nextrow['last_ctrl']);peer.adapter.integral=nextrow['integral']
    proof=restore(peer,task,step,time.time()+400);assert proof['passed'] and peer.count==15105
    checks['actual_prefix_wrapper_saved_metadata_positive']=True
    tree=ast.parse((C/'prefix_restore.py').read_text())
    assert not any(isinstance(n,(ast.Assign,ast.AugAssign)) and any(isinstance(t,ast.Attribute) and ast.unparse(t).startswith('vehicle.d.') for t in (n.targets if isinstance(n,ast.Assign) else [n.target])) for n in ast.walk(tree))
    checks['prefix_wrapper_has_no_physical_state_or_clock_assignment']=True
    # Full saved algebra reconstruction with metadata-only Adapter.__new__.
    sys.path.insert(0,str(R/'experiments/v993_steering_transient_diagnosis'))
    from fixture import make
    spec=importlib.util.spec_from_file_location('same_signed_allocator_no_model',R/'experiments/v1035_signed_timed_input_source/signed_control.py');control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control);owner=make(control.Adapter,setup);error=0.
    for i,row in enumerate(journal):
        error=max(error,float(abs(owner.last-row['last_ctrl']).max()),abs(owner.integral-row['integral']))
        u=owner.compute(*row['request'][:2],*row['body'][3:],False);error=max(error,float(abs(u-expected['ctrl'][i,setup['actuator_ids']]).max()))
    assert error<=1e-8;checks['full_original_saved_control_algebra_reconstructed']=True
    assert not any(k in sys.modules for k in ['mujoco','vehicle','torch'])
    checks['no_model_imports_or_constructors_executed']=True
    proof=dict(passed=all(checks.values()),checks=checks,source_saved_native=len(journal),control_reconstruction_error=error,
        metadata_prefix_steps_not_physical_integrations=15105,models=0,physical_native=0,new_navigation_trials=0,
        complete_dynamic_route_qualified=False,scope='short shared recovery component preparation only',wall_s=time.monotonic()-begin)
    dump(O/'QUALIFICATION.json',proof);print(json.dumps(proof))


if __name__=='__main__':main()
