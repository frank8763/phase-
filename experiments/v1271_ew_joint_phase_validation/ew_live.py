"""Certified observer component, real causal refresh, signed whole-source gate."""
from pathlib import Path
import copy,importlib.util,json,math,sys,time
C=Path(__file__).resolve().parent;R=C.parents[1]
def private(name,path):
    if name not in sys.modules:
        s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m)
    m=sys.modules[name];assert Path(m.__file__).resolve()==path.resolve(),'PRIVATE_BINDING_COLLISION';return m
component=private('phase_v1271_immutable_ew_component',R/'experiments/v1255_ew_component_entry/ew_handoff.py')
q=component.q;np=component.np
sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'))
import chain as bridge
from chain_tools import packet,previous
read=lambda p:json.loads(Path(p).read_text())

def initialize_component_adapter(v):
    """Materialize the allocator's existing implicit non-parked default only."""
    p=packet(v);previous.body_gate(p)
    assert previous.stopped(p),'EW_ADAPTER_ENTRY_REQUIRES_REST'
    assert getattr(v.adapter,'parked_target',None)is None and not getattr(v.adapter,'_steering_motion_active',False),'EW_ACTIVE_PARK_MODE_AT_ENTRY'
    prior=np.asarray(v.adapter.last).copy();integral=float(v.adapter.integral);native=v.count
    assert np.isfinite(np.r_[prior,integral]).all(),'EW_ADAPTER_MEMORY_FINITE'
    v.adapter.parked_target=None
    assert np.array_equal(prior,v.adapter.last)and integral==v.adapter.integral and native==v.count,'EW_ADAPTER_INIT_MUTATED_MEMORY_OR_STATE'

def refresh(v,setup,out,name,*,after_native=None):
    p=packet(v)
    assert previous.stopped(p),'EW_REFRESH_REQUIRES_ACTUAL_REST'
    assert v.sensor_rows and max(s['native_tick']for s in v.sensor_rows)<=v.count,'EW_FUTURE_SENSOR_PACKET'
    if after_native is not None:
        assert any(after_native<s['native_tick']<=v.count for s in v.sensor_rows),'EW_MISSING_NEW_ACTUAL_SENSOR_PACKETS'
    evidence,meta=bridge.fresh_evidence(v,setup);x=bridge.current_input(v,setup,evidence);x['goal']=setup['case']['goal_xy']
    assert x['setup']['case']['id']=='EAST_WEST'and x['goal']==[-4.,-2.],'EW_GOAL_SCOPE'
    q.dump(out/(name+'_INPUT.json'),x);q.dump(out/(name+'_PROVENANCE.json'),meta)
    table,calls=bridge.joint_table(x['source']);np.savez_compressed(out/(name+'_TABLE.npz'),**table)
    return x,table,calls

def select_onward(x,table,load,deadline,checkpoint=lambda _:None):
    path=C/'timed_source.py'
    module=private('phase_v1271_current_time_source',path)
    return module.generate(x,table,load,deadline,checkpoint)

def run_onward(v,x,table,plan,deadline,permit,packet_fn,checkpoint=lambda _:None):
    start=v.count;origin=component.entry.bind_current(x,packet_fn(v),plan['initial_load'])
    assert plan['passed']and origin['steering_load_episode']==v._live_load
    shadow=q.model.Predictor(x['setup'],origin);ref=plan['states'];g=q.Geometry(x,table)
    states=[origin['state'].copy()];shadows=[origin['state'].copy()];controls=[];memory=[np.r_[origin['last_ctrl'],origin['integral']]];journal=[];requests=[]
    cursor=0;parked=False;anchor=None
    try:
        for rowindex,(turn,speed,count,mode)in enumerate(plan['rows']):
            assert speed in[-.03,0.,.08]and mode in[0,1],'EW_SOURCE_COMMAND_SCOPE'
            if mode and not parked:
                assert previous.stopped(packet_fn(v)),'EW_PARK_ENTRY_REST';anchor=np.asarray(q.initial(packet_fn(v))['state'])[:3].copy()
                assert g.cycle(anchor[None,:])[0]-.02-math.hypot(.44,.375)*.1>=q.REQUIRED,'EW_PARK_ENTRY_ENVELOPE'
            if abs(speed)>=.005:anchor=None
            for _ in range(int(count)):
                assert time.monotonic()<deadline and permit(),'EW_ONWARD_EXECUTION_DEADLINE'
                p=packet_fn(v);previous.body_gate(p)
                assert p['native_tick']==v.count==start+cursor and abs(p['sim_time']-x['packet']['sim_time']-.01*cursor)<=1e-8,'EW_ONWARD_CLOCK'
                vr=float(speed);wr=0. if mode or vr==0. else vr*math.tan(float(turn))/.6
                shadow.adapter.parked_target=float(turn)if mode else None
                predicted,_=shadow.step(vr,wr,False);v.adapter.parked_target=float(turn)if mode else None
                before=v.count;v.step(vr,wr,False);assert v.count==before+1
                if vr>=.005:v._live_load=True
                elif vr<=-.005:v._live_load=False
                after=packet_fn(v);actual=np.asarray(q.initial(after)['state']);cursor+=1
                d=actual-predicted;err=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])])
                d=actual-ref[cursor];pose=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2])))])
                states.append(actual);shadows.append(predicted);controls.append(np.asarray(after['controller_memory']['last_ctrl']));memory.append(np.r_[after['controller_memory']['last_ctrl'],after['controller_memory']['integral']]);requests.append([vr,wr,0.])
                journal.append(dict(native=v.count,row=rowindex,request=[vr,wr,False],parked_target=float(turn)if mode else None,response_error=err,pose_error=pose))
                assert(err<=[.04,.035,.015]).all()and(pose<=[.04,.035]).all(),'EW_ACTUAL_RESPONSE_OR_REFERENCE'
                if anchor is not None:
                    assert np.linalg.norm(actual[:2]-anchor[:2])<=.02 and abs(math.atan2(math.sin(actual[2]-anchor[2]),math.cos(actual[2]-anchor[2])))<=.1,'EW_PARK_PHYSICAL_DRIFT'
                if mode:assert abs(actual[3])<=.01 and abs(v.d.ctrl[v.adapter.commands.ids[2:]]).max()<=1e-10,'EW_PARK_BODY_REAR_CTRL'
                if v.count%5==0:v.scan()
                if cursor%500==0:checkpoint(dict(stage='ew_refreshed_execution',native=v.count,local_native=cursor,total=len(ref)-1))
            parked=bool(mode)
        assert cursor==len(ref)-1 and previous.stopped(packet_fn(v)),'EW_FULL_ONWARD_STOP'
        sh=np.asarray(shadows);actual=states[-1];delta=actual-ref[-1]
        assert np.minimum(*g.components(sh[:,:3],np.arange(len(sh)))).min()>=q.REQUIRED and g.cycle(actual[None,:3])[0]>=q.REQUIRED,'EW_FULL_SHADOW_PROOF'
        assert np.linalg.norm(delta[:2])<=.025 and abs(math.atan2(math.sin(delta[2]),math.cos(delta[2])))<=.1,'EW_TERMINAL_REFERENCE'
        assert np.linalg.norm(actual[:2]-x['goal'])+.08<=.45,'EW_ORIGINAL_GOAL'
        return dict(passed=True,native=cursor,goal_distance_m=float(np.linalg.norm(actual[:2]-x['goal'])),no_unqualified_capture=True)
    finally:
        v.adapter.parked_target=None
        v._ew_onward_trace={k:np.asarray(a)for k,a in dict(states=states,shadow=shadows,controls=controls,memory=memory,requests=requests).items()}
        v._ew_onward_journal=journal

