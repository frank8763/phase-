"""Complete finite-method witness producer; no standalone launch permission.

All construction/steps require a separately registered CPU2 run_phase owner,
the same execution-lock descriptor and qualified source hashes. This source is
preparation only until that entry is qualified and frozen. No MuJoCo imports.
"""
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


Method=exact('phase_v1406_exact_current_method',C/'method.py').Method
assert Path(Method.select.__code__.co_filename).resolve()==C/'method.py', 'CURRENT_METHOD_SOURCE_COLLISION'

def clone_private_branch(p, join):
    branch=copy.deepcopy(p)
    # A function's captured owner survives deepcopy unless explicitly rebound.
    branch.adapter.encoders=lambda owner=branch:join(owner.front,owner.front_rate)
    return branch


def binding():
    assert sorted(os.sched_getaffinity(0))==[2], 'CURRENT_WITNESS_REQUIRES_CPU2'
    assert os.environ.get('PHASE_REPO')==str(R) and os.environ.get('CUDA_VISIBLE_DEVICES')=='', 'CURRENT_WITNESS_REQUIRES_RUN_PHASE'
    sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
    from logic import Predictor,initial,kernel,Adapter
    for function,path in [(Predictor.step,'coupled_model.py'),(initial,'coupled_model.py'),(Adapter.compute,'coupled_control.py')]:
        assert Path(function.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode'/path, 'CURRENT_WITNESS_MODEL_BINDING'
    geometry=exact('v1398_original_response_geometry',R/'experiments/v1393_full9390_preparation/geometry.py').Geometry
    gear=exact('v1398_original_measured_gear',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py').GearHandoff
    capture=exact('v1398_original_capture',R/'experiments/v1376_prepared_capture_component/controller.py').Capture
    return Predictor,initial,kernel,Adapter,geometry,gear,capture


def generate(current, setup, *, authority, lock, peer_command, save_branch):
    # Authorization is supplied by the future registered owner, never inferred
    # from the old V1393 or V1396 success. No current authority file exists yet.
    parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
    assert authority['models_authorized'] is True and authority['round_id']==parent['active_round'] and parent['models_now_authorized'], 'CURRENT_WITNESS_NOT_REGISTERED'
    assert authority['current_input_sha256']==current['input_sha256'], 'CURRENT_WITNESS_INPUT_NOT_APPROVED'
    assert authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'CURRENT_WITNESS_BOOT_CHANGED'
    assert 0<authority['maximum_nominal_native']<=5000 and 0<authority['maximum_analytical_native']<=1005000
    assert authority['absolute_deadline_unix']<=1795395600 and authority['hard_stop_monotonic']<=parent['hard_stop_monotonic']
    assert authority['tested_source_hashes'] and all(hashlib.sha256((R/name).read_bytes()).hexdigest()==h for name,h in authority['tested_source_hashes'].items()), 'CURRENT_WITNESS_SOURCE_CHANGED'
    assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock', 'CURRENT_WITNESS_WRONG_LOCK'
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    Predictor,initial,kernel,Adapter,Geometry,GearHandoff,Capture=binding()
    import numpy as np
    state=dict(current);expected=state.pop('input_sha256')
    assert hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==expected, 'CURRENT_WITNESS_INPUT_CHANGED'
    origin=current['origin'];forecast=current['bridge_forecast'];segment=current['next_segment'];origin_tick=origin['native_tick']
    assert forecast['invariant_for_all_future_under_declared_class'] and forecast['periodic_source_tick']<=origin_tick
    geometry=Geometry(setup['known'],[*forecast['center'],forecast['radius_m']])
    start=time.monotonic();end=min(start+1800,authority['hard_stop_monotonic']-30)
    result=dict(passed=False,closed=False,physical_admission=False,physical_native=0,mujoco_initializations=0,replay_native=0,
                analytical_native=0,analytical_inflight_unknown=False,analytical_predictor_constructions=0,
                analytical_branch_copies=0,complete_braking_branches=0,nominal_native=0,input_sha256=expected,qualified_method=current['method_spec']['method'])
    states=[];controls=[];journal=[];memory=[];modes=[];minimum_nominal=math.inf;minimum_brake=math.inf
    def advance(p,v,w):
        assert time.monotonic()<end and time.time()<min(authority['absolute_deadline_unix'],1795395600)-30, 'CURRENT_WITNESS_DUAL_CLOCK_STOP'
        assert result['analytical_native']<authority['maximum_analytical_native'], 'CURRENT_WITNESS_ANALYTICAL_CAP'
        result['analytical_inflight_unknown']=True
        s,u=p.step(v,w,False)
        result['analytical_native']+=1;result['analytical_inflight_unknown']=False
        return s,u
    def body(p):
        s=p.state;return [float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])]
    def enc(p):return [*p.front.tolist(),*p.front_rate.tolist()]
    def rear_error(p,target):
        s=p.state;a=[s[0]-.3*math.cos(s[2]),s[1]-.3*math.sin(s[2]),s[2]]
        return math.dist(a[:2],target[:2]),abs(math.atan2(math.sin(a[2]-target[2]),math.cos(a[2]-target[2])))
    try:
        result['analytical_predictor_constructions']=None
        p=Predictor(setup,initial(origin),kernel.PARAMETERS);result['analytical_predictor_constructions']=1
        assert p.adapter.__class__ is Adapter, 'CURRENT_WITNESS_ALLOCATOR_CHANGED'
        p.adapter.parked_target=origin['parked_target'];p.adapter._steering_motion_active=origin['steering_motion_active']
        assert np.max(abs(np.asarray(body(p))-origin['body']))<=1e-8
        assert np.max(abs(p.front-origin['steering']['position']))<=1e-8 and np.max(abs(p.front_rate-origin['steering']['velocity']))<=1e-8
        assert np.max(abs(p.adapter.last-origin['controller_memory']['last_ctrl']))<=1e-8 and p.adapter.integral==origin['controller_memory']['integral']
        assert p.coupled_episode==origin['coupled_episode'] and abs(p.state[4]-origin['body_lateral'])<=1e-8
        gate=GearHandoff()
        for key,value in current['gear_memory'].items():setattr(gate,key,value)
        method=Method(current);final_zero=None;reply=None;stage=None
        states.append(p.state.copy())
        for index in range(authority['maximum_nominal_native']):
            tick=origin_tick+index
            decision=method.select(body(p),tick,enc(p),p.adapter.last)
            stage=decision['phase'];requested=decision['requested'];target=decision['parked_target'];metadata=decision['metadata']
            final_zero=None if decision['final_tail_start'] is None else decision['final_tail_start']-origin_tick
            if stage=='RPP':
                if reply is None or index%5==0:
                    reply=peer_command(native_tick=tick,body=body(p),input_sha256=expected)
                    assert reply['input_sha256']==expected and reply['native_tick']==tick and reply['body']==body(p) and reply['not_measured_response'], 'CURRENT_MODELED_PEER_SOURCE'
                if reply['kind']=='RPP_ACTION_DONE':
                    assert reply['status']==4 and reply['error_code']==0, 'CURRENT_RPP_MODELED_REFUSAL'
                    final_zero=index;stage='FINAL_TAIL';requested=[0.,0.];method.rpp_done(tick)
                else:
                    assert reply['kind']=='ORIGINAL_RPP_MODELED_COMMAND'
                    requested=[reply['v'],reply['w']]
                    assert abs(requested[0])<=.1+1e-6 and (abs(requested[0])<.005 or requested[0]*segment['gear']>0.), 'CURRENT_RPP_SIGN_OR_SPEED'
                    assert abs(requested[1])<=abs(requested[0])/1.32+1e-6, 'CURRENT_RPP_CURVATURE'
            if stage=='FINAL_TAIL':requested=[0.,0.]
            assert requested is not None
            # Complete branch from every exact nominal origin, including modes,
            # gear holds and both applied200-zero tails; stream evidence out.
            branch=clone_private_branch(p,lambda a,b:np.r_[a,b]);result['analytical_branch_copies']+=1;branch.adapter.parked_target=None
            bs=[branch.state.copy()];bu=[]
            for _ in range(200):s,u=advance(branch,0.,0.);bs.append(s.copy());bu.append(u.copy())
            bs=np.asarray(bs);bu=np.asarray(bu);lower=geometry.tube(bs);minimum_brake=min(minimum_brake,lower)
            rest=bool(abs(bs[-1,[3,4,5]]).max()<=.003 and abs(branch.front_rate).max()<=.03 and abs(branch.adapter.last[2:]).max()<=1e-10)
            caps=bool((abs(bs[:,3:6])<=np.array([.13,.03,.16])+1e-8).all())
            proof=dict(before_native=tick,complete_native=200,causal_tube_lower_m=lower,rest=rest,body_caps=caps,input_sha256=expected)
            save_branch(proof,bs,bu);result['complete_braking_branches']+=1
            assert lower>=.22-1e-8 and rest and caps, 'CURRENT_COMPLETE_BRAKING_REFUSED'
            vr,wr,gear_proof=gate.select(*requested,native_tick=tick,body=body(p),last_ctrl=p.adapter.last,encoders=enc(p))
            command_checked=None
            if stage=='RPP':
                command_checked=time.monotonic()
                assert 0<=command_checked-reply['origin']['generated_monotonic']<=.2, 'CURRENT_MODELED_COMMAND_EXPIRED_DURING_CERTIFICATE'
            method.observe_gear(tick,gear_proof)
            memory.append([*p.adapter.last.tolist(),float(p.adapter.integral)])
            modes.append(dict(parked_target=target,coupled_episode=p.coupled_episode,steering_motion_active=bool(getattr(p.adapter,'_steering_motion_active',False))))
            p.adapter.parked_target=target;s,u=advance(p,vr,wr);states.append(s.copy());controls.append(u.copy());result['nominal_native']+=1
            assert (abs(p.state[3:6])<=np.array([.13,.03,.16])+1e-8).all(), 'CURRENT_NOMINAL_BODY_CAP'
            lower=geometry.tube(states[-2:]);minimum_nominal=min(minimum_nominal,lower)
            journal.append(dict(before_native=tick,stage=stage,requested=requested,admitted=[vr,wr],gear=gear_proof,capture=metadata,zero_tail=stage=='FINAL_TAIL',qualified_method=method.name,control_owner=decision['control_owner'] if stage!='FINAL_TAIL'else'DISCLOSED_SHARED_EXECUTION_BRIDGE',rpp_sequence=None if stage!='RPP'else reply['sequence'],modeled_command_checked_monotonic=command_checked))
            assert lower>=.22-1e-8, 'CURRENT_NOMINAL_CAUSAL_TUBE_REFUSED'
            if final_zero is not None and index-final_zero+1==200:
                position,heading=rear_error(p,segment['poses'][-1])
                whole_tube=geometry.tube(states)
                checks=dict(endpoint_position=position<=.12,endpoint_heading=heading<=.20,whole_nominal_tube=whole_tube>=.22-1e-8,
                    complete200_zero_tail=all(x['zero_tail'] and x['admitted']==[0.,0.] for x in journal[-200:]),
                    all_branches_saved=result['complete_braking_branches']==len(journal),
                    body_rest=max(abs(x) for x in body(p)[3:])<=.003,steering_rest=max(abs(x) for x in p.front_rate)<=.03,
                    rear_zero=max(abs(x) for x in p.adapter.last[2:])<=1e-10)
                result.update(passed=all(checks.values()),checks=checks,whole_nominal_tube_m=whole_tube,endpoint_position_m=position,endpoint_heading_rad=heading,stop_reason='CURRENT_COMPLETE_SEGMENT_WITNESS');break
        else:result['stop_reason']='CURRENT_NOMINAL_LIMIT_REFUSAL'
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc(),stop_reason='CURRENT_EVENT_WITNESS_REFUSED_OR_EXCEPTION')
    finally:
        unchanged=all(hashlib.sha256((R/name).read_bytes()).hexdigest()==h for name,h in authority['tested_source_hashes'].items())
        result.update(original_RPP_nominal_native=sum(r.get('control_owner')=='ORIGINAL_RPP'for r in journal),shared_bridge_nominal_native=sum(r.get('control_owner')!='ORIGINAL_RPP'for r in journal),closed=True,passed=result['passed'] and unchanged,source_unchanged=unchanged,wall_s=time.monotonic()-start,minimum_nominal_tube_m=None if minimum_nominal==math.inf else minimum_nominal,minimum_braking_tube_m=None if minimum_brake==math.inf else minimum_brake)
    return result,dict(states=states,ctrl=controls,journal=journal,memory=memory,modes=modes)
