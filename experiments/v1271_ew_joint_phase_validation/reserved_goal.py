"""Whole-source parked/terminal reserves; separate low-priority CPU workers."""
from pathlib import Path
import copy,concurrent.futures,importlib.util,json,math,multiprocessing,os,sys,time
C=Path(__file__).resolve().parent;R=C.parents[1]
s=importlib.util.spec_from_file_location('v1260_private_parent',R/'experiments/v1257_ew_adapter_entry/ew_live.py');live=importlib.util.module_from_spec(s);sys.modules[s.name]=live;s.loader.exec_module(live)
q=live.q;np=live.np
sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'))
from scipy.optimize import least_squares
CAP=.42722137342572125;RHO=math.hypot(.44,.375)
RESPONSE=.04+2*RHO*math.sin(.035/2)+2e-6
read=lambda p:json.loads(Path(p).read_text())
class WorkEnd(Exception):pass
class Found(Exception):pass

def groups_of():
    rows=read(R/'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_ROWS.json');groups=[];current=[]
    for row in rows:
        if row[1]!=0.:current.append(row)
        elif current:groups.append(current);current=[]
    assert len(groups)==4 and len(groups[-1])==12
    return groups

def schedule(groups,delta2,z):
    z=np.clip(np.asarray(z,float),[.5,.85,-.2,-.2],[2.5,1.25,.2,.2]);base=[sum(r[2]for r in g)for g in groups]
    rows=[];scales=[1.,(base[1]+delta2)/base[1],float(z[0]),float(z[1])]
    for i,group in enumerate(groups):
        counts=np.diff(np.round(np.r_[0.,np.cumsum([r[2]for r in group])]*scales[i]).astype(int));turns=[r[0]for r in group]
        if i==3:turns=[float(np.clip(t+z[2 if k<6 else 3],-CAP,CAP))for k,t in enumerate(turns)]
        if i:rows.append((float(turns[0]),0.,600,1))
        rows.extend((float(t),float(group[0][1]),int(n),0)for t,n in zip(turns,counts));rows.append((0.,0.,2200,0))
    rows.append((0.,0.,2200,0));return rows

def reserves(g,ss,rows):
    out=[];cursor=0
    for t,v,n,mode in rows:
        if mode:out.append(float(g.cycle(ss[cursor:cursor+1,:3])[0])-.02-RHO*.1)
        cursor+=int(n)
    return out,float(g.cycle(ss[-1:,:3])[0])