def execute(v,setup,original,end,evidence,out,packet_fn,output,*,remaining_fn):
    assert setup['case']['id']=='EAST_WEST'and remaining_fn()>400 and time.time()<end-300,'EW_SCOPE_OR_TIME'
    deadline=time.monotonic()+max(0.,end-time.time()-120)
    x,table,calls=refresh(v,setup,out,'EW_OBSERVATION');entry=v.count;v._chain_phase='ew_observation';v._chain_episode=False;v._live_load=False
    v._chain_counts=dict(cpp_native=0,python_native=0,LP_calls=calls)
    initialize_component_adapter(v)
    result=component.execute(v,x,table,deadline,packet,lambda p:q.dump(out/'PARTIAL_PROGRESS.json',p))
    plan=result['plan'];q.dump(out/'EW_OBSERVATION_SELECTION.json',{k:a for k,a in plan.items()if k not in['states','controls','memory']})
    np.savez_compressed(out/'EW_OBSERVATION_REFERENCE.npz',**{k:plan[k]for k in ['states','controls','memory']})
    np.savez_compressed(out/'EW_OBSERVATION_EXECUTED.npz',**result['arrays']);q.dump(out/'EW_OBSERVATION_JOURNAL.json',result['journal'])
    q.dump(out/'EW_OBSERVATION_RESULT.json',{k:a for k,a in result.items()if k not in['plan','arrays','journal']})
    v._chain_counts.update(cpp_native=plan['analytical_cpp_native'],python_native=2*result['native'])
    v.scan() # genuine physical scan at the handoff; analytical substitutes do not append evidence
    fresh,ft,calls=refresh(v,setup,out,'EW_ONWARD',after_native=entry);v._chain_counts['LP_calls']+=calls
    q.dump(out/'EW_HANDOFF.json',dict(entry_native=entry,handoff_native=v.count,component_native=result['native'],actual_load=v._live_load,
        source_changed_by_real_current_run_packets=True,old_source_tick=x['source']['source_native_tick'],new_source_tick=fresh['source']['source_native_tick']))
    selected=select_onward(fresh,ft,v._live_load,deadline,lambda p:q.dump(out/'PARTIAL_PROGRESS.json',p));v._chain_counts['cpp_native']+=selected['analytical_cpp_native']
    q.dump(out/'EW_ONWARD_SELECTION.json',{k:a for k,a in selected.items()if k not in['states','controls','memory']})
    assert selected['passed'],'EW_FRESH_DOMAIN_SOURCE_REFUSED'
    np.savez_compressed(out/'EW_ONWARD_REFERENCE.npz',**{k:selected[k]for k in['states','controls','memory']});v._chain_phase='ew_refreshed_goal'
    try:
        onward=run_onward(v,fresh,ft,selected,deadline,lambda:time.time()<end-120 and remaining_fn()>150,packet,lambda p:q.dump(out/'PARTIAL_PROGRESS.json',p))
    finally:
        if hasattr(v,'_ew_onward_trace'):
            np.savez_compressed(out/'EW_ONWARD_EXECUTED.npz',**v._ew_onward_trace);q.dump(out/'EW_ONWARD_JOURNAL.json',v._ew_onward_journal)
            v._chain_counts['python_native']+=2*len(v._ew_onward_journal)
    return dict(passed=True,entry_native=entry,observer_native=result['native'],goal=onward,actual_sensor_refresh=True,
        old_library_certificate_reused=False,formal_retained_commit=False)
