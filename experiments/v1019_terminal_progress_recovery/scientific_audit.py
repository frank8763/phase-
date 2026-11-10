"""Saved-only full navigation audit, including every committed recovery input."""
import gzip,hashlib,importlib.util,json,math,sys,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads(Path(p).read_text())
def gz(p):return json.loads(gzip.decompress(Path(p).read_bytes()))
def physical_body(q,v):
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    return np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]

def own_inputs(out,task,body,q,v,ctrl,setup):
    sys.path.insert(0,str(R/'experiments/v1003_causal_recovery_execution'))
    from plan import predict,geometry
    from predictor import fixture,law
    timeline=read(out/'PROFILE_EXECUTION.json');events={x['native_tick']:x for x in timeline['adapter_switches']};commands=read(out/'physics/BODY_COMMANDS.json')
    adapter=fixture.make(law.base.Adapter,setup);control_error=feedback_error=0.;memory={}
    for i,row in enumerate(commands):
        memory[i]=dict(last_ctrl=adapter.last.copy(),integral=adapter.integral)
        if i in events:
            event=events[i];new=fixture.make(law.Adapter if event['adapter']=='V993'else law.base.Adapter,setup)
            assert event['physical_state_unchanged']and np.max(abs(event['last_ctrl']-adapter.last))<=1e-8 and abs(event['integral']-adapter.integral)<=1e-8
            new.last=adapter.last.copy();new.integral=adapter.integral;new.virtual_rate=.6;adapter=new
        if i:feedback_error=max(feedback_error,float(abs(np.array(row[3:5])-body[i-1,3:5]).max()))
        u=adapter.compute(*row[1:6]);control_error=max(control_error,float(abs(u-ctrl[i]).max()))
    assert control_error<=1e-8 and feedback_error<=1e-8,'ACTUATOR_OR_ACTUAL_FEEDBACK_NOT_RECONSTRUCTIBLE'
    journal=gz(out/'MOTION_ENVELOPE.json.gz');from periodic_support import PeriodicSupport
    periodic=PeriodicSupport();snapshots={}
    for state in journal['states']:
        periodic.update(state['time'],state['native_tick'],state['support_bounds']);snapshots[state['native_tick']]=None if periodic.last is None else periodic.snapshot()
    reports=[];profile_ranges={};recovery_rows=read(out/'RECOVERY_CORRIDORS.json')
    for item in timeline['profiles']:
        raw=Path(item['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==item['sha256']
        record=json.loads(raw);plan=record['plan'];packet=record['packet'];source=record['source'];start=item['start_native_tick'];end=item.get('end_native_tick')
        assert item['completed']and end is not None and end-start==len(plan['planned_body_requests'])
        assert plan['original_goal']==task['goal_xy']and plan['source_native_tick']==source['source_native_tick']<=packet['native_tick']<=start
        index=packet['native_tick']-1
        assert abs(np.array(packet['body'])-body[index]).max()<=1e-8 and abs(np.array(packet['steering']['position'])-q[index,setup['steering_qpos_addresses']]).max()<=1e-8
        expected=snapshots[source['source_native_tick']];assert expected is not None
        assert all(expected[k]==source['periodic'][k]for k in ['omega','amplitude','last','source_tick'])
        assert all(np.allclose(a,b,rtol=0,atol=1e-9)for a,b in zip(expected['vertices'],source['periodic']['vertices'])),'PROFILE_SOURCE_NOT_CAUSAL'
        mem=memory[packet['native_tick']];assert abs(mem['last_ctrl']-plan['initial']['last_ctrl']).max()<=1e-8 and abs(mem['integral']-plan['initial']['integral'])<=1e-8
        states,controls,requests=predict(setup,plan['initial'],plan['edge_targets'])
        assert np.allclose(states,np.asarray(plan['state_path']),rtol=0.,atol=1e-12)and np.array_equal(controls,np.asarray(plan['predicted_actuator_controls']))and requests==plan['planned_body_requests']
        assert np.allclose(states[:,:3],np.array(plan['path']),rtol=0.,atol=1e-12)
        sys.path.insert(0,str(R/'experiments/v997_input_consistent_recovery'));from saved_qualification import independently_check_geometry
        raw_clear=independently_check_geometry(np.c_[states[:,:3],states[:,6]],setup['known'],source['periodic'])
        lower=raw_clear-geometry.SPATIAL-.005*(.13+math.hypot(.44,.375)*.16)
        assert lower>=.155 and raw_clear>=plan['required_raw_clearance_m']
        assert all(commands[start+j][1:3]+[commands[start+j][5]]==req for j,req in enumerate(requests)),'RECOVERY_INPUT_REPLACED'
        actual=np.vstack([body[start-1],body[start:end]]);pe=np.linalg.norm(actual[:,:2]-states[:,:2],axis=1);d=actual[:,2]-states[:,2];ae=abs(np.arctan2(np.sin(d),np.cos(d)))
        progress=float(np.linalg.norm(body[start-1,:2]-task['goal_xy'])-np.linalg.norm(body[end-1,:2]-task['goal_xy']))
        capture=plan.get('goal_capture')is True
        if capture:
            upper=float(np.linalg.norm(states[-1,:2]-task['goal_xy']))+.08
            assert abs(upper-plan['terminal_goal_distance_upper_m'])<=1e-12 and upper<=.45 and np.linalg.norm(body[end-1,:2]-task['goal_xy'])<=.45,'GOAL_CAPTURE_PREDICTED_OR_ACTUAL_FAILED'
        assert pe.max()<=.04 and ae.max()<=.035 and (progress>=.4 or capture),'RECOVERY_ACTUAL_TRACKING_OR_PROGRESS'
        assert requests[-200:]==[[0.,0.,False]]*200 and np.linalg.norm(v[end-50:end,:2],axis=1).max()<=.03 and abs(v[end-50:end,5]).max()<=.03 and abs(v[end-50:end][:,setup['steering_qvel_addresses']]).max()<=.03
        row=next(x for x in recovery_rows if x.get('profile_id')==item['profile_id']);assert row['passed']and abs(row['actual_goal_progress_m']-progress)<=.004
        reports.append(dict(profile_id=item['profile_id'],passed=True,start=start,end=end,independent_lower_m=lower,actual_progress_m=progress,maximum_position_error_m=float(pe.max()),maximum_heading_error_rad=float(ae.max())))
        for j in range(start+1,end+1):profile_ranges[j]=(item['profile_id'],j-start-1,requests[j-start-1])
    ingress=gz(out/'INGRESS.json.gz');proofs=[r['proof']for r in gz(out/'COMMAND_TUBES.json.gz')if r['proof']['passed']]
    assert len(ingress['execution'])==len(body)and not any(e['decision']=='REJECTED_ABORT'for e in ingress['receipts'])
    active=None;phase='WAITING';receipts=iter(ingress['receipts']);next_event=next(receipts,None);owned=None;holding=False
    for tick,step in enumerate(ingress['execution'],1):
        while next_event is not None and next_event['native_tick']<tick:
            e=next_event;p=e['packet'];assert p['run_id']==task['run_id']
            if p['kind']=='arm':phase='RUNNING'
            elif p['kind']=='stop':phase='STOPPING'
            elif p['kind']=='commit_profile':
                assert e['decision']=='PROFILE_COMMITTED'and 0<=e['received_at']-p['issued_at']<=.05;owned=p['profile_id'];active=None
            elif p['kind']=='release_profile':assert e['decision']=='PROFILE_RELEASED';owned=None;holding=False;active=None
            elif p['kind']=='command':
                if e['decision']=='ACCEPTED':
                    assert owned is None and p['tube']in proofs and 0<=e['received_at']-p['issued_at']<=.05;active=p
                elif e['decision']=='LATE_NEW_COMMAND_DISCARDED':assert .05<e['received_at']-p['issued_at']<=.2 and active is not None
                else:assert e['decision']in ['PROFILE_OWNER_IGNORED','POST_STOP_COMMAND_IGNORED']
            next_event=next(receipts,None)
        assert step['native_tick']==tick and step['completed']and step['controls']==commands[tick-1][1:3]+[commands[tick-1][5]],'UNCHECKED_NATIVE_INPUT'
        if tick in profile_ranges:
            pid,index,request=profile_ranges[tick];assert owned==pid and step['owner']=='COMMITTED_RECOVERY'and step['profile_index']==index and step['controls']==request
        elif step['owner']=='RECOVERY_STOP_HOLD':assert owned is not None and step['controls']==[0.,0.,False]
        else:
            assert owned is None
            expected=[0.,0.,True]if phase!='RUNNING'or active is None or step['at']-active['issued_at']>.2 else[active['v'],active['w'],False]
            assert step['controls']==expected,'NORMAL_INPUT_OWNER_OR_EXPIRY'
            if active is not None:
                from cycle_backup import retained_allowed
                from command_tube import nominal
                p=active['tube'];dt=(tick-p['body_native_tick'])*.01;assert retained_allowed(p,dt)
                pose=nominal(p['body'],p['v'],p['w'],[dt])[0];delay=p['body_age_s']+.05;r=body[tick-1]
                assert np.linalg.norm(r[:2]-pose[:2])<=p['residual_position_m']+.13*delay+1e-8
                assert abs(math.atan2(math.sin(r[2]-pose[2]),math.cos(r[2]-pose[2])))<=.035+.16*delay+1e-8
        assert abs(body[tick-1,3])<=.13 and abs(body[tick-1,4])<=.16
    return dict(passed=True,profiles=reports,maximum_actuator_reconstruction_error=control_error,maximum_actual_feedback_error=feedback_error,all_native_inputs_checked=len(commands))

def audit(task):
    out=Path(task['output'])
    try:
        original=load('v1004_original_full_physical_audit',R/'experiments/v858_nav2_verified/audit_navigation.py');result=original.audit(task)
        n=read(out/'RESULT.json');ros=read(out/'ROS_RESULT.json');setup=read(out/'physics/SETUP.json')
        with np.load(out/'physics/NATIVE_TRACE.npz')as z:q=z['qpos'];v=z['qvel'];ctrl=z['ctrl'][:,setup['actuator_ids']]
        body=physical_body(q,v);startup=load('v1004_original_startup_checks',R/'experiments/v862_ready_static/audit_result.py').startup_checks(n,ros)
        assert all(startup.values())and read(out/'physics/SELECTED_NATIVE_BINDING.json')['passed']and read(out/'physics/EXACT_SENSOR_BINDING.json')['passed']
        prior=read(Path(task['preflight_output'])/'SETUP.json');from repeat_contract import canonical_setup
        initial=np.load(out/'physics/INITIAL_STATE.npz')['state'];pinitial=np.load(Path(task['preflight_output'])/'INITIAL_STATE.npz')['state']
        assert canonical_setup(setup)==canonical_setup(prior)and np.max(abs(initial-pinitial))<=1e-8
        from motion_audit import audit as motion_audit
        motion=motion_audit(out);assert motion['passed'],'CAUSAL_SENSOR_FORECAST_MAP_OR_PLANNER_AUDIT'
        from tube_audit import audit_tubes
        tubes=audit_tubes(out);assert tubes['passed']
        from shaping_audit import audit as shaping_audit
        shaping=shaping_audit(out);assert shaping['passed']
        inputs=own_inputs(out,task,body,q,v,ctrl,setup)
        from handoff_audit import audit as audit_handoff
        result['atomic_handoff']=audit_handoff(out);assert result['atomic_handoff']['passed']
        master=ros['global_master_readiness'];assert master['passed']and master['native_tick']==0 and len(master['accepted_replies'])==2
        actor=setup['actor'];assert actor['phase_rad']==task['phase']and actor['maximum_speed_m_s']==.08 and actor['amplitude_m']==.25 and actor['radius_m']==.1
        assert np.linalg.norm(v[-50:,:2],axis=1).max()<=.03 and abs(v[-50:,5]).max()<=.03 and abs(v[-50:][:,setup['steering_qvel_addresses']]).max()<=.03
        result.update(input_consistent_recovery=inputs,startup=startup,motion=motion,tubes=tubes,shaping=shaping,complete_stop=True)
        result['passed']=bool(result['passed']and n['passed']);result['scope']='V1014 empirical finite single-actor Nav2 navigation with atomic stopped handoff; no328-step/global/RAS safety claim'
    except BaseException as e:result=dict(passed=False,evidence_passed=False,error=repr(e),traceback=traceback.format_exc(),models_during_audit=0)
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
