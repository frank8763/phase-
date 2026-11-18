"""Finite certified observation handoff, with no assumed future observations."""
from pathlib import Path
import copy,importlib.util,math,sys,time
C=Path(__file__).resolve().parent;R=C.parents[1]
s=importlib.util.spec_from_file_location('v1254_parent_loader',R/'experiments/v1250_ew_current_goal/package_loader.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
entry=m.get_goal_entry();q=entry.q;np=entry.np
sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'))
from scipy.optimize import least_squares
CAP=.42722137342572125
class WorkEnd(Exception):pass

def bounded(z):
    z=np.asarray(z,float);assert z.shape==(6,)and np.isfinite(z).all(),'FINITE_CONNECTOR_VECTOR'
    return np.r_[np.clip(z[:3],-CAP,CAP),np.clip(z[3:],50.,1800.)]

def schedule(z):
    z=bounded(z);rows=[]
    for i,speed in enumerate([.08,-.03,.08]):
        rows.extend([(float(z[i]),speed,int(round(z[3+i])),0),(0.,0.,2200,0)])
    return rows

def proof(x,table,states,controls,memory,requests):
    g=q.Geometry(x,table);a,b=g.components(states[:,:3],np.arange(len(states)))
    low=float(np.minimum(a,b).min());cycle=float(g.cycle(states[-1:,:3])[0])
    checks,upper=q.helper.checks(states,controls,requests,x['packet'],x['setup'],np.asarray(x['goal']),low,q.REQUIRED)
    checks.update(terminal_cycle=cycle>=q.REQUIRED,full2200=bool(np.array_equal(requests[-2200:],np.zeros((2200,3)))),
        signed_component=bool(np.isin(requests[:,0],[-.03,0.,.08]).all()),
        complete_memory=bool(memory.shape==(len(states),5)and np.array_equal(memory[1:,:4],controls)))
    return dict(passed=bool(all(checks.values())),checks=checks,minimum_raw_m=low,
        minimum_static_m=float(a.min()),minimum_dynamic_m=float(b.min()),terminal_cycle_m=cycle,goal_upper_m=upper,native=len(controls))

def generate(x,table,deadline,checkpoint=lambda _:None):
    origin=entry.bind_current(x,x['packet'],False)
    assert x['setup']['case']['id']=='EAST_WEST','EW_ONLY'
    old=R/'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_RECOVERY_INPUT.json'
    import json
    target=np.asarray(q.initial(json.loads(old.read_text())['packet'])['state'])
    g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);total=0;trials=[]
    for index,turns in enumerate([[CAP,CAP,-CAP],[.32,-.32,-.32],[-.32,.32,.32],[0.,0.,0.]]):
        calls=0;cache={};best=None
        def evaluate(z):
            nonlocal total,calls,best
            z=bounded(z);key=z.tobytes()
            if key in cache:return cache[key]
            if calls>=250 or time.monotonic()>=deadline:raise WorkEnd()
            ss,uu,mm=engine.simulate(origin,schedule(z));calls+=1;total+=1
            a,b=g.components(ss[:,:3],np.arange(len(ss)));lo=np.minimum(a,b)
            bins=24;ii=np.minimum(np.arange(len(ss))*bins//len(ss),bins-1);mins=np.full(bins,np.inf);np.minimum.at(mins,ii,lo)
            d=ss[-1]-target;yaw=math.atan2(math.sin(d[2]),math.cos(d[2]));cycle=float(g.cycle(ss[-1:,:3])[0])
            residual=np.r_[3*d[:2],yaw,.25*d[6],10*np.maximum(0.,q.REQUIRED+.002-mins),10*max(0.,q.REQUIRED+.002-cycle)]
            rank=(float(np.linalg.norm(residual)),float(np.linalg.norm(d[:2])))
            if best is None or rank<best[0]:best=(rank,z.copy(),dict(seed=index,position_m=float(np.linalg.norm(d[:2])),heading_rad=abs(yaw),steer_rad=abs(float(d[6])),raw_m=float(lo.min()),cycle_m=cycle))
            cache[key]=residual
            if len(cache)>64:cache.pop(next(iter(cache)))
            return residual
        def jac(z):
            columns=[]
            for j in range(6):
                delta=.0001 if j<3 else 10.;a=bounded(z);b=a.copy();a[j]-=delta;b[j]+=delta;a=bounded(a);b=bounded(b)
                columns.append((evaluate(b)-evaluate(a))/(b[j]-a[j]))
            return np.array(columns).T
        try:
            least_squares(evaluate,np.r_[turns,600.,300.,250.],jac=jac,
                bounds=(np.r_[np.full(3,-CAP),np.full(3,50.)],np.r_[np.full(3,CAP),np.full(3,1800.)]),
                max_nfev=30,ftol=1e-9,xtol=1e-9,gtol=1e-9)
        except WorkEnd:pass
        if best is None:break
        rec=dict(best[2],calls=calls);trials.append(rec);checkpoint(dict(stage='signed_observation_connection',trial=rec,cpp_native=engine.native))
        if not(rec['position_m']<=.015 and rec['heading_rad']<=.015 and rec['steer_rad']<=.025 and rec['raw_m']>=q.REQUIRED+.002 and rec['cycle_m']>=q.REQUIRED+.002):continue
        rows=schedule(best[1]);ss,uu,mm=engine.simulate(origin,rows)
        local=copy.deepcopy(x);local['goal']=ss[-1,:2].tolist();requests=q.requests_of(rows)
        checked=proof(local,table,ss,uu,mm,requests)
        if checked['passed']:
            return dict(passed=True,rows=rows,states=ss,controls=uu,memory=mm,proof=checked,
                target=ss[-1,:3],trials=trials,analytical_cpp_native=engine.native,candidate_calls=total,
                physical_eligible=False,original_goal_certified=False,requires_fresh_actual_sensors_before_onward=True)
    return dict(passed=False,trials=trials,analytical_cpp_native=engine.native,candidate_calls=total,physical_eligible=False)

def execute(v,x,table,deadline,packet_fn,checkpoint=lambda _:None):
    origin=entry.bind_current(x,packet_fn(v),False);start=v.count
    assert v.adapter.parked_target is None,'UNQUALIFIED_PARK_MODE'
    plan=generate(x,table,deadline,checkpoint);assert plan['passed'],'NO_CERTIFIED_OBSERVATION_HANDOFF'
    ref=plan['states'];shadow=q.model.Predictor(x['setup'],origin)
    states=[origin['state'].copy()];shadows=[origin['state'].copy()];controls=[];memory=[np.r_[origin['last_ctrl'],origin['integral']]];requests=[];journal=[]
    for i,(turn,speed,n,mode) in enumerate(plan['rows']+[(0.,0.,2200,0)]):
        assert mode==0 and speed in [-.03,0.,.08],'SIGNED_HANDOFF_COMMAND_SCOPE'
        for _ in range(int(n)):
            assert time.monotonic()<deadline,'HANDOFF_DEADLINE'
            packet=packet_fn(v);now=entry.measured_origin(packet,v._live_load)
            assert packet['native_tick']==v.count==start+len(controls)and abs(packet['sim_time']-(x['packet']['sim_time']+.01*len(controls)))<=1e-8,'HANDOFF_NATIVE_CLOCK'
            vr=float(speed);wr=vr*math.tan(float(turn))/.6 if vr else 0.
            expected,_=shadow.step(vr,wr,False);before=v.count;v.step(vr,wr,False);assert v.count==before+1
            if vr>=.005:v._live_load=True
            elif vr<=-.005:v._live_load=False
            after=entry.measured_origin(packet_fn(v),v._live_load);actual=after['state'];reference=ref[min(len(controls)+1,len(ref)-1)]
            d=actual-expected;error=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])])
            d=actual-reference;pose=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2])))])
            states.append(actual);shadows.append(expected);controls.append(after['last_ctrl']);memory.append(np.r_[after['last_ctrl'],after['integral']]);requests.append([vr,wr,0.])
            journal.append(dict(native=v.count,row=i,request=[vr,wr,False],response_error=error,reference_error=pose,load=v._live_load))
            assert (error<=np.array([.04,.035,.015])).all()and(pose<=np.array([.04,.035])).all(),'HANDOFF_RESPONSE_OR_REFERENCE'
            if v.count%5==0:v.scan()
    arrays={k:np.asarray(z)for k,z in dict(states=states,shadow=shadows,controls=controls,memory=memory,requests=requests).items()}
    local=copy.deepcopy(x);local['goal']=plan['target'][:2].tolist()
    checked=proof(local,table,arrays['states'],arrays['controls'],arrays['memory'],arrays['requests'])
    shchecked=proof(local,table,arrays['shadow'],arrays['controls'],arrays['memory'],arrays['requests'])
    assert checked['passed']and shchecked['passed']and entry.original.previous.stopped(packet_fn(v)),'COMPLETE_HANDOFF_STOP_PROOF'
    return dict(passed=True,native=len(controls),proof=checked,shadow_proof=shchecked,plan=plan,arrays=arrays,journal=journal,
        actual_sensor_evidence_generated=False,original_goal_certified=False)
