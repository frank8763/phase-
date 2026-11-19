"""Real signed allocator and old interlock reproduce the saved same-gear restart."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def load(name,path):
    s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    O.mkdir(exist_ok=True)
    raw=R/'runs/v858_nav2_verified/v1358/horizon_terminal_dynamic_main'
    journal=json.loads((raw/'APPLIED_JOURNAL.json').read_text());failed=journal[-1]
    old=load('old_gear','experiments/v1358_terminal_contract/gear_handoff.py');gate=old.GearHandoff()
    for row in journal[:-1]:
        _,_,proof=gate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        assert proof==row['gear_handoff']
    v,w,proof=gate.select(*failed['upstream_request'][:2],native_tick=failed['before_native'],body=failed['body'],last_ctrl=failed['last_ctrl'],encoders=failed['encoders'])
    assert v<-.005 and proof['mode']=='UNCHANGED' and not proof['measured_rest'] and proof['prior_gear']==-1
    sys.path.insert(0,str(R/'experiments/v993_steering_transient_diagnosis'))
    from fixture import make
    signed=load('actual_signed_allocator','experiments/v1035_signed_timed_input_source/signed_control.py')
    setup=json.loads((raw/'physics/SETUP.json').read_text());owner=make(signed.Adapter,setup)
    owner.last=np.asarray(failed['last_ctrl']);owner.integral=failed['integral']
    error=None
    try:owner.compute(v,w,*failed['body'][3:],False)
    except AssertionError as exc:error=str(exc)
    assert error=='REVERSE_GEAR_REQUIRES_ACTUAL_REST',error
    proof=dict(reproduced=True,saved_failure_tick=failed['before_native'],prior_gear=-1,drive_targets=failed['last_ctrl'][2:],
        measured_longitudinal_m_s=failed['body'][3],old_interlock_passed_reverse_without_actual_rest=True,
        actual_unchanged_allocator_error=error,failed_row=failed,models=0,physical_native=0)
    (O/'ORIGINAL_REPRODUCTION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='failed_row'}))


if __name__=='__main__':main()
