"""Current-state observation certificate followed by a fresh whole-goal source."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1195_eight_gib_timed_refuge'))
from route_tools import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
import goal_entry
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
import candidate_observer as observer_source
import stop_certificates
def execute(v,setup,original_seed,end,evidence,out,packet_fn,output):
    evidence,meta=bridge.fresh_evidence(v,setup);x=bridge.current_input(v,setup,evidence)
    assert previous.stopped(x['packet'])and setup['case']['id']=='WEST_EAST'
    entry=v.count;v._chain_phase='live_observer';v._chain_episode=False;v._live_load=False;v._chain_counts=dict(cpp_native=0,python_native=0,LP_calls=0)
    dump(out/'LIVE_OBSERVER_INPUT.json',x);dump(out/'LIVE_OBSERVER_PROVENANCE.json',meta)
    table,calls=bridge.joint_table(x['source']);v._chain_counts['LP_calls']+=calls;np.savez_compressed(out/'LIVE_OBSERVER_TABLE.npz',**table)
    selected=observer_source.synthesize(x,table,time.monotonic()+min(130.,end-time.time()-240),lambda p:dump(out/'PARTIAL_PROGRESS.json',p));v._chain_counts['cpp_native']+=selected['analytical_cpp_native']
    dump(out/'LIVE_OBSERVER_SELECTION.json',{k:value for k,value in selected.items()if k not in['states','controls','memory']});assert selected['passed'],'NO_CURRENT_STATE_OBSERVATION_REFUGE'
    rows=selected['rows'];reference=selected['states'];np.savez_compressed(out/'LIVE_OBSERVER_REFERENCE.npz',states=reference,controls=selected['controls'],memory=selected['memory'])
    g=q.Geometry(x,table);engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);v._chain_engine=engine;offset=0;mode=False;anchor=None;certificates=[];maximum=np.zeros(3);refmax=np.zeros(3)
    try:
        while offset<len(reference)-1:
            assert time.time()<end-240 and remaining()>270,'OBSERVER_DEADLINE_RESERVE'
            suffix=bridge.remaining_rows(rows,offset);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));block=bridge.front(suffix,n)
            p=packet(v);p.update(coupled_episode=v._chain_episode,steering_motion_active=bool(getattr(v.adapter,'_steering_motion_active',False)))
            origin=dict(q.initial(p),steering_load_episode=bool(v._live_load));proofs,predicted=stop_certificates.prove(engine,g,x,p,origin,block)
            certificates.append(dict(offset=offset,native=v.count,packet=p,steering_load_episode=bool(v._live_load),prefix=n,current=proofs[0],prospective=proofs[1]));assert all(z['passed']for z in proofs),'LIVE_COMPLETE_STOP_CERTIFICATE_REFUSED'
            local=0
            for target,speed,count,park in block:
                if park and not mode:
                    assert previous.stopped(packet(v)),'LIVE_PARK_ENTRY_NOT_REST';anchor=np.array(packet(v)['body'][:3])
                    assert g.cycle(anchor[None,:])[0]-.02-np.hypot(.44,.375)*.1>=q.REQUIRED,'LIVE_ACTUAL_PARK_RESERVE_REFUSED'
                if abs(speed)>=.005:anchor=None
                for _ in range(int(count)):
                    v.adapter.parked_target=float(target)if park else None
                    v.step(float(speed),0. if park or speed==0. else float(speed)*math.tan(target)/.6,False)
                    if park:v._chain_episode=True;v._live_load=False
                    elif speed<=-.005:v._chain_episode=False;v._live_load=False
                    elif speed>=.005:v._chain_episode=False;v._live_load=True
                    local+=1;actual=np.array(q.initial(packet(v))['state']);d=actual-predicted[1][local];err=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])]);maximum=np.maximum(maximum,err)
                    d=actual-reference[offset+local];referr=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])]);refmax=np.maximum(refmax,referr)
                    assert(err<=[.04,.035,.015]).all()and(referr<=[.04,.035,.015]).all(),'LIVE_CURRENT_REFERENCE_RESPONSE_REFUSED'
                    if anchor is not None:assert np.linalg.norm(actual[:2]-anchor[:2])<=.02 and abs(math.atan2(math.sin(actual[2]-anchor[2]),math.cos(actual[2]-anchor[2])))<=.1,'LIVE_PARK_ENVELOPE_REFUSED'
                    if park:assert abs(actual[3])<=.01 and abs(v.d.ctrl[v.adapter.commands.ids[2:]]).max()<=1e-10
                    if v.count%5==0:evidence.update(v.scan())
                mode=bool(park)
            offset+=n
            if len(certificates)%100==0:dump(out/'PARTIAL_PROGRESS.json',dict(stage='actual_current_observation',native=v.count,observer_offset=offset,total_reference=len(reference)-1))
    finally:
        dump(out/'LIVE_OBSERVER_CERTIFICATES.json',certificates);v._chain_counts['cpp_native']+=engine.native
    assert previous.stopped(packet(v))and g.cycle(np.array(packet(v)['body'][:3])[None,:])[0]>=q.REQUIRED,'LIVE_REFUGE_ACTUAL_STOP_OR_CYCLE_REFUSED'
    dump(out/'LIVE_REFUGE_ACTUAL_PACKET.json',packet(v));dump(out/'LIVE_OBSERVER_RESULT.json',dict(passed=True,actual_native=offset,maximum_response_error=maximum,maximum_reference_error=refmax,complete_stop_certificates=len(certificates)))
    # Additional actual observation is essential: the earlier entry confidence
    # set need not yet certify the path to the original goal.
    evidence,meta=bridge.fresh_evidence(v,setup);fresh=bridge.current_input(v,setup,evidence);dump(out/'LIVE_GOAL_INPUT.json',fresh);dump(out/'LIVE_GOAL_PROVENANCE.json',meta)
    gt,calls=bridge.joint_table(fresh['source']);v._chain_counts['LP_calls']+=calls;np.savez_compressed(out/'LIVE_GOAL_TABLE.npz',**gt)
    goal_out=out/'CURRENT_GOAL_ENTRY';goal_out.mkdir(exist_ok=False)
    v._chain_phase='current_goal';v.adapter.parked_target=None
    try:
        answer=goal_entry.execute(v,setup,fresh,gt,time.monotonic()+max(0.,end-time.time()-120),
            lambda:time.time()<end-120 and remaining()>150,packet,
            lambda p:dump(out/'PARTIAL_PROGRESS.json',p),goal_out)
    finally:
        v._chain_counts['cpp_native']+=getattr(v,'_goal_cpp_native',0)
        v._chain_counts['python_native']+=len(getattr(v,'_goal_journal',[]))
    return dict(passed=True,entry_native=entry,observer_native=offset,goal=answer,
        current_state_and_time_regeneration=True,old_library_certificate_reused=False,
        formal_retained_commit=False)
