"""Vehicle-interface goal phase; no physical factory or launch code."""
import copy
import math
import time
from current_goal_source import q,np,generate,PreviewGeometry
from admission import predictor_origin
from current_state_tools import validate_input,original


def measured_origin(packet,load_episode):
    assert type(load_episode)is bool,'EXPLICIT_MEASURED_LOAD_MODE'
    assert not packet.get('coupled_episode',False) and not packet.get('steering_motion_active',False),'GOAL_MODE_CONFLICT'
    assert type(packet['native_tick'])is int and packet['steering']['native_tick']==packet['native_tick']
    assert abs(packet['sim_time']-.01*packet['native_tick'])<=1e-8,'GOAL_PACKET_CLOCK'
    original.previous.body_gate(packet)
    origin=dict(q.initial(packet),steering_load_episode=load_episode)
    origin['state']=np.asarray(origin['state'],float)
    origin['last_ctrl']=np.asarray(origin['last_ctrl'],float)
    assert np.isfinite(np.r_[origin['state'],origin['last_ctrl'],origin['integral']]).all()
    return origin


def bind_current(x,packet,load_episode):
    validate_input(x)
    origin=measured_origin(packet,load_episode)
    nominal=q.initial(x['packet'])
    assert packet['native_tick']==x['packet']['native_tick'] and abs(packet['sim_time']-x['packet']['sim_time'])<=1e-8,'STALE_GOAL_CLOCK'
    assert max(float(abs(origin['state']-np.asarray(nominal['state'])).max()),
        float(abs(origin['last_ctrl']-np.asarray(nominal['last_ctrl'])).max()),
        abs(origin['integral']-nominal['integral']))<=1e-8,'STALE_GOAL_FULL_STATE_OR_MEMORY'
    assert original.previous.stopped(packet),'GOAL_REPLACEMENT_REQUIRES_REST'
    return origin


