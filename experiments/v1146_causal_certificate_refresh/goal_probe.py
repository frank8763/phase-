"""One bounded analytical goal restoration; no physics or new observations."""
from qualify import *


def main(output_name='goal02',entry_offset=12500):
    out=O/output_name;out.mkdir(exist_ok=False);started=time.monotonic()
    wall_deadline=1794661200.
    assert time.time()<wall_deadline-180, 'ORIGINAL_WINDOW_INSUFFICIENT'
    deadline=min(time.monotonic()+120,time.monotonic()+wall_deadline-time.time()-30)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('GOAL_PROBE150')))
    signal.alarm(min(150,max(1,int(wall_deadline-time.time()-15))))
    p=json.loads((R/'runs/v1145_observer_failure_review/SAVED_STOP_PACKET.json').read_text())
    source=json.loads((R/'runs/v1145_observer_failure_review/SAVED_OBSERVATION_SOURCE.json').read_text())
    assert p['native_tick']==source['source_native_tick']==34715 and source['source_age_s']==0.
    setup=json.loads((R/'runs/v858_nav2_verified/v1144/observation_main/physics/SETUP.json').read_text())
    table=np.load(R/'runs/v1145_observer_failure_review/SAVED_JOINT_TABLE.npz')
    x=dict(setup=setup,packet=p,source=source,goal=[4.,-2.],safe_terminal_pose=[4.,-1.85,0.])
    geometry=Geometry(x,{k:table[k] for k in ['bounds','centers']})
    old=json.loads((R/'runs/v1136_route_clock_restore/dynamic_seed_v120/OPTIMIZATION.json').read_text())
    base=remaining_rows(old['rows'],entry_offset);assert base[-1]==(0.,0.,2200,0) and not any(r[3] for r in base)
    n=len(base)-1;u0=np.r_[[r[0] for r in base[:-1]],np.ones(n)]
    lower=np.r_[np.full(n,-.42722137342572125),np.full(n,.8)]
    upper=np.r_[np.full(n,.42722137342572125),np.full(n,1.2)]
    engine=Engine(setup);origin=initial(p);best=None;calls=0;cache={}
    class End(Exception):pass
    class Feasible(Exception):pass
    def schedule(u):
        return [(float(u[i]),.12,max(1,int(round(base[i][2]*u[n+i]))),0) for i in range(n)]+[(0.,0.,2200,0)]
    def grouped(a):
        b=np.full(64,np.inf);np.minimum.at(b,np.minimum(np.arange(len(a))*64//len(a),63),a);return b
    def evaluate(u):
        nonlocal best,calls
        if calls>=300 or time.monotonic()>=deadline:raise End()
        rows=schedule(u);key=(u[:n].tobytes(),tuple(r[2] for r in rows))
        if key in cache:return cache[key]
        ss,uu=engine.simulate(origin,rows);calls+=1
        a,b=geometry.components(ss[:,:3],np.arange(len(ss)));hold=float(geometry.cycle(ss[-1:,:3])[0])
        delta=ss[-1,:2]-[4.,-1.85];yaw=float(np.arctan2(np.sin(ss[-1,2]),np.cos(ss[-1,2])))
        residual=np.r_[delta/.025,yaw/.1,np.maximum(0.,REQUIRED+.005-grouped(a))/.01,np.maximum(0.,REQUIRED+.005-grouped(b))/.01,max(0.,REQUIRED+.005-hold)/.01]
        rank=(max(float(np.linalg.norm(delta))-.025,abs(yaw)-.1,REQUIRED-float(a.min()),REQUIRED-float(b.min()),REQUIRED-hold,0.),float(residual@residual))
        if best is None or rank<best['rank']:best=dict(rows=rows,rank=rank,minimum_raw_m=float(np.minimum(a,b).min()),terminal_error_m=float(np.linalg.norm(delta)),terminal_yaw_rad=abs(yaw))
        cache[key]=residual
        if len(cache)>80:cache.pop(next(iter(cache)))
        if rank[0]<=0 and geometry.final(x,ss,uu,rows)[0]['passed']:raise Feasible()
        return residual
    def jac(u):
        f=evaluate(u);matrix=np.empty((len(f),len(u)))
        for k in range(len(u)):
            step=.0001 if k<n else max(.005,2/base[k-n][2]);a=u.copy();b=u.copy();a[k]=max(lower[k],u[k]-step);b[k]=min(upper[k],u[k]+step)
            matrix[:,k]=(evaluate(b)-evaluate(a))/(b[k]-a[k])
        return matrix
    sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'))
    from scipy.optimize import least_squares
    try:
        least_squares(evaluate,u0,jac=jac,bounds=(lower,upper),max_nfev=30)
        stop='OPTIMIZER_RETURNED'
    except Feasible:stop='FULL_SOURCE_FEASIBLE'
    except End:stop='FIXED_SOFTWARE_BUDGET'
    assert best is not None
    rows=best['rows'];ss,uu=engine.simulate(origin,rows)
    ps,pu,memory,episodes,active=python_replay(setup,origin,rows)
    error=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert error<=1e-8
    proof,_=geometry.final(x,ss,uu,rows);backups=[]
    if proof['passed']:
        from recovery_source import forecast_packet
        moving=len(pu)-2200
        for i in sorted(set(list(range(0,moving+1,8))+[moving])):
            assert time.time()<wall_deadline-10, 'ORIGINAL_WINDOW_REACHED'
            origin=dict(state=ps[i],last_ctrl=memory[i,:4],integral=float(memory[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]))
            bs,bu=engine.simulate(origin,[(0.,0.,2200,0)])
            packet=forecast_packet(p,ps[i],memory[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]))
            bp,_=geometry.final(dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)])
            backups.append(dict(native=i,passed=bp['passed'],minimum_raw_m=bp['minimum_raw_m'],failed_checks=[k for k,v in bp['checks'].items() if not v]))
    result=dict(passed=bool(proof['passed'] and backups and all(b['passed'] for b in backups)),entry_offset=entry_offset,full_source_passed=proof['passed'],proof=proof,best=best,optimizer_stop=stop,optimizer_calls=calls,backup_count=len(backups),failed_backups=sum(not b['passed'] for b in backups),backups=backups,python_cpp_error=error,analytical_cpp_native=engine.native,analytical_python_native=len(pu),models=0,physical_native=0,source_sensor_native=34715,future_observations_used=0,original_goal_physical_passed=False,wall_s=time.monotonic()-started)
    dump(out/'RESULT.json',result);np.savez_compressed(out/'SOURCE.npz',states=ps,controls=pu,memory=memory,episodes=episodes,active=active);signal.alarm(0);print(encode(result))


if __name__=='__main__':main()