def solve_job(job):
    assert not any(n in sys.modules for n in ['mujoco','vehicle']),'MATHEMATICAL_WORKER_HAS_PHYSICAL_MODULE'
    cpu=job['cpu'];os.sched_setaffinity(0,{cpu});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
    x=job['input'];table=job['table'];org=job['origin'];target=np.asarray(job['target']);delta2=job['delta_second'];deadline=job['deadline'];groups=groups_of()
    g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);calls=0;cache={};best=None;selected=None;error=None
    low=np.array([.5,.85,-.2,-.2]);high=np.array([2.5,1.25,.2,.2]);seed=np.array([1.,1.,0.,0.])
    def evaluate(z):
        nonlocal calls,best,selected
        z=np.clip(z,low,high);key=z.tobytes()
        if key in cache:return cache[key]
        if calls>=350 or time.monotonic()>=deadline:raise WorkEnd()
        rows=schedule(groups,delta2,z);ss,uu,mm=engine.simulate(org,rows);calls+=1
        a,b=g.components(ss[:,:3],np.arange(len(ss)));lo=np.minimum(a,b);env,cycle=reserves(g,ss,rows)
        bins=48;ix=np.minimum(np.arange(len(ss))*bins//len(ss),bins-1);mins=np.full(bins,np.inf);np.minimum.at(mins,ix,lo)
        delta=ss[-1,:3]-target;yaw=math.atan2(math.sin(delta[2]),math.cos(delta[2]));pos=float(np.linalg.norm(delta[:2]))
        res=np.r_[4*delta[:2],yaw,10*np.maximum(0.,q.REQUIRED+.022-mins),10*np.maximum(0.,q.REQUIRED+RESPONSE-np.asarray(env)),10*max(0.,q.REQUIRED+RESPONSE-cycle)]
        rec=dict(calls=calls,position_m=pos,heading_rad=abs(yaw),minimum_raw_m=float(lo.min()),mode_envelopes=env,terminal_cycle_m=cycle,residual=float(np.linalg.norm(res)))
        if best is None or rec['residual']<best['residual']:best=rec
        if pos<=.025 and abs(yaw)<=.1 and lo.min()>=q.REQUIRED+.022 and min(env)>=q.REQUIRED+RESPONSE and cycle>=q.REQUIRED+RESPONSE:
            one=copy.deepcopy(x);one['safe_terminal_pose']=target.tolist();proof,_=g.final(one,ss,uu,rows)
            proof['checks']['complete_memory']=bool(mm.shape==(len(ss),5)and np.array_equal(mm[1:,:4],uu));proof['checks']['mode_response_reserve']=min(env)>=q.REQUIRED+RESPONSE;proof['checks']['terminal_response_reserve']=cycle>=q.REQUIRED+RESPONSE;proof['passed']=bool(all(proof['checks'].values()))
            if proof['passed']:
                selected=dict(passed=True,rows=rows,states=ss,controls=uu,memory=mm,proof=proof,input=one,origin=org,initial_load=org['steering_load_episode'],wait_native=0,
                    candidate_kind='response_reserved_current_goal',parameters=z.tolist(),delta_second=delta2,terminal_target=target.tolist(),response_reserve_m=RESPONSE,record=rec)
                raise Found()
        cache[key]=res
        if len(cache)>64:cache.pop(next(iter(cache)))
        return res
    def jac(z):
        columns=[]
        for j in range(4):
            step=.02 if j<2 else .0001;a=z.copy();b=z.copy();a[j]=max(low[j],z[j]-step);b[j]=min(high[j],z[j]+step)
            columns.append((evaluate(b)-evaluate(a))/(b[j]-a[j]))
        return np.asarray(columns).T
    try:least_squares(evaluate,seed,jac=jac,bounds=(low,high),max_nfev=30,ftol=1e-9,xtol=1e-9,gtol=1e-9)
    except Found:pass
    except WorkEnd:
        if calls<350:error='DEADLINE_PARTIAL_NOT_ELIGIBLE'
    except BaseException as exc:error=repr(exc)
    return dict(id=job['id'],cpu=cpu,candidate=selected,best=best,calls=calls,analytical_cpp_native=engine.native,
        partial_unknown=engine.in_call,error=error,models=0,physical_native=0)

def generate(x,table,load,deadline,checkpoint=lambda _:None):
    org=live.component.entry.bind_current(x,x['packet'],load);g=q.Geometry(x,table)
    # Target points are computed from the current causal geometry, inside the
    # original goal set. No original task goal or sensor model is changed.
    yaw=float(read(R/'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_RECOVERY_INPUT.json')['safe_terminal_pose'][2])
    targets=[]
    for dx in np.arange(-.25,.251,.05):
        for dy in np.arange(-.25,.251,.05):
            if math.hypot(dx,dy)>.30+1e-10:continue
            pose=np.r_[np.asarray(x['goal'])+[dx,dy],yaw];cycle=float(g.cycle(pose[None,:])[0])
            if cycle>=q.REQUIRED+RESPONSE+.005:targets.append((math.hypot(dx,dy),-cycle,pose.tolist()))
    targets=sorted(targets,key=lambda t:(t[0],t[1],t[2]))[:2]
    assert targets,'NO_CURRENT_CAUSAL_RESERVED_GOAL_REGION'
    jobs=[]
    for delta in[-200,-250,-300]:
        for _,_,target in targets:
            jobs.append(dict(id=len(jobs),input=x,table=table,origin=org,target=target,delta_second=delta,cpu=[2,3,4,5][len(jobs)%4],deadline=min(deadline-10,time.monotonic()+180)))
    # Distinct processes isolate the C++ profiler's native-work counter. Ordered
    # results ensure completion timing cannot choose a different winner.
    results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn'))as pool:
        futures=[pool.submit(solve_job,j)for j in jobs]
        for future in futures:
            answer=future.result();results.append(answer)
            checkpoint(dict(stage='parallel_reserved_goal',complete=len(results),jobs=len(jobs),passed=sum(a['candidate']is not None for a in results),cpp_native=sum(a['analytical_cpp_native']for a in results)))
    assert not any(a['error']or a['partial_unknown']for a in results),('RESERVED_GOAL_WORKER_ANOMALY',[a['error']for a in results])
    work=sum(a['analytical_cpp_native']for a in results);summaries=[{k:v for k,v in a.items()if k!='candidate'}for a in results]
    selected=next((a['candidate']for a in results if a['candidate']is not None),None)
    if selected is None:return dict(passed=False,parallel_results=summaries,analytical_cpp_native=work)
    selected.update(parallel_results=summaries,analytical_cpp_native=work,selection_by_fixed_job_order=True,parallel_cpus=[2,3,4,5],models=0,physical_native=0,physical_eligible=False)
    return selected