def execute(v,setup,x,table,deadline,permit,packet_fn,checkpoint,out):
    """Caller supplies real packet/step interfaces; harness supplies analytical ones."""
    assert setup==x['setup'],'GOAL_SETUP_CHANGED'
    packet=packet_fn(v);initial=bind_current(x,packet,v._live_load)
    start=v.count
    assert start==packet['native_tick']
    assert v.adapter.parked_target is None,'GOAL_ADAPTER_PARK_MODE'
    shadow=q.model.Predictor(setup,initial)
    states=[initial['state'].copy()];shadows=[initial['state'].copy()]
    controls=[];memory=[np.r_[initial['last_ctrl'],initial['integral']]];requests=[];journal=[]
    generations=[];stops=[];cpp=0;maximum=np.zeros(3);posemax=np.zeros(2);admission_work=0
    geometry=q.Geometry(x,table)

    def current():
        p=packet_fn(v)
        assert p['native_tick']==v.count and v.count-start==len(controls),'GOAL_NATIVE_COVERAGE'
        assert abs(p['sim_time']-(x['packet']['sim_time']+.01*len(controls)))<=1e-8,'GOAL_ABSOLUTE_TIME'
        origin=measured_origin(p,v._live_load)
        return p,origin

    def step(vr,wr,reference,phase,index):
        nonlocal maximum,posemax
        assert time.monotonic()<deadline and permit(),'GOAL_EXECUTION_DEADLINE'
        current();expected,_=shadow.step(float(vr),float(wr),False)
        before=v.count;v.step(float(vr),float(wr),False)
        assert v.count==before+1,'GOAL_STEP_COVERAGE'
        if vr>=.005:v._live_load=True
        p=packet_fn(v);origin=measured_origin(p,v._live_load);actual=origin['state']
        delta=actual-expected
        error=np.array([np.linalg.norm(delta[:2]),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2]))),abs(delta[6])])
        delta=actual-reference
        pose=np.array([np.linalg.norm(delta[:2]),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2])))])
        states.append(actual.copy());shadows.append(expected.copy());controls.append(origin['last_ctrl'].copy())
        memory.append(np.r_[origin['last_ctrl'],origin['integral']]);requests.append([float(vr),float(wr),0.])
        maximum=np.maximum(maximum,error);posemax=np.maximum(posemax,pose)
        journal.append(dict(native=v.count,phase=phase,reference_index=index,response_error=error,pose_error=pose))
        assert (error<=np.array([.04,.035,.015])).all(),'ACTUAL_RESPONSE_REFUSED'
        assert (pose<=np.array([.04,.035])).all(),'ACTUAL_REFERENCE_REFUSED'
        if v.count%5==0:v.scan()
        if len(controls)%500==0:checkpoint(dict(stage='current_goal_entry',native=v.count,local_native=len(controls)))

    def run_rows(rows,reference,phase):
        nonlocal cpp
        i=0
        for target,speed,count,mode in rows:
            assert not mode and speed in [0.,.12],'UNQUALIFIED_GOAL_COMMAND'
            if speed==0. and count>=2200:
                p,origin=current();engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients'])
                ss,uu,mm=engine.simulate(origin,[(0.,0.,int(count),0)])
                local=copy.deepcopy(x);local['packet']['controller_memory']['last_ctrl']=origin['last_ctrl'].tolist();local['goal']=ss[-1,:2].tolist()
                proof=q.proof(PreviewGeometry(geometry,len(controls)),local,ss,uu,q.requests_of([(0.,0.,int(count),0)]),mm)
                cpp+=engine.native;stops.append(dict(offset=len(controls),origin=origin,proof=proof))
                assert proof['passed'],'CURRENT_SCHEDULED_FULL_STOP_REFUSED'
            for _ in range(int(count)):
                if speed==0.:vr=wr=0.
                else:vr,wr,_=q.tracking.request(measured_origin(packet_fn(v),v._live_load)['state'],reference[i],float(target),float(speed))
                step(vr,wr,reference[i+1],phase,i+1);i+=1
        assert i==len(reference)-1 and original.previous.stopped(packet_fn(v)),'COMPLETE_SEGMENT_STOP_REQUIRED'

    try:
        plan=generate(x,table,initial,0,deadline,checkpoint,shadow_origin=predictor_origin(shadow));cpp+=plan['analytical_cpp_native'];admission_work+=plan['admission_python_native']
        q.dump(out/'INITIAL_SELECTION.json',{k:z for k,z in plan.items()if k not in ['states','controls','memory']})
        assert plan['passed'],'NO_CURRENT_WHOLE_GOAL_SOURCE'
        np.savez_compressed(out/'INITIAL_REFERENCE.npz',**{k:plan[k]for k in ['states','controls','memory']})
        generations.append(dict(offset=0,origin=initial,method=plan['method']))
        if plan['prefix_rows'] is not None:
            n=plan['prefix_native'];run_rows(plan['prefix_rows'],plan['states'][:n+1],'refuge_prefix')
            p,origin=current();assert original.previous.stopped(p),'REFUGE_HANDOFF_NOT_STOPPED'
            q.dump(out/'HANDOFF_PACKET.json',dict(packet=p,origin=origin,native_offset=len(controls),source_clock_unchanged=x['source']['source_native_tick']))
            onward=generate(x,table,origin,len(controls),deadline,checkpoint,onward_only=True,shadow_origin=predictor_origin(shadow));cpp+=onward['analytical_cpp_native'];admission_work+=onward['admission_python_native']
            q.dump(out/'ONWARD_SELECTION.json',{k:z for k,z in onward.items()if k not in ['states','controls','memory']})
            assert onward['passed'],'NO_MEASURED_HANDOFF_ONWARD_SOURCE'
            np.savez_compressed(out/'ONWARD_REFERENCE.npz',**{k:onward[k]for k in ['states','controls','memory']})
            generations.append(dict(offset=len(controls),origin=origin,method=onward['method']))
            plan=onward
        run_rows(plan['rows'],plan['states'],'goal_reference')
        target=plan['states'][-1,:3]
        capture=0
        if np.linalg.norm(states[-1][:2]-target[:2])>.025:
            for _ in range(600):
                vr,wr,status=q.capture.request(states[-1],target)
                if status=='CAPTURED':break
                assert status=='CAPTURING','FORWARD_CAPTURE_REFUSED'
                step(vr,wr,plan['states'][-1],'capture',len(plan['states'])-1);capture+=1
            else:raise AssertionError('CAPTURE_NATIVE_CAP')
        for _ in range(2200):step(0.,0.,plan['states'][-1],'final_stop',len(plan['states'])-1)
        arrays={k:np.asarray(z)for k,z in dict(states=states,controls=controls,memory=memory,requests=requests,shadow=shadows).items()}
        proof=q.proof(geometry,x,arrays['states'],arrays['controls'],arrays['requests'],arrays['memory'])
        shadow_proof=q.proof(geometry,x,arrays['shadow'],arrays['controls'],arrays['requests'],arrays['memory'])
        final=states[-1];distance=float(np.linalg.norm(final[:2]-target[:2]));yaw=abs(math.atan2(math.sin(final[2]-target[2]),math.cos(final[2]-target[2])))
        assert proof['passed'] and shadow_proof['passed'] and original.previous.stopped(packet_fn(v)) and distance<=.025 and yaw<=.1,'FULL_EXECUTED_GOAL_PROOF'
        result=dict(passed=True,native=len(controls),generations=generations,scheduled_stops=stops,
            maximum_response_error=maximum,maximum_reference_error=posemax,capture_native=capture,
            proof=proof,shadow_proof=shadow_proof,analytical_cpp_native=cpp,
            analytical_shadow_python_native=len(controls),admission_python_native=admission_work,formal_retained_commit=False)
        q.dump(out/'RESULT.json',result)
        return result
    finally:
        v.adapter.parked_target=None
        v._goal_trace={k:np.asarray(z)for k,z in dict(states=states,controls=controls,memory=memory,requests=requests,shadow=shadows).items()}
        v._goal_journal=journal;v._goal_cpp_native=cpp
        np.savez_compressed(out/'EXECUTED.npz',**v._goal_trace);q.dump(out/'JOURNAL.json',journal)
