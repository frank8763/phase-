"""Read-only experiment accounting and source-level fairness/readiness audit."""
import ast
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    started=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes()
    pointer=read(R/'CURRENT_EXPERIMENT.json')
    assert pointer['status']=='REVIEW_PENDING' and pointer['active_run'] is None
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    versions=['v1346_measured_gear_handoff','v1347_cusp_segment_execution','v1348_recoverable_tracking']
    timing=[]
    for version in versions:
        completion=read(R/'runs'/version/'COMPLETION.json')
        assert completion['closed'] and not completion['passed']
        tasks=[]
        for row in completion['results']:
            n=row['native'];m=row['monitor']
            tasks.append(dict(task=row['task'],stage=row['stage'],passed=row['passed'],
                actual=n['new_actual_native'],own_replay=n['own_replay_native'],
                simulated_actual_s=n['new_actual_native']*.01,
                task_monitor_wall_s=m['wall_s'],native_worker_wall_s=n['wall_s'],
                ros_worker_wall_s=row['ros']['wall_s']))
        timing.append(dict(version=version,tasks=tasks,
            summed_monitor_wall_s=sum(x['task_monitor_wall_s'] for x in tasks),
            static_pair_monitor_s=sum(x['task_monitor_wall_s'] for x in tasks if x['stage']=='static'),
            dynamic_monitor_s=sum(x['task_monitor_wall_s'] for x in tasks if x['stage']=='dynamic')))
    raw=R/'runs/v858_nav2_verified/v1348/rpp_async_default_dynamic_main'
    plans=read(raw/'CAUSAL_ROUTE_RECORDS.json')
    search_wall=sum(x['wall_s'] for x in plans)
    performance=read(R/'runs/v1350_bounded_complete_search/ISOLATED_EQUIVALENT_TIMING.json')
    old_mean=sum(x['original_numpy_wall_s'] for x in performance['rows'])/3
    new_mean=sum(x['compiled_wall_s'] for x in performance['rows'])/3
    latest=timing[-1]
    # Accounting estimate only: changing speed changes observations/decisions,
    # so subtracting search time is not a forecast of closed-loop completion.
    estimate=dict(recorded_planning_attempts=len(plans),recorded_planning_wall_s=search_wall,
        recorded_dynamic_monitor_s=latest['dynamic_monitor_s'],
        planning_wall_fraction=search_wall/latest['dynamic_monitor_s'],
        saved_input_mean_old_s=old_mean,saved_input_mean_new_s=new_mean,
        mean_kernel_ratio=old_mean/new_mean,
        nominal_cost_for10_fast_requests_s=10*new_mean,
        hypothetical_saved_time_same10decisions_s=search_wall-10*new_mean,
        caveat='Accounting only; no new closed-loop run and changed decisions may change all durations')
    original=read(R/'experiments/v1281_partial_reconnection_fixed24/TASK_main_slot01.json')
    baseline=next(x for x in read(R/'experiments/v1348_recoverable_tracking/TASKS.json') if x['stage']=='dynamic' and x['role']=='main')
    keys=['case_id','seed','phase','dynamic','goal_xy','goal_yaw','start_xy','start_yaw','course_id']
    same_task={k:original[k]==baseline[k] for k in keys};assert all(same_task.values())
    sources=[
        'experiments/v1281_partial_reconnection_fixed24/owner.py',
        'experiments/v1281_partial_reconnection_fixed24/route_dispatch.py',
        'experiments/v1037_periodic_norm_source/periodic_norm.py',
        'experiments/v1020_terminal_two_route_development/periodic_support.py',
        'experiments/v1348_recoverable_tracking/causal_occupancy.py',
        'experiments/v1348_recoverable_tracking/ros_component.py',
        'experiments/v1288_baseline_interface/contract.py',
        'experiments/v1348_recoverable_tracking/rpp_async_default_params.json']
    text={name:(R/name).read_text() for name in sources}
    assert 'PeriodicSupport' in text[sources[0]] and 'branch(case)' in text[sources[1]]
    assert 'hypot(a,b)<=.25' in text[sources[2]]
    assert '.08*' in text[sources[4]] and 'self.horizon' in text[sources[4]]
    prior=dict(selected_task_fields_match=same_task,
        model_equivalence_proven_by_this_audit=False,
        rpccr_estimator='past-observation periodic coefficient polytope, declared sinusoidal/amplitude prior',
        rpp_estimator='last novel endpoint center ball, Euclidean speed bound and1.5s horizon',
        estimator_prior_equivalent=False,
        rpccr_proposal='route-dispatched qualified control sources/observation approaches and reconnection library',
        rpp_proposal='generic bounded pose lattice plus RPP path tracking',
        proposal_prior_equivalent=False,
        same_lidar_backend_does_not_prove_same_information=True,
        formal_independent_method_comparison_ready=False)
    old_owner=text[sources[0]]
    current_bridge=text[sources[5]]
    assert 'plan=renew(' in old_owner and "planner.start(" in current_bridge
    clock_audit=dict(
        rpccr_original_has_inline_planning_stages=True,
        original_independent_clock_realtime_acceptance_proven=False,
        current_rpp_runs_async_search_and_brake_timers=True,
        same_physical_clock_during_compute_proven=False,
        consequence='Do not compare old RPCCR success directly with a new RPP continuous-planning experiment as a controlled latency comparison')
    shared=['native_component.py','gear_handoff.py','transport.py','rpp_async_default_params.json']
    reuse=[]
    for name in shared:
        a=R/'experiments/v1347_cusp_segment_execution'/name;b=R/'experiments/v1348_recoverable_tracking'/name
        assert sha(a)==sha(b),name
        reuse.append(dict(component=name,sha256=sha(a),same_1347_1348=True))
    # Positive reuse does not cover the whole ROS bridge, changed prediction
    # inputs, a different steering law, task, safety gate or future parameter.
    reuse_policy=dict(examples=reuse,completed_old_static_passes=2,
        old_static_passes_are_new_trials=False,
        replay_new_software_actions_if_changed=True,
        reuse_requires_exact_dependency_closure_and_task_contract=True,
        entry_output_guard_root_clock_lock_checks_never_skipped=True,
        any_future_skipped_static_stage_must_be_preregistered=True)
    assert (R/'REVIEW_PENDING').read_bytes()==guard
    result=dict(passed=True,scope='data-only accounting and next-plan readiness audit',
        checked_at=datetime.datetime.now().astimezone().isoformat(),
        current_status='REVIEW_PENDING',active_navigation=False,
        historical_task_timing=timing,acceleration_accounting=estimate,
        information_fairness=prior,clock_fairness=clock_audit,qualification_reuse=reuse_policy,
        qualified_gpu_backend=False,gpu_speedup_measured=False,
        resource_plan=dict(native_cpu=[2],ros_planning_cpu=[3,4,5],
            native_single_instance=True,offline_math_can_parallelize_distinct_cores=True,
            latency_benchmarks_serial=True,no_stage_process_inspection=True),
        source_sha256={n:sha(R/n) for n in sources},
        models=0,new_native=0,replay_native=0,training=0,stage_access=0,
        physical_authorized=False,new_physical_window=False,
        guard_preserved=True,wall_s=time.monotonic()-started)
    (O/'AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=True,current_status=result['current_status'],
        static_pair_seconds=latest['static_pair_monitor_s'],latest_whole_batch_seconds=latest['summed_monitor_wall_s'],
        latest_dynamic_seconds=latest['dynamic_monitor_s'],planning_seconds=search_wall,
        kernel_speedup=estimate['mean_kernel_ratio'],information_contract_equivalent=False,models=0,new_native=0)))


if __name__=='__main__':main()
