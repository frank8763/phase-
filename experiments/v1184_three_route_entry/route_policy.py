"""Regenerate a finite library source at the current full measured state.

NS retains the qualified pose feedback. EW retains signed velocity feedback
and timed pose monitoring; it is not advertised as a new reverse pose law.
"""
from route_tools import *
def state(v):return np.array(q.initial(packet(v))['state'])
def command(actual,reference,target,speed,park):
    if park or speed==0.:return 0.,0.
    if speed==.12:
        v,w,_=q.tracking.request(actual,reference,target,speed);return v,w
    assert speed in[-.03,.08]
    return float(speed),float(speed)*math.tan(target)/.6
def run(v,setup,x,rows,ss,permit,checkpoint):
    start=v.count;org=dict(q.initial(packet(v)),steering_load_episode=False)
    shadow=q.model.Predictor(setup,org);sh=[shadow.state.copy()];log=[];maximum=np.zeros(3);posemax=np.zeros(2)
    index=0;parked=False;anchor=None;capture=0;target=ss[-1,:3].copy()
    def step(vr,wr,mode,turn,refindex,phase):
        nonlocal index,maximum,posemax,parked,anchor
        assert permit(),'FULL_ROUTE_DEADLINE_RESERVE'
        p=packet(v);actual=state(v);previous.body_gate(p)
        if mode and not parked:
            assert previous.stopped(p),'PARK_MODE_ENTRY_REQUIRES_REST';anchor=actual[:3].copy()
        if abs(vr)>=.005:anchor=None
        shadow.adapter.parked_target=float(turn)if mode else None
        expected,_=shadow.step(float(vr),float(wr),False);sh.append(expected.copy())
        v.adapter.parked_target=float(turn)if mode else None
        before=v.count;v.step(float(vr),float(wr),False);assert v.count==before+1
        actual=state(v);d=actual-expected;e=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])]);maximum=np.maximum(maximum,e)
        d=actual-ss[refindex];pe=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2])))]);posemax=np.maximum(posemax,pe)
        log.append(dict(before_native=before,reference_index=refindex,phase=phase,parked_target=float(turn)if mode else None,request=[float(vr),float(wr),False],response_error=e,pose_error=pe))
        assert(e<=[.04,.035,.015]).all(),'ACTUAL_RESPONSE_REFUSED'
        assert(pe<=[.04,.035]).all(),'ACTUAL_REFERENCE_REFUSED'
        if anchor is not None:assert np.linalg.norm(actual[:2]-anchor[:2])<=.02 and abs(math.atan2(math.sin(actual[2]-anchor[2]),math.cos(actual[2]-anchor[2])))<=.1,'PARK_ENVELOPE_REFUSED'
        if mode:assert abs(actual[3])<=.01 and abs(v.d.ctrl[v.adapter.commands.ids[2:]]).max()<=1e-10,'PARK_BODY_OR_REAR_CTRL'
        if v.count%5==0:v.scan()
        index+=1;parked=bool(mode)
        if index%500==0:checkpoint(dict(stage='fresh_'+setup['case']['id']+'_recovery',absolute_native=v.count,local_native=index,total_reference_native=len(ss)-1))
    try:
        for turn,speed,n,mode in rows:
            for _ in range(int(n)):
                vr,wr=command(state(v),ss[index],float(turn),float(speed),bool(mode));step(vr,wr,bool(mode),turn,index+1,'reference')
        assert previous.stopped(packet(v)),'COMPLETE_REFERENCE_STOP_REQUIRED'
        if np.linalg.norm(state(v)[:2]-target[:2])>.025:
            for _ in range(600):
                vr,wr,status=q.capture.request(state(v),target)
                if status=='CAPTURED':break
                assert status=='CAPTURING','FORWARD_CAPTURE_REFUSED'
                step(vr,wr,False,0.,len(ss)-1,'capture');capture+=1
            else:raise AssertionError('CAPTURE_NATIVE_CAP')
        for _ in range(2200):step(0.,0.,False,0.,len(ss)-1,'final_stop')
        final=state(v);goal=float(np.linalg.norm(final[:2]-x['goal']));distance=float(np.linalg.norm(final[:2]-target[:2]));yaw=abs(math.atan2(math.sin(final[2]-target[2]),math.cos(final[2]-target[2])))
        assert previous.stopped(packet(v))and distance<=.025 and yaw<=.1 and goal+.08<=.45,'FINAL_TERMINAL_OR_GOAL_REFUSED'
        return dict(passed=True,start_native=start,recovery_native=index,capture_native=capture,goal_distance_m=goal,maximum_response_error=maximum,maximum_reference_pose_error=posemax,final_stop_executed=True,formal_retained_commit=False)
    finally:
        v._route_shadow=np.array(sh);v._route_journal=log;v._route_python_native=len(sh)-1;v.adapter.parked_target=None
