"""Saved evidence and timing only. A verified failed prefix cannot become an arrival."""
import gzip,importlib.util,json,sys,traceback
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
            spec=importlib.util.spec_from_file_location('v931_saved_prefix_audit',R/'experiments/v858_nav2_verified/audit_navigation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            saved=m.audit(task);checks=saved['checks'];integrity=all(v for k,v in checks.items()if k not in ['closed_native','wall_pacing','genuine_ros_observations'])
            result.update(failed_prefix_record_integrity_passed=integrity,failed_prefix_checks=checks)
        records=json.loads((out/'MPPI_DIAGNOSTICS.json').read_text())
        command_ok=bool(records)and all(x['gear']in[-1,1]and x['v']*x['gear']>=-1e-6 and abs(x['w'])<=abs(x['v'])/1.32+1e-6 and abs(x['v'])<=.100001 and x['final_full_trajectory_collision_checked']is True and x['samples']==56 and x['projected_samples']>=0 and(abs(x['v'])>=.005 or x['v']==0 and x['w']==0)for x in records)
        from ingress_audit import audit as ingress_check
        ingress=ingress_check(json.loads(gzip.decompress((out/'INGRESS.json.gz').read_bytes())),json.loads((out/'physics/BODY_COMMANDS.json').read_text()),task['run_id'])
        result['nominal_ingress_reconstruction']=ingress
        result['executable_mppi_output_and_final_trajectory_checks']=command_ok
        result['mppi_compute_timing_s']=dict(maximum=max([x['compute_s']for x in records],default=None),p99=float(np.quantile([x['compute_s']for x in records],.99))if records else None)
        result['mppi_controller_records']=len(records)
        attempts=json.loads((out/'FINAL_COMMAND_ATTEMPTS.json').read_text());finals=json.loads((out/'COMMANDS.json').read_text())['cmd_vel']
        from twist_contract import require_representable
        for x in attempts:require_representable(x['v'],x['w'])
        assert len(attempts)==len(finals)and all(x['decision']=='ACCEPTED'and [x['v'],x['w']]==f[1:]for x,f in zip(attempts,finals))
        result['all_final_commands_logged_before_validation']=True
        result['evidence_passed']=bool(result['evidence_passed']and command_ok)
        result['passed']=bool(result['passed']and n.get('passed')is True and timing_ok and gate_ok and command_ok)
        result['scope']='V931 executable MPPI engineering development, not RP-CCR/new24 acceptance'
    except Exception as e:result.update(passed=False,evidence_passed=False,timing_audit_error=repr(e),timing_audit_traceback=traceback.format_exc())
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
