"""Real saved input seams + independent final-target checks; zero new physics."""
import copy
import hashlib
import json
import math
import time
import xml.etree.ElementTree as ET
import numpy as np
from fixture import R,O,old,make
from vehicle_control import Adapter,steering,transfer_restored_state
from independent import check


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    checks={};cases=[];timings=[];witnesses=[];negative=[]
    receipt=json.loads((O/'RESTORE_RECEIPT.json').read_text())
    for row in receipt['files']:assert digest(R/row['path'])==row['sha256']
    checks['original_saved_member_sha']=True
    xml=R/'runtime/mk-mini/training/assets/mkmini_real/mkmini_mobile_manipulator_indoor_v1.xml'
    root=ET.parse(xml).getroot();world=root.find('worldbody')
    positions={n.get('name'):list(map(float,n.get('pos','0 0 0').split()))for n in world.iter('body')}
    assert positions['left_front_steer']==[.3,.27,-.12]and positions['right_front_steer']==[.3,-.27,-.12]
    assert positions['left_rear_wheel']==[-.3,.27,-.12]and positions['right_rear_wheel']==[-.3,-.27,-.12]
    for n in world.iter('joint'):
        if 'steer'in n.get('name',''):assert n.get('axis')=='0 0 1'
        if 'wheel'in n.get('name',''):assert n.get('axis')=='0 1 0'
    checks['existing_model_axes_and_axle_positions_decoded_no_model_load']=True
    setup=json.loads((O/'saved_v987/physics/SETUP.json').read_text())
    inputs=[('V982',6083,O/'saved_v982/physics'),('V987',6083,O/'saved_v987/physics'),
            ('V974_second_origin',7814,O/'saved_v982/prior/physics')]
    for label,origin,folder in inputs:
        commands=json.loads((folder/'BODY_COMMANDS.json').read_text())
        with np.load(folder/'NATIVE_TRACE.npz')as f:controls=f['ctrl'][:,:4]
        before=make(old.Adapter);history_error=0.
        for i,row in enumerate(commands[:origin]):
            control=before.compute(*row[1:6]);history_error=max(history_error,float(abs(control-controls[i]).max()))
        assert history_error<=1e-8
        a=make(Adapter);transfer=transfer_restored_state(before,a)
        assert np.array_equal(a.last,before.last)and a.integral==before.integral
        assert transfer['integrations']==0
        result=[]
        for j,row in enumerate(commands[origin:]):
            previous=a.last.copy();stamp=time.perf_counter();u=a.compute(*row[1:6]);timings.append(time.perf_counter()-stamp)
            proof=check(previous,u,setup['limits'],setup['slew_per_second'])
            if row[5]or abs(row[1])<.005:assert np.array_equal(previous[:2],u[:2])
            result.append(u.tolist())
            if label=='V987'and j+origin+1 in [6114,6124,6144,6184,6229]:
                witnesses.append(dict(native_tick=j+origin+1,old_actual_body_input=row[1:6],
                    new_counterfactual_control=u.tolist(),allocation=copy.deepcopy(a.last_allocation_proof),independent=proof))
        cases.append(dict(label=label,origin_native=origin,history_rows=origin,history_control_error=history_error,
            saved_response_rows=len(result),all_final_targets_independently_coordinated=True,
            new_physical_response=False,complete_stop_inputs_included=True))
    checks['three_real_saved_input_sequences_and_two_origins']=len(cases)==3
    start=next(w for w in witnesses if w['native_tick']==6114)
    assert start['new_counterfactual_control'][2]!=start['new_counterfactual_control'][3]
    checks['saved_startup_curved_motion_has_nonzero_allocated_differential']=True
    checks['saved_original_motor_history_reconstructs']=all(c['history_control_error']<=1e-8 for c in cases)
    # Original controller compute class + same caller seam, but no root/model API.
    rng=np.random.default_rng(990);boundary=0;max_residual=0.
    for k in np.r_[np.linspace(-.758770385,.758770385,11),0.]:
        for mean in [0.,.001,.0875,.2,1.,6.]:
            for v in [.005,.03,.05,.1,.30]:
                for w in [-.16,0.,.16]:
                    a=make(Adapter);a.last=np.r_[steering(k,.6,.27),mean*np.array([1-.27*k,1+.27*k])]
                    previous=a.last.copy();u=a.compute(v,w,.04,float(rng.uniform(-.16,.16)))
                    r=check(previous,u,setup['limits'],setup['slew_per_second'])
                    max_residual=max(max_residual,r['rear_compatibility_residual_rad_s']);boundary+=1
    checks['fixed_boundary_map_cases']=boundary==1080
    # A complete 20k-input call sequence with arbitrary flips/deadband/stale.
    a=make(Adapter);stale_count=deadband_count=0
    for i in range(20000):
        v=float(rng.choice([0.,.004999,.005,.03,.05,.10,.30]));w=float(rng.uniform(-.2,.2))
        stale=bool(rng.integers(0,40)==0);previous=a.last.copy()
        u=a.compute(v,w,float(rng.uniform(-.02,.2)),float(rng.uniform(-.2,.2)),stale)
        r=check(previous,u,setup['limits'],setup['slew_per_second']);max_residual=max(max_residual,r['rear_compatibility_residual_rad_s'])
        if stale or v<.005:
            assert np.array_equal(previous[:2],u[:2]);stale_count+=int(stale);deadband_count+=int(v<.005)
    checks['continuous_twenty_thousand_calls_with_stop_and_restart']=True
    # From every nonzero operating curvature, braking has a finite full tail;
    # mathematical target convergence is not actual chassis stopping evidence.
    for k in np.linspace(-.758770385,.758770385,21):
        a=make(Adapter);a.last=np.r_[steering(k,.6,.27),6*np.array([1-.27*k,1+.27*k])]
        first_front=a.last[:2].copy();prior_mean=a.last[2:].mean()
        for i in range(200):
            previous=a.last.copy();u=a.compute(0.,0.,.1,.03,True);check(previous,u,setup['limits'],setup['slew_per_second'])
            assert np.array_equal(first_front,u[:2])and u[2:].mean()<=prior_mean+1e-10;prior_mean=u[2:].mean()
        assert np.array_equal(a.last[2:],np.zeros(2))
    checks['coordinated_steering_hold_full_stop_21_curvatures']=True
    # Decode/mutate final output independently. Wrong targets must not pass just
    # because the allocator's own proof says passed.
    a=make(Adapter)
    for _ in range(150):a.compute(.05,.01,.05,0.)
    p=a.last.copy();u=a.compute(.05,.01,.05,0.)
    for label,index,offset in [('left_front',0,.001),('right_front',1,-.001),('left_rear',2,.001),('right_rear',3,-.001)]:
        changed=u.copy();changed[index]+=offset
        try:check(p,changed,setup['limits'],setup['slew_per_second'])
        except AssertionError:negative.append(dict(case=label,rejected=True))
        else:negative.append(dict(case=label,rejected=False))
    for label,changed in [('front_sign',np.array([-u[0],u[1],u[2],u[3]])),('rear_reverse',np.array([u[0],u[1],-u[2],u[3]])),
                          ('rate',u+np.array([0,0,1,1]))]:
        try:check(p,changed,setup['limits'],setup['slew_per_second'])
        except AssertionError:negative.append(dict(case=label,rejected=True))
        else:negative.append(dict(case=label,rejected=False))
    for i in range(4):
        args=[.05,.01,.05,0.];args[i]=float('nan');a=make(Adapter);memory=a.last.copy()
        try:a.compute(*args)
        except AssertionError:negative.append(dict(case='nonfinite_'+str(i),rejected=np.array_equal(a.last,memory)))
        else:negative.append(dict(case='nonfinite_'+str(i),rejected=False))
    for label,change in [('inconsistent_front',lambda a:a.last.__setitem__(0,.1)),
                         ('inconsistent_rear',lambda a:a.last.__setitem__(2,.1)),
                         ('negative_rear',lambda a:a.last.__setitem__(slice(2,4),[-.1,-.1]))]:
        a=make(Adapter);change(a);before=a.last.copy()
        try:a.compute(.05,.01,.05,0.)
        except AssertionError:negative.append(dict(case=label,rejected=np.array_equal(before,a.last)))
        else:negative.append(dict(case=label,rejected=False))
    checks['independent_mutation_and_invalid_memory_negatives']=all(x['rejected']for x in negative)
    # Compare deterministic identical independent stateful invocations.
    a=make(Adapter);b=make(Adapter)
    for i in range(200):
        args=(.05,float(.02*math.sin(i*.1)),.045,-.03)
        assert np.array_equal(a.compute(*args),b.compute(*args))
    checks['deterministic_final_control_and_memory']=True
    assert 'mujoco'not in __import__('sys').modules
    checks['no_physics_module_imported']=True
    result=dict(passed=all(checks.values()),checks=checks,models=0,actual_native=0,private_native=0,replay_native=0,
        physical_tracking_qualified=False,physical_ready=False,models_authorized=False,
        saved_cases=cases,fixed_boundary_cases=boundary,continuous_sequence_inputs=20000,
        continuous_stale_inputs=stale_count,continuous_deadband_inputs=deadband_count,
        maximum_independent_rear_compatibility_residual_rad_s=max_residual,
        runtime_saved_map_s=dict(p99=float(np.quantile(timings,.99)),maximum=max(timings),samples=len(timings)),
        negatives=negative,witnesses=witnesses,model_axes_source_sha256=digest(xml),
        limitations='Only algebraic control-map compatibility on old observations/metadata. No predicted or actual new trajectory, friction identification, physical tracking or dynamic acceptance.')
    (O/'CONTROL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='witnesses'}));assert result['passed']


if __name__=='__main__':main()
