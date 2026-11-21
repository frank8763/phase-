"""Independently reconstruct finite methods, source engineeringMPPI replies and states."""
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import traceback


R=Path(__file__).resolve().parents[2]


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


BranchReader=exact('v1408_exact_bitwise_branch_reader',R/'experiments/v1407_lossless_branch_stream/stream.py').BranchReader


def backend_binding():
    source=exact('v1419_bound_frozen_generator',Path(__file__).with_name('generator.py'))
    assert Path(source.generate.__code__.co_filename).resolve()==Path(__file__).with_name('generator.py')
    assert Path(source.feedback.current.__code__.co_filename).resolve()==R/'experiments/v1409_scalar_steering_feedback/feedback.py'
    return source


def audit(current,setup,evidence,branch_folder,*,authority,lock):
    parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
    assert authority['mode']=='CURRENT_WITNESS_INDEPENDENT_AUDIT' and authority['round_id']==parent['active_round'] and parent['models_now_authorized'], 'UNREGISTERED_CURRENT_WITNESS_AUDIT'
    assert os.environ.get('PHASE_REPO')==str(R) and sorted(os.sched_getaffinity(0))==[2]
    assert authority['input_sha256']==current['input_sha256'] and authority['maximum_steps']<=1005000
    assert authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert authority['absolute_deadline_unix']<=1795395600 and authority['hard_stop_monotonic']<=parent['hard_stop_monotonic']
    assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock'
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    frozen=authority['source_hashes'];assert frozen and all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in frozen.items())
    controller=exact('v1483_independent_MPPI_identity',Path(__file__).with_name('controller_identity.py'));controller.verify_current(current)
    source=backend_binding()
    Predictor,initial,kernel,Adapter,Geometry,Gear,Capture=source.binding()
    import numpy as np
    result=dict(passed=False,closed=False,input_sha256=current['input_sha256'],controller_identity_sha256=current['controller_identity_sha256'],qualified_method=current['method_spec']['method'],geometry_kind=current['geometry_kind'],causal_snapshot_sha256=current['causal_snapshot_sha256'],audit_analytical_native=0,audit_inflight_unknown=False,predictor_constructions=0,predictor_construction_inflight_unknown=False,private_branch_copies=0,physical_native=0,mujoco_models=0,replay_native=0,physical_admission=False)
    maximum=0.;minimum=math.inf;start=time.monotonic();end=min(start+1800,authority['hard_stop_monotonic']-30)
    def step(p,v,w):
        assert result['audit_analytical_native']<authority['maximum_steps'] and time.monotonic()<end and time.time()<authority['absolute_deadline_unix']-30
        result['audit_inflight_unknown']=True;s,u=p.step(v,w,False);result['audit_analytical_native']+=1;result['audit_inflight_unknown']=False;return s,u
    def compare(a,b):
        nonlocal maximum
        assert np.shape(a)==np.shape(b)
        maximum=max(maximum,float(np.max(np.abs(np.asarray(a)-np.asarray(b)))))
        assert maximum<=1e-8, 'CURRENT_WITNESS_NUMERICAL_REPLAY_DIVERGED'
    def body(p):s=p.state;return [float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])]
    try:
        original=dict(current);identity=original.pop('input_sha256')
        assert hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==identity
        index=json.loads((Path(branch_folder)/'INDEX.json').read_text());rows=index['branches']
        assert index['closed'] and index['input_sha256']==identity
        reader=BranchReader(branch_folder,index,np)
        nominal=np.asarray(evidence['states']);ctrl=np.asarray(evidence['ctrl']);journal=evidence['journal'];memory=evidence['memory'];modes=evidence['modes']
        n=len(journal);assert nominal.shape==(n+1,8) and ctrl.shape==(n,4) and len(rows)==len(memory)==len(modes)==n
        assert n>=200 and 201*n<=authority['maximum_steps']
        result['predictor_construction_inflight_unknown']=True;p=Predictor(setup,initial(current['origin']),kernel.PARAMETERS);result['predictor_constructions']=1;result['predictor_construction_inflight_unknown']=False
        assert p.adapter.__class__ is Adapter
        p.adapter.encoders=lambda owner=p:source.feedback.current(owner)
        p.adapter.parked_target=current['origin']['parked_target'];p.adapter._steering_motion_active=current['origin']['steering_motion_active']
        method=source.Method(current);accepted=evidence.get('modeled_mppi_replies',[]);replies={r['sequence']:r for r in accepted if r['kind']=='COHERENT_MPPI_MODELED_COMMAND'};previous_mppi=None
        gate=Gear()
        for key,value in current['gear_memory'].items():setattr(gate,key,value)
        forecast=current['bridge_forecast'];geometry=source.geometry_binding.GeometryBinding(current,setup);compare(p.state,nominal[0])
        for i,row in enumerate(journal):
            assert row['before_native']==current['origin']['native_tick']+i and rows[i]['index']==i and rows[i]['proof']['before_native']==row['before_native'] and rows[i]['proof']['input_sha256']==identity
            assert rows[i]['proof']['geometry_kind']==current['geometry_kind']and rows[i]['proof']['causal_snapshot_sha256']==current['causal_snapshot_sha256']
            compare([*p.adapter.last.tolist(),float(p.adapter.integral)],memory[i])
            decision=method.select(body(p),row['before_native'],source.feedback.current(p),p.adapter.last)
            expected_phase=decision['phase'];expected_request=decision['requested']
            if expected_phase=='MPPI':
                if row['stage']=='FINAL_TAIL':
                    done=[r for r in accepted if r['kind']=='MPPI_ACTION_DONE'and r['native_tick']==row['before_native']]
                    assert len(done)==1 and done[0]['controller_identity_sha256']==current['controller_identity_sha256']and done[0]['input_sha256']==identity and done[0]['body']==body(p)and done[0]['status']==4 and done[0]['error_code']==0,'COHERENT_MPPI_DONE_SOURCE_MISSING'
                    method.mppi_done(row['before_native']);expected_phase='FINAL_TAIL';expected_request=[0.,0.]
                else:
                    assert row['mppi_sequence']in replies
                    reply=replies[row['mppi_sequence']];assert reply['controller_identity_sha256']==current['controller_identity_sha256']and reply['input_sha256']==identity and reply['not_measured_response']is True
                    if previous_mppi!=reply['sequence']:assert reply['native_tick']==row['before_native']and reply['body']==body(p)
                    else:assert 0<=row['before_native']-reply['native_tick']<5
                    previous_mppi=reply['sequence'];expected_request=[reply['v'],reply['w']]
                    checked=row['modeled_command_checked_monotonic'];assert 0<=checked-reply['origin']['generated_monotonic']<=.2
            assert expected_phase==row['stage']and list(expected_request)==row['requested']and row['qualified_method']==method.name, 'FINITE_METHOD_ACTION_OR_PHASE_CHANGED'
            assert modes[i]['parked_target']==decision['parked_target']
            assert row['control_owner']==('ENGINEERING_COHERENT_MPPI'if expected_phase=='MPPI'else'DISCLOSED_SHARED_EXECUTION_BRIDGE')
            assert p.coupled_episode==modes[i]['coupled_episode']and bool(getattr(p.adapter,'_steering_motion_active',False))==modes[i]['steering_motion_active']
            saved_states,saved_ctrl=reader.read(rows[i]);compare(p.state,saved_states[0])
            branch=source.clone_private_branch(p,lambda a,b:np.r_[a,b]);result['private_branch_copies']+=1;branch.adapter.parked_target=None
            for j in range(200):
                s,u=step(branch,0.,0.);compare(s,saved_states[j+1]);compare(u,saved_ctrl[j])
            lower=geometry.tube(saved_states,row['before_native']);minimum=min(minimum,lower)
            assert lower>=.22-1e-8 and abs(lower-rows[i]['proof']['causal_tube_lower_m'])<=1e-8
            assert abs(branch.state[[3,4,5]]).max()<=.003 and max(abs(x)for x in source.feedback.current(branch)[2:])<=.03 and abs(branch.adapter.last[2:]).max()<=1e-10
            assert (abs(saved_states[:,3:6])<=np.array([.13,.03,.16])+1e-8).all()
            vr,wr,proof=gate.select(*row['requested'],native_tick=row['before_native'],body=body(p),last_ctrl=p.adapter.last,encoders=source.feedback.current(p))
            assert [vr,wr]==row['admitted']and proof==row['gear']
            method.observe_gear(row['before_native'],proof)
            p.adapter.parked_target=modes[i]['parked_target'];s,u=step(p,vr,wr);compare(s,nominal[i+1]);compare(u,ctrl[i])
        reader.finish()
        goal=current['next_segment']['poses'][-1];s=p.state;rear=[s[0]-.3*math.cos(s[2]),s[1]-.3*math.sin(s[2]),s[2]]
        checks=dict(all_model_state_ctrl_error=maximum<=1e-8,complete_branch_coverage=len(rows)==n,whole_nominal_tube=geometry.tube(nominal,current['origin']['native_tick'])>=.22-1e-8,
                    complete200_zero_tail=all(r['zero_tail']and r['admitted']==[0.,0.]for r in journal[-200:]),
                    endpoint_position=math.dist(rear[:2],goal[:2])<=.12,endpoint_heading=abs(math.atan2(math.sin(rear[2]-goal[2]),math.cos(rear[2]-goal[2])))<=.20,
                    body_rest=max(abs(x)for x in body(p)[3:])<=.003,steering_rest=max(abs(x)for x in source.feedback.current(p)[2:])<=.03,rear_zero=abs(p.adapter.last[2:]).max()<=1e-10)
        result.update(passed=all(checks.values()),checks=checks,nominal_native=n,braking_origins=len(rows),model_error=maximum,minimum_braking_tube_m=minimum)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        unchanged=all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in frozen.items())
        result.update(closed=True,passed=result['passed']and unchanged,source_unchanged=unchanged,wall_s=time.monotonic()-start)
    return result
