"""Saved failure, exact allocator and adversarial reverse-restart boundaries."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from gear_handoff import GearHandoff

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    old=json.loads((O/'ORIGINAL_REPRODUCTION.json').read_text());row=old['failed_row']
    raw=R/'runs/v858_nav2_verified/v1358/horizon_terminal_dynamic_main'
    setup=json.loads((raw/'physics/SETUP.json').read_text())
    sys.path.insert(0,str(R/'experiments/v993_steering_transient_diagnosis'))
    from fixture import make
    s=importlib.util.spec_from_file_location('unchanged_signed',R/'experiments/v1035_signed_timed_input_source/signed_control.py')
    signed=importlib.util.module_from_spec(s);s.loader.exec_module(signed)
    gate=GearHandoff();gate.gear=-1;owner=make(signed.Adapter,setup)
    owner.last=np.array(row['last_ctrl']);owner.integral=row['integral'];checks={}
    for i in range(250):
        v,w,proof=gate.select(*row['upstream_request'][:2],native_tick=row['before_native']+i,
            body=row['body'],last_ctrl=owner.last,encoders=row['encoders'])
        assert v==w==0. and proof['mode']=='GEAR_BRAKE_HOLD'
        prev=owner.last.copy();u=owner.compute(v,w,*row['body'][3:],False)
        assert owner.commands.legal(u) and np.max(abs(u-prev)-owner.commands.rate*.01/.08)<=1e-10
    checks['saved_reverse_reentry_cannot_bypass_measured_rest']=True
    stationary=row['body'][:];stationary[3:]=[0.,0.];enc=row['encoders'][:];enc[2:]=[0.,0.]
    v,w,proof=gate.select(-.04,0.,native_tick=row['before_native']+250,body=stationary,last_ctrl=owner.last,encoders=enc)
    assert proof['released'] and proof['braking_native']>=200 and v==-.04
    owner.compute(v,w,0.,0.,False);checks['fresh_reverse_after200_and_full_actual_rest_passes']=True
    # Original allocator assertion still protects a direct bypass.
    owner.last=np.array(row['last_ctrl']);owner.integral=row['integral']
    try:owner.compute(*row['request'][:2],*row['body'][3:],False)
    except AssertionError as exc:assert str(exc)=='REVERSE_GEAR_REQUIRES_ACTUAL_REST'
    else:raise AssertionError('LOWER_ALLOCATOR_GUARD_WAS_REMOVED')
    checks['lower_allocator_assertion_unchanged']=True
    for speed in [-.004,.004]:
        g=GearHandoff();g.gear=-1
        assert g.select(-.04,0.,native_tick=0,body=[0.,0.,0.,speed,0.],last_ctrl=[0.]*4,encoders=[0.]*4)[:2]==(0.,0.)
    checks['reverse_zero_drive_both_moving_signs_refused']=True
    for desired in [-.04,.04]:
        g=GearHandoff()
        v,w,p=g.select(desired,0.,native_tick=0,body=[0.]*5,last_ctrl=[0.]*4,encoders=[0.]*4)
        assert v==desired
    checks['stationary_initial_commands_unmodified']=True
    # Reuse all actual forward static histories: this narrow reverse change
    # cannot alter them; no whole-route repeat solely for this algebra change.
    count=0
    for role in ['main','repeat']:
        out=R/('runs/v858_nav2_verified/v1357/entry_static_static_'+role);g=GearHandoff()
        for event in json.loads((out/'APPLIED_JOURNAL.json').read_text()):
            v,w,p=g.select(*event['upstream_request'][:2],native_tick=event['before_native'],body=event['body'],last_ctrl=event['last_ctrl'],encoders=event['encoders'])
            assert [v,w,False]==event['request'];count+=1
    checks['all_actual_forward_static_commands_unchanged']=count==18385
    result=dict(passed=all(checks.values()),checks=checks,saved_gate_braking_commands=250,
        actual_static_commands=count,original_failure_preserved=True,models=0,physical_native=0)
    (O/'GEAR_REENTRY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
