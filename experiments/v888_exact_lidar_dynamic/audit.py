"""Saved evidence and timing only. A verified failed prefix cannot become an arrival."""
import importlib.util,json,sys,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from audit_result import audit as original_audit
def audit(task):
    out=Path(task['output']);result=original_audit(task)
    try:
        n=json.loads((out/'RESULT.json').read_text());profile=json.loads((out/'RUNTIME_TIMING.json').read_text())
        with np.load(out/'RUNTIME_TIMING.npz')as z:rows=z['rows'];fields=z['fields'].tolist()
        timing_ok=bool(rows.ndim==2 and rows.shape[1]==5 and len(rows)==profile['recorded_rows']<=profile['capacity']and np.isfinite(rows).all()and np.all(rows[:,3:]>=0)and fields==['tick_before','stage_id','wall_start_s','wall_elapsed_s','thread_cpu_elapsed_s'])
        gate_ok=n.get('maximum_wall_lag_s')==profile['maximum_wall_lag_s']<=.1 and profile.get('overrun')is None
        result.update(timing_profile_integrity=timing_ok,original100ms_gate_passed=gate_ok,failed_prefix_record_integrity_passed=False)
        # The original full physical audit recomputes saved checks without a model.
        # Its closed_native/wall_pacing checks remain failures for a timing exception.
        if n.get('status')!='NATIVE_COMPLETE'and (out/'physics/REPLAY.json').exists():
            spec=importlib.util.spec_from_file_location('v888_saved_prefix_audit',R/'experiments/v858_nav2_verified/audit_navigation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            saved=m.audit(task);checks=saved['checks'];integrity=all(v for k,v in checks.items()if k not in ['closed_native','wall_pacing','genuine_ros_observations'])
            result.update(failed_prefix_record_integrity_passed=integrity,failed_prefix_checks=checks)
        result['passed']=bool(result['passed']and n.get('passed')is True and timing_ok and gate_ok)
        result['scope']='V888 single-actor dynamic Nav2 development; not new24 confirmation or RP-CCR328'
        binding=json.loads((out/'physics/EXACT_SENSOR_BINDING.json').read_text());binding_ok=binding.get('passed')is True and binding.get('original_and_exact_true_t0_packets_bitwise_equal')is True and binding.get('native_integrations_during_binding')==0
        result['exact_sensor_binding_and_true_t0_equivalence']=binding_ok
        result['passed']=bool(result['passed']and binding_ok)
        setup=json.loads((out/'physics/SETUP.json').read_text());actor=setup.get('actor');config_ok=bool(setup['dynamic']is True and actor and actor['radius_m']==.1 and actor['amplitude_m']==.25 and actor['maximum_speed_m_s']==.08 and actor['phase_rad']==task['phase'])
        with np.load(out/'physics/NATIVE_TRACE.npz')as z:
            at=z['time'];positions=z['mocap_pos'][:,actor['mocap_id'],:2]
            expected=np.asarray(actor['anchor_xy'])+actor['amplitude_m']*np.sin(actor['omega_rad_s']*at[:,None]+actor['phase_rad'])*np.asarray(actor['axis_xy'])
            motion_ok=bool(np.max(abs(positions-expected))<=1e-10 and np.ptp(positions,axis=0).max()>1e-5 and np.linalg.norm(np.diff(positions,axis=0),axis=1).max()<=.0008+1e-8)
        from repeat_contract import canonical_setup
        preflight=R/'runs/v858_nav2_verified/v888/t0_we/physics';p_setup=json.loads((preflight/'SETUP.json').read_text())
        initial=np.load(out/'physics/INITIAL_STATE.npz')['state'];p_initial=np.load(preflight/'INITIAL_STATE.npz')['state'];same_t0=bool(canonical_setup(setup)==canonical_setup(p_setup)and initial.shape==p_initial.shape and np.max(abs(initial-p_initial))<=1e-8)
        result['same_actual_dynamic_preflight_physical_setup_and_initial_state']=same_t0
        plans=json.loads((out/'PLANS.json').read_text());routes=json.loads((out/'ROUTER_REQUESTS.json').read_text());d=n.get('first_actor_detection');after_time=float('inf')if d is None else n['armed_at']+d['native_tick']*.01
        after=[x for x in plans if x['at']>=after_time];routes_after=[x for x in routes if x['passed']and x['started_monotonic']>=after_time]
        result.update(original_dynamic_actor_configuration=config_ok,independent_recorded_actor_motion=motion_ok,reference_updates_after_detection=len(after),successful_routes_after_detection=len(routes_after),postdetection_update_is_periodic_not_claimed_detection_triggered=True)
        result['functional_passed']=bool(result.get('functional_passed')and after and routes_after)
        result['evidence_passed']=bool(result.get('evidence_passed')and config_ok and motion_ok and same_t0)
        result['passed']=bool(result['passed']and result['functional_passed']and result['evidence_passed'])
    except Exception as e:result.update(passed=False,timing_audit_error=repr(e),timing_audit_traceback=traceback.format_exc())
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
