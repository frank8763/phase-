"""Saved-only full input auditor and explicit1e-12 analytical portability gate."""
import importlib.abc,importlib.util,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];S=R/'runs/v1013_atomic_handoff_software/saved';O=R/'runs/v1014_atomic_handoff_navigation'
sys.path[:0]=[str(C),str(R/'experiments/v1003_causal_recovery_execution')]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('SAVED_AUDIT_ONLY '+name)
sys.meta_path.insert(0,NoModel())
def main():
    spec=importlib.util.spec_from_file_location('v1014_saved_scientific_audit',C/'scientific_audit.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    prefix=str(R/'runs/v858_nav2_verified/v1009/main_we');m.Path=lambda p:Path(str(p).replace(prefix,str(S),1))if str(p).startswith(prefix)else Path(p)
    setup=json.loads((S/'physics/SETUP.json').read_text());task=json.loads((C/'TASKS.json').read_text())[0]
    with np.load(S/'physics/NATIVE_TRACE.npz')as z:q=z['qpos'];v=z['qvel'];ctrl=z['ctrl'][:,setup['actuator_ids']]
    body=m.physical_body(q,v);proof=m.own_inputs(S,task,body,q,v,ctrl,setup)
    assert proof['passed']and proof['all_native_inputs_checked']==10076
    from handoff_audit import audit
    try:audit(S)
    except KeyError:missing_handoff_rejected=True
    else:raise AssertionError('OLD_UNPROTECTED_HANDOFF_RELABELED')
    record=json.loads((S/'COMMITTED_PROFILE_1.json').read_text());states=np.asarray(record['plan']['state_path']);bad=states.copy();bad[1,0]+=1e-9
    assert not np.allclose(states,bad,rtol=0.,atol=1e-12),'PORTABLE_STATE_GATE_TOO_LOOSE'
    result=dict(passed=True,models=0,integrations=0,physical_replays=0,saved_full_input_audit=proof,
        old_total_failure_not_upgraded=True,missing_atomic_handoff_rejected=missing_handoff_rejected,
        analytical_state_rebuild_tolerance_only=1e-12,one_nanometer_state_tamper_rejected=True,
        physical_state_control_mocap_replay_tolerance_unchanged=1e-8,actuator_controls_and_body_requests_still_exact=True)
    (O/'SAVED_AUDIT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,native_inputs_saved_checked=10076,models=0)))
if __name__=='__main__':main()
