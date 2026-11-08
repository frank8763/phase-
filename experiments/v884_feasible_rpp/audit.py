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
            spec=importlib.util.spec_from_file_location('v884_saved_prefix_audit',R/'experiments/v858_nav2_verified/audit_navigation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            saved=m.audit(task);checks=saved['checks'];integrity=all(v for k,v in checks.items()if k not in ['closed_native','wall_pacing','genuine_ros_observations'])
            result.update(failed_prefix_record_integrity_passed=integrity,failed_prefix_checks=checks)
        result['passed']=bool(result['passed']and n.get('passed')is True and timing_ok and gate_ok)
        result['scope']='V884 same original static NS runtime qualification, not dynamic acceptance'
    except Exception as e:result.update(passed=False,timing_audit_error=repr(e),timing_audit_traceback=traceback.format_exc())
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
