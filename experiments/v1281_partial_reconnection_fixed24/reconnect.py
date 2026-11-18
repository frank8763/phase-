"""Fixed short signed adjustment followed by original fully certified renewal.

No prefix is executed unless its complete stop and a continuation both pass.
Ordinary body-request semantics only; no new parked steering mode.
"""
from pathlib import Path
import concurrent.futures,multiprocessing,os,time
C=Path(__file__).resolve().parent;R=C.parents[1]
def job(data):
    from worker_context import science
    old=science();q=old.q;np=q.np
    from fresh import finite_plan
    from static_source import renew
    from recovery_source import forecast_packet
    from brake_reserve import Reserve
    import kernel,planner
    kernel.O=Path(data['output']);planner.O=kernel.O
    os.sched_setaffinity(0,{data['cpu']});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
    start=time.monotonic();p=data['packet'];setup=data['setup'];turn=data['turn'];speed=data['speed']
    rr=np.vstack([np.tile([speed,speed*np.tan(turn)/.6,0.],(500,1)),np.zeros((2200,3))])
    prefix=finite_plan(setup,p,None,rr,'FIXED_SIGNED_STATIC_RECONNECTION_PREFIX')
    rec=dict(index=data['index'],turn=turn,speed=speed,prefix_passed=bool(prefix['passed']),passed=False,cpu=data['cpu'])
    if not prefix['passed']:return dict(record=rec)
    # Full actual memory/steering state is carried through the whole prefix.
    from fresh import actions_from_requests
    ss,uu,rr,mm=kernel.predict(setup,p,actions_from_requests(rr),tail=False)
    guard=Reserve(setup,use_wide_reserve=False)
    for i in range(0,len(rr),5):
        pp=forecast_packet(p,ss[i],mm[i],i)
        if not guard.check(pp,rr[i:i+5])['passed']:
            rec['preview_rejected_native']=i;return dict(record=rec)
    pp=forecast_packet(p,ss[-1],mm[-1],len(rr));continuation=renew(setup,pp,data['goal'],wall_s=12.,max_expansions=20000)
    rec.update(continuation_passed=bool(continuation['passed']),continuation_status=continuation['status'])
    if not continuation['passed']:return dict(record=rec)
    requests=np.vstack([rr,np.asarray(continuation['planned_body_requests'])])
    complete=finite_plan(setup,p,None,requests,'COMPLETE_STATIC_TWO_STAGE_RECONNECTION')
    assert complete['passed'],'JOINED_FULL_STATIC_CERTIFICATE'
    rec.update(passed=True,native=len(requests),wall_s=time.monotonic()-start,minimum_raw_m=complete['minimum_raw_m'])
    complete.update(functional_goal_source=continuation['functional_goal_source'],finite_progress_never_counts_as_arrival=not continuation['functional_goal_source'],
        original_goal_profile_checks=continuation['original_goal_profile_checks'],source_kind='COMPLETE_GOAL'if continuation['functional_goal_source']else'SAFE_PROGRESS_NOT_ARRIVAL',
        static_reconnection=dict(record=rec,continuation_origin=pp,prefix_native=len(rr),continuation=continuation))
    # Original source contract names the complete200 stop explicitly.
    complete['checks']['full_200_stop']=complete['checks']['complete_200_stop']
    return dict(record=rec,plan=complete)
def renew_from_complete_partial(setup,packet,goal,output):
    targets=[0.,.21361068671286063,-.21361068671286063,.42722137342572125,-.42722137342572125]
    jobs=[dict(setup=setup,packet=packet,goal=goal,output=str(output),turn=t,speed=v,index=i,cpu=2+i%4)
        for i,(v,t)in enumerate((v,t)for v in [.08,-.03]for t in targets)]
    # Every fixed member is examined, fixed index selects among full passes.
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn'))as pool:
        answers=list(pool.map(job,jobs))
    records=[a['record']for a in answers]
    good=[a for a in answers if a['record']['passed']]
    return (good[0]['plan']if good else dict(passed=False,status='FIXED_TWO_STAGE_RECONNECTION_NO_SOURCE',models=0,integrations=0)),records
