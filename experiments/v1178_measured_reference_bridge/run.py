from bridge_tools import *
import fcntl,signal,time,traceback,concurrent.futures,multiprocessing
def main():
    assert not(O/'COMPLETION.json').exists()and not(C/'SOURCE_FREEZE.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')==q.GUARD
    begin=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('REFERENCE_BRIDGE_900S')));signal.setitimer(signal.ITIMER_REAL,900)
    error=None;frozen={};engine=None;py=0;inside=False;measurements=[];stops=[];gate=None;inflight=False;jobs=[]
    dump(O/'ROUND_WINDOW.json',dict(software_only=True,started_unix=time.time(),hard_stop_monotonic=begin+900,physical_authorized=False,old_windows_closed=True))
    try:
        parent=R/'runs/v1177_gap_response_execution';assert read_json(parent/'FINALIZED.json')['all_three_response_pairs_passed']
        tasks=read_json(R/'experiments/v1177_gap_response_execution/TASKS.json');mains=[t for t in tasks if t['role']=='main'];assert len(mains)==3
        selected=read_json(R/'runs/v1160_safe_terminal_connection/SELECTED.json');x=selected['input'];params=q.model.parameters()
        with np.load(R/'runs/v1163_joint_timing_repair/REFERENCE.npz')as z:reference={k:z[k].copy()for k in z.files}
        with np.load(R/selected['table_path'])as z:table={k:z[k].copy()for k in ['bounds','centers']}
        for i in sorted(set([*range(0,5885,8),5884])):jobs.append(dict(id=len(jobs),offset=i,origin=to_json_origin(reference['states'][i],reference['memory'][i],i>1685)))
        dump(C/'TASKS.json',dict(main_actual_tasks=[t['task_id']for t in mains],main_actual_records=17600,reference_stop_jobs=jobs,original_reference_native=5885,full_stop_native=2200))
        files=[*C.glob('*.py'),C/'PROTOCOL.md',C/'TASKS.json',R/'runs/v1177_gap_response_execution/FINALIZED.json',R/'runs/v1177_gap_response_execution/COMPLETION.json',R/'experiments/v1177_gap_response_execution/TASKS.json',R/'runs/v1160_safe_terminal_connection/SELECTED.json',R/'runs/v1163_joint_timing_repair/REFERENCE.npz',R/'experiments/v1163_joint_timing_repair/TASKS.json',R/selected['table_path'],R/'runs/v1159_bounded_steering_load/profile.so',R/'experiments/v1159_bounded_steering_load/PARAMETERS.json',R/'experiments/v1176_multicore_stop_backend/policy.py']
        for t in tasks:
            root=Path(t['output']);files.extend(root/p for p in ['RESULT.json','FINAL_INDEPENDENT_AUDIT.json','REQUEST_JOURNAL.json','ACTUAL_INITIAL_PACKET.json','physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json','physics/SETUP.json'])
        for mod in list(sys.modules.values()):
            p=getattr(mod,'__file__',None)
            if p and Path(p).resolve().is_relative_to(R)and Path(p).suffix=='.py':files.append(Path(p).resolve())
        frozen={str(p.relative_to(R)):sha(p)for p in set(files)};dump(C/'SOURCE_FREEZE.json',dict(files=frozen,before_new_prediction=True,model_coefficients_unchanged=True))
        gate='new_actual_regression'
        for task in mains:
            root=Path(task['output']);setup=read_json(root/'physics/SETUP.json');packet=read_json(root/'ACTUAL_INITIAL_PACKET.json');journal=read_json(root/'REQUEST_JOURNAL.json');cmd=np.array(read_json(root/'physics/BODY_COMMANDS.json'),float)
            with np.load(root/'physics/NATIVE_TRACE.npz')as z:after=project(z['qpos'],z['qvel'],setup);ctrl=z['ctrl'][:,setup['actuator_ids']].copy()
            ss=np.vstack([q.initial(packet)['state'],after]);mem=np.array([[*j['last_ctrl'],j['integral']]for j in journal]);n=len(cmd);loaded=False;res=[];pred=[];maxctrl=0.;maxmem=0.;maxcpp=0.;engine=q.accelerator.Engine(setup,params['coefficients']);previous_cpp=0
            for i in range(n):
                assert journal[i]['packet']['steering_load_episode']is loaded
                org=origin(ss[i],mem[i],loaded);p=q.model.Predictor(setup,org);v,w=map(float,cmd[i,[1,2]])
                inside=True;s,u=p.step(v,w,False);inside=False;py+=1
                cs,cu,cm=engine.simulate(org,[q.accelerator.row(v,w)])
                maxcpp=max(maxcpp,float(abs(cs[-1]-s).max()),float(abs(cu[0]-u).max()),float(abs(cm[-1]-np.r_[p.adapter.last,p.adapter.integral]).max()));assert maxcpp<=1e-8
                maxctrl=max(maxctrl,float(abs(u-ctrl[i]).max()));assert maxctrl<=1e-8
                if i+1<n:
                    maxmem=max(maxmem,float(abs(np.r_[p.adapter.last,p.adapter.integral]-mem[i+1]).max()));assert maxmem<=1e-8
                pred.append(s);delta=s-ss[i+1];delta[2]=math.atan2(math.sin(delta[2]),math.cos(delta[2]));res.append(delta)
                if v>=.005:loaded=True
            predicted=np.array(pred);residual=np.array(res);cp=primitive.encode(ss[:-1],predicted);eta=primitive.encode(ss[:-1],ss[1:])-cp;decoded=primitive.decode(ss[:-1],cp+eta);inv=primitive.maximum_error(decoded,ss[1:]);assert inv<=1e-8
            np.savez_compressed(O/(task['component']+'_residual.npz'),before=ss[:-1],actual=ss[1:],predicted=predicted,residual=residual,primitive_predicted=cp,primitive_innovation=eta,memory=mem,request=cmd[:,[1,2]],native_before=np.arange(n))
            old=read_json(root/'RESULT.json');assert old['passed']and(read_json(root/'FINAL_INDEPENDENT_AUDIT.json')['maximum_response_error']==old['maximum_response_error'])and(np.array(old['maximum_response_error'])<=[.04,.035,.015]).all()
            r=dict(component=task['component'],actual_records=n,one_step_cpp_native=engine.native,maximum_actual_trajectory_response=old['maximum_response_error'],observed_actual_state_min=ss[:-1,3:8].min(0),observed_actual_state_max=ss[:-1,3:8].max(0),observed_residual_abs_max=abs(residual).max(0),primitive_innovation_abs_max=abs(eta).max(0),maximum_control_error=maxctrl,maximum_memory_error=maxmem,maximum_cpp_python_error=maxcpp,primitive_inverse_error=inv,models=0,universal_support=False)
            measurements.append(r);engine=None;dump(O/'MEASURED_PARTIAL.json',measurements)
        engine=None;dump(O/'MEASURED_REGRESSION.json',dict(passed=True,main_records=17600,repeats_separate=17600,new_coefficients_fitted=False,cases=measurements,universal_model_error_support=False))
        gate='full_reference_stop_boundaries'
        sys.path.insert(0,str(C));import stop_backend
        context=multiprocessing.get_context('spawn');counter=context.Value('i',0);guard=context.Lock();before=time.perf_counter();inflight=True
        with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=context,initializer=stop_backend.initialize,initargs=(counter,guard,frozen))as pool:stops=list(pool.map(stop_backend.evaluate,jobs,chunksize=4))
        inflight=False;elapsed=time.perf_counter()-before
        passed=[r for r in stops if r['passed']];failed=[r for r in stops if not r['passed']]
        stop_summary=dict(all_passed=not failed,total=len(stops),passed=len(passed),rejected=len(failed),rows=stops,first_refused=failed[0]if failed else None,worst=min(stops,key=lambda r:r['minimum_raw']),wall_s=elapsed,analytical_cpp_native=len(stops)*2200,source_is_saved_nominal_not_actual=True)
        dump(O/'REFERENCE_STOP_AUDIT.json',stop_summary)
        gate='nominal_complete_recovery'
        s,u,m,r=[reference[k]for k in ['states','controls','memory','requests']];geom=q.Geometry(x,table);raw=np.minimum(*geom.components(s[:,:3],np.arange(len(s))));cycle=float(geom.cycle(s[-1:,:3])[0]);checks,goal=q.helper.checks(s,u,r,x['packet'],x['setup'],np.array(x['goal']),float(raw.min()),q.REQUIRED)
        checks.update(full2200=bool((r[-2200:]==0).all()),terminal_cycle=cycle>=q.REQUIRED);assert all(checks.values()),'ORIGINAL_COMPLETE_REFERENCE_NO_LONGER_PASSES'
        conclusion=dict(complete_nominal_recovery_passed=True,checks=checks,goal_upper=goal,minimum_reference_raw=float(raw.min()),terminal_full_cycle_raw=cycle,stop_anywhere_nominal_all_passed=not failed,
            model_disturbance_support_verified=False,full_feedback_successor_inclusion_verified=False,physical_eligibility_not_granted_by_this_audit=True,
            missing_fallback='none_in_nominal_stop_scan'if not failed else'Instant2200 braking cannot replace complete recovery at every scanned boundary; do not launch ordinary stop-anywhere recovery controller.',next_priority='close verified full-state/model-error recovery contract, or explicitly preregister limited empirical development scope without falsely passing formal retention flags')
        dump(O/'BRIDGE_CONCLUSION.json',conclusion)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        cpp=sum(r['one_step_cpp_native']for r in measurements)+(engine.native if engine else 0)+len(stops)*2200
        done=dict(closed=True,error=error,completed_main_regressions=len(measurements),main_records=sum(r['actual_records']for r in measurements),analytical_python_native=py,analytical_cpp_native=cpp,cpp_stop_jobs=len(stops),python_inflight_unknown=inside,parallel_unreturned_work_unknown=inflight,models=0,physical_native=0,training_updates=0,source_unchanged=all(sha(R/p)==h for p,h in frozen.items()),guard_original=sha(R/'REVIEW_PENDING')==q.GUARD,physical_window_open=False,wall_s=time.monotonic()-begin,last_gate=gate);dump(O/'COMPLETION.json',done);print(json.dumps(done));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None else 1
def read_json(p):return json.loads(p.read_text())
def to_json_origin(s,m,loaded):
    d=origin(s,m,loaded);d['state']=d['state'].tolist();d['last_ctrl']=d['last_ctrl'].tolist();return d
if __name__=='__main__':sys.exit(main())