def execute(v,setup,original,end,evidence,out,packet_fn,output):
    case=setup['case']['id']
    if case=='WEST_EAST':return bridge.execute(v,setup,original,end,evidence,out,packet_fn,output)
    nominal,rows=finite_plan(case);e,meta=bridge.fresh_evidence(v,setup);p=packet(v)
    assert e.first is not None and previous.stopped(p),'FRESH_DISCOVERY_AND_REST_REQUIRED'
    x=dict(setup=setup,packet=p,source=e.source(v),goal=setup['case']['goal_xy'],safe_terminal_pose=nominal['safe_terminal_pose'])
    assert x['source']['source_native_tick']<=v.count and 0<=x['source']['source_age_s']<=.051
    dump(out/'ROUTE_RECOVERY_INPUT.json',x);dump(out/'ROUTE_SOURCE_PROVENANCE.json',meta)
    table,calls=bridge.joint_table(x['source']);np.savez_compressed(out/'ROUTE_JOINT_TABLE.npz',**table)
    engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);org=dict(q.initial(p),steering_load_episode=False);ss,uu,mm=engine.simulate(org,rows)
    g=q.Geometry(x,table);proof,rr=g.final(x,ss,uu,rows);proof['checks']['memory_complete']=bool(mm.shape==(len(ss),5)and np.array_equal(mm[1:,:4],uu));proof['passed']=bool(all(proof['checks'].values()));dump(out/'ROUTE_REFERENCE_PROOF.json',proof)
    v._chain_counts=dict(cpp_native=engine.native,LP_calls=calls,python_native=0)
    assert proof['passed'],'CURRENT_FULL_STATE_SOURCE_REFUSED'
    np.savez_compressed(out/'ROUTE_REFERENCE.npz',states=ss,controls=uu,memory=mm);dump(out/'ROUTE_ROWS.json',rows)
    v._chain_phase='route_recovery'
    try:answer=run(v,setup,x,rows,ss,lambda:time.time()<end-150 and remaining()>180,lambda z:dump(out/'PARTIAL_PROGRESS.json',z))
    finally:
        if hasattr(v,'_route_shadow'):
            np.savez_compressed(out/'ROUTE_SHADOW.npz',states=v._route_shadow);dump(out/'ROUTE_POLICY_JOURNAL.json',v._route_journal);v._chain_counts['python_native']=v._route_python_native
    shadow=v._route_shadow;minimum=float(np.minimum(*g.components(shadow[:,:3],np.arange(len(shadow)))).min())
    assert minimum>=q.REQUIRED and g.cycle(state(v)[None,:3])[0]>=q.REQUIRED,'COMPLETE_EXECUTED_SHADOW_OR_REFUGE_REFUSED'
    answer.update(minimum_shadow_raw=minimum,causal_current_run_source=True,finite_known_course_library=True);dump(out/'ROUTE_POLICY_RESULT.json',answer);return answer
