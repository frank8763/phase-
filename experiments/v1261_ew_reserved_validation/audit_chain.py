"""Independent full-array checking of each stage against external native data."""
from pathlib import Path
import copy,importlib.util,json,math,sys
C=Path(__file__).resolve().parent;R=C.parents[1]
s=importlib.util.spec_from_file_location('v1261_audit_parent',R/'experiments/v1250_ew_current_goal/package_loader.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
e=m.get_goal_entry();q=e.q;np=e.np
read=lambda p:json.loads(Path(p).read_text())
def arrays(p):
    with np.load(p)as z:return {k:z[k].copy()for k in z.files}
def same(a,b):
    assert a.shape==b.shape and np.isfinite(a).all()and (not a.size or abs(a-b).max()<=1e-8),'EXTERNAL_ARRAY_OR_BINDING'
def bind(x,external):
    initial=q.initial(x['packet']);same(external['states'][0],np.asarray(initial['state']));same(external['memory'][0],np.r_[initial['last_ctrl'],initial['integral']])
def compare(external,trace):
    for k in ['states','controls','memory','requests']:same(external[k],trace[k])
    assert np.array_equal(external['memory'][1:,:4],external['controls']),'ACTUAL_MEMORY_CONTROLS'
def response(actual,shadow):
    d=actual-shadow
    assert (np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])]<=[.04,.035,.015]).all(),'FULL_RESPONSE_OR_REFERENCE'

def verify_component(x,table,plan,reference,trace,external,journal):
    bind(x,external);compare(external,trace);rows=plan['rows']
    assert len(rows)==6 and [r[1]for r in rows]==[.08,0.,-.03,0.,.08,0.]
    for i,(t,v,n,mode)in enumerate(rows):
        assert mode==0 and abs(t)<=.42722137342572125
        assert 50<=n<=1800 if i%2==0 else n==2200
    allrows=rows+[[0.,0.,2200,0]];req=q.requests_of(allrows);same(external['requests'],req)
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);org=dict(q.initial(x['packet']),steering_load_episode=False)
    ss,uu,mm=engine.simulate(org,rows)
    for k,a in [('states',ss),('controls',uu),('memory',mm)]:same(reference[k],a)
    cs,cu,cm=engine.simulate(org,allrows);same(trace['shadow'],cs);response(external['states'],cs)
    expected=np.vstack([reference['states'],np.repeat(reference['states'][-1:,:],2200,axis=0)])
    response(external['states'],expected)
    g=q.Geometry(x,table);local=copy.deepcopy(x);local['goal']=plan['target'][:2]
    static,dynamic=g.components(external['states'][:,:3],np.arange(len(external['states'])));low=float(np.minimum(static,dynamic).min())
    checks,upper=q.helper.checks(external['states'],external['controls'],external['requests'],x['packet'],x['setup'],np.asarray(local['goal']),low,q.REQUIRED)
    assert all(checks.values())and g.cycle(external['states'][-1:,:3])[0]>=q.REQUIRED and np.array_equal(req[-2200:],np.zeros((2200,3)))
    assert len(journal)==len(req);load=False
    for i,row in enumerate(journal):
        assert row['native']==x['packet']['native_tick']+i+1 and np.array_equal(row['request'],req[i])
        if req[i,0]>=.005:load=True
        elif req[i,0]<=-.005:load=False
        assert row['load']is load
    return dict(passed=True,native=len(req),minimum_actual_pose_causal_raw_m=low,goal_upper_m=upper,final_load=load,analytical_cpp_native=engine.native)

