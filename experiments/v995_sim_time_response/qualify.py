"""Actual schedules/control/binding reconstruction on explicit arrays only."""
import ast,copy,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
from fixture import R,O,old,make
from vehicle_control import Adapter,transfer_restored_state,inverse_steering
from schedule import controls
from independent import check

def main():
    tasks=json.loads((Path(__file__).parent/'TASKS.json').read_text());checks={};cases=[]
    receipt=json.loads((O/'RESTORE_RECEIPT.json').read_text())
    for row in receipt['files']:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    setup=json.loads((O/'prior_v974/physics/SETUP.json').read_text())
    commands=json.loads((O/'prior_v974/physics/BODY_COMMANDS.json').read_text())
    history=make(old.Adapter,setup)
    for row in commands[:6083]:history.compute(*row[1:6])
    k=inverse_steering(history.last[0],1,.6,.27)
    for task in tasks:
        a=make(Adapter,setup);a.virtual_rate=task['virtual_rate_rad_s'];transfer_restored_state(history,a)
        b=make(Adapter,setup);b.virtual_rate=a.virtual_rate;transfer_restored_state(history,b)
        fronts=[];maxrate=0.
        for i in range(800):
            v,w,stale=controls(i,task,k);previous=a.last.copy()
            # Same speed and opposing body-yaw inputs: feedback must be exactly
            # disabled in this diagnostic, without falsifying the recorded input.
            u=a.compute(v,w,.028,-.05,stale);other=b.compute(v,w,.028,.05,stale)
            assert np.array_equal(u,other)
            assert a.last_allocation_proof['measured']==[.028,-.05]
            assert check(previous,u,setup['limits'],setup['slew_per_second'])['passed']
            d0=np.arctan(.6*inverse_steering(previous[0],1,.6,.27));d1=np.arctan(.6*inverse_steering(u[0],1,.6,.27))
            maxrate=max(maxrate,abs(float(d1-d0))/.01);fronts.append(u[:2].tolist())
            assert abs(float(d1-d0))<=a.virtual_rate*.01+1e-10
            if i>=600:assert np.max(abs(u[:2]-previous[:2]))==0.
        assert np.array_equal(a.last[2:],np.zeros(2))
        cases.append(dict(slot=task['slot'],passed=True,software_map_calls=800,maximum_target_virtual_rate_rad_s=maxrate))
    checks['all_four_registered_stimuli_and_both_rate_bounds']=all(c['passed']for c in cases)
    checks['no_body_yaw_feedback_or_forged_measurement']=True
    checks['same_full_200_tick_stop_no_alignment_after_stop']=True
    checks['original_saved_member_sha']=True
    checks['four_tasks_one_original_state_same_scene_no_seed_search']=len(tasks)==4 and all(t['seed']==10010001 and t['origin_native_tick']==6083 and t['stage']=='diagnostic'for t in tasks)
    checks['new_90min_user_authority']=json.loads((R/'runs/sim_time_recovery_20261110/USER_AUTHORIZATION.json').read_text())['maximum_root_s']==5400.
    for p in Path(__file__).parent.iterdir():
        if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
    checks['source_parse']=True
    # Same constructor/dispatch/audit seam already exercised by V990, now select
    # the diagnostic class at its actual binding and reconstruct metadata rows.
    import actuation_binding as binding
    assert binding.SOURCE==R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py'
    checks['declared_probe_adapter_source_selected']=True
    assert 'mujoco'not in sys.modules
    result=dict(passed=all(checks.values()),checks=checks,cases=cases,models=0,integrations=0,
        physical_response_tested=False,diagnostic_only=True,navigation_qualified=False,
        no_controller_fitted_from_new_responses=True)
    (O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
if __name__=='__main__':main()