def verify_onward(x,table,selection,reference,trace,external,journal):
    assert selection['passed'];bind(x,external);compare(external,trace)
    rows=selection['rows'];assert rows[-1]==[0.,0.,2200,0]
    assert selection['candidate_kind']=='response_reserved_current_goal'and selection['wait_native']==0
    oldrows=read(R/'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_ROWS.json')
    old_input=read(R/'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_RECOVERY_INPUT.json')
    groups=[];group=[]
    for r in oldrows:
        if r[1]!=0.:group.append(r)
        elif group:groups.append(group);group=[]
    assert len(groups)==4
    z=np.asarray(selection['parameters']);assert z.shape==(4,)and np.isfinite(z).all()and(z>=[.5,.85,-.2,-.2]).all()and(z<=[2.5,1.25,.2,.2]).all()
    delta=selection['delta_second'];assert delta in[-200,-250,-300]
    base=[sum(r[2]for r in g)for g in groups];scales=[1.,(base[1]+delta)/base[1],float(z[0]),float(z[1])];rebuilt=[]
    for i,gp in enumerate(groups):
        original_counts=np.asarray([r[2]for r in gp]);ends=np.r_[0,np.cumsum(original_counts)];counts=np.diff(np.round(ends*scales[i]).astype(int));angles=[r[0]for r in gp]
        if i==3:angles=[float(np.clip(t+z[2 if k<6 else 3],-.42722137342572125,.42722137342572125))for k,t in enumerate(angles)]
        if i:rebuilt.append([float(angles[0]),0.,600,1])
        rebuilt.extend([float(t),float(gp[0][1]),int(n),0]for t,n in zip(angles,counts));rebuilt.append([0.,0.,2200,0])
    rebuilt.append([0.,0.,2200,0]);assert rows==rebuilt,'UNREGISTERED_RESERVED_PROFILE'
    response_margin=.04+2*math.hypot(.44,.375)*math.sin(.035/2)+2e-6
    assert abs(selection['response_reserve_m']-response_margin)<=1e-12
    one=selection['input'];assert all(one[k]==x[k]for k in ['setup','packet','source','goal'])
    target=np.asarray(selection['terminal_target']);assert np.array_equal(target,np.asarray(one['safe_terminal_pose']))
    goal=np.asarray(x['goal']);assert np.linalg.norm(target[:2]-goal)<=.30+1e-10 and abs(target[2]-old_input['safe_terminal_pose'][2])<=1e-12
    for d in target[:2]-goal:assert abs(d/.05-round(d/.05))<=1e-8 and abs(d)<=.25+1e-10
    req=q.requests_of(rows);same(external['requests'],req)
    org=dict(q.initial(x['packet']),steering_load_episode=selection['initial_load'])
    same(np.asarray(selection['origin']['state']),np.asarray(org['state']));same(np.asarray(selection['origin']['last_ctrl']),np.asarray(org['last_ctrl']));assert abs(selection['origin']['integral']-org['integral'])<=1e-8
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);ss,uu,mm=engine.simulate(org,rows)
    for k,a in [('states',ss),('controls',uu),('memory',mm)]:same(reference[k],a)
    same(trace['shadow'],ss);response(external['states'],ss)
    g=q.Geometry(x,table);nominal,_=g.final(selection['input'],ss,uu,rows);actual,_=g.final(selection['input'],external['states'],external['controls'],rows)
    assert nominal['passed']and actual['passed'],'COMPLETE_NOMINAL_AND_ACTUAL_POSE_SOURCE'
    assert nominal['minimum_raw_m']>=q.REQUIRED+.022 and min(r['raw_envelope_lower']for r in nominal['mode_envelopes'])>=q.REQUIRED+response_margin and nominal['terminal_full_cycle_raw_m']>=q.REQUIRED+response_margin,'RESERVED_PARK_AND_TERMINAL_SOURCE'
    assert len(journal)==len(req)
    schedule=[(float(t),float(v),bool(mode))for t,v,n,mode in rows for _ in range(int(n))]
    for i,(row,(turn,speed,mode))in enumerate(zip(journal,schedule)):
        assert row['native']==x['packet']['native_tick']+i+1 and np.array_equal(row['request'],req[i])
        assert row['parked_target']==(turn if mode else None)
    assert np.linalg.norm(external['states'][-1,:2]-ss[-1,:2])<=.025
    return dict(passed=True,native=len(req),nominal=nominal,actual_pose_proof=actual,analytical_cpp_native=engine.native)

def verify_refusal(x,table,selection):
    assert selection['passed']is False
    jobs=selection['parallel_results'];assert len(jobs)==6 and [j['id']for j in jobs]==list(range(6))
    assert all(j['error']is None and j['partial_unknown']is False and j['models']==j['physical_native']==0 and 0<j['calls']<=350 for j in jobs)
    assert sum(j['analytical_cpp_native']for j in jobs)==selection['analytical_cpp_native']
    g=q.Geometry(x,table);state=np.asarray(q.initial(x['packet'])['state'])
    assert g.cycle(state[None,:3])[0]>=q.REQUIRED
    return dict(passed=True,safe_stopped_functional_refusal=True,finite_search_not_infeasibility_proof=True,analytical_cpp_native=0,recorded_search_cpp_native=selection['analytical_cpp_native'])
