"""One frozen saved input; full original time-window validation, no MuJoCo."""
import importlib.abc
import sys


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SAVED_STATE_ONLY '+name)


sys.meta_path.insert(0,NoPhysical())
import hashlib,importlib.util,json,math,os,signal,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def dump(p,x):
    def default(v):
        if hasattr(v,'tolist'):return v.tolist()
        if hasattr(v,'item'):return v.item()
        raise TypeError(type(v).__name__)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False,default=default)+'\n');tmp.replace(p)


def main():
    slot,cpu=map(int,sys.argv[1:3]);assert slot in range(17,25)and cpu in[2,3,4,5]
    os.sched_setaffinity(0,{cpu});start=time.monotonic();result=dict(passed=False,slot=slot,cpu=cpu,models=0,physical_native=0,analytical_cpp_native=0)
    engine=None;begin_cpu=time.process_time();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_STATE_JOB_600S')));signal.alarm(600)
    try:
        p=R/'experiments/v1271_ew_joint_phase_validation/audit_chain.py';s=importlib.util.spec_from_file_location('study_original_full_array_checker',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);q=m.q;np=q.np
        # Original imports deliberately pin their own process. Assign this fresh
        # saved-state job back to its predeclared disjoint Phase CPU afterwards.
        os.sched_setaffinity(0,{cpu})
        inp=O/f'input_slot{slot:02}';restored=json.loads((inp/'RESTORED.json').read_text());assert restored['passed']
        for x in restored['retained']:assert hashlib.sha256((R/x['local_path']).read_bytes()).hexdigest()==x['sha256'],'INPUT_SHA_CHANGED'
        x=json.loads((inp/'EW_ONWARD_INPUT.json').read_text());selected=json.loads((inp/'EW_ONWARD_SELECTION.json').read_text())
        assert selected['passed'],'ORIGINAL_SOURCE_NOT_PASSED'
        with np.load(inp/'EW_ONWARD_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
        with np.load(inp/'EW_ONWARD_REFERENCE.npz')as z:reference={k:z[k].copy()for k in z.files}
        wait=selected['wait_native'];rows0=selected['rows'][1:]if wait else selected['rows']
        if wait:assert selected['rows'][0]==[0.,0.,wait,0]
        assert wait in range(0,2000,50)and rows0[-1]==[0.,0.,2200,0]
        origin=dict(q.initial(x['packet']),steering_load_episode=selected['initial_load']);geometry=q.Geometry(x,table)
        engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients'])
        reserve=.04+2*math.hypot(.44,.375)*math.sin(.035/2)+2e-6;trials=[];reference_error=None
        # Reproduce chosen source FIRST; a failed reconstruction cannot produce
        # a valid ablation. Remaining timing windows follow fixed numeric order.
        delays=[wait]+[n for n in range(0,2000,50)if n!=wait]
        for delay in delays:
            rows=([[0.,0.,delay,0]]if delay else[])+rows0
            ss,uu,mm=engine.simulate(origin,rows)
            proof,_=geometry.final(selected['input'],ss,uu,rows)
            cursor=0;park=[]
            for target,speed,count,mode in rows:
                if mode:park.append(float(geometry.cycle(ss[cursor:cursor+1,:3])[0])-.02-math.hypot(.44,.375)*.1)
                cursor+=int(count)
            cycle=float(geometry.cycle(ss[-1:,:3])[0])
            extras=dict(complete_control_memory=bool(mm.shape==(len(ss),5)and np.array_equal(mm[1:,:4],uu)),
                        original_22mm_reserve=bool(proof['minimum_raw_m']>=q.REQUIRED+.022),
                        original_park_reserve=bool(park and min(park)>=q.REQUIRED+reserve),
                        original_terminal_reserve=bool(cycle>=q.REQUIRED+reserve))
            eligible=bool(proof['passed']and all(extras.values()))
            rec=dict(wait_native=delay,wait_s=.01*delay,complete_admission_passed=eligible,original_full_gate=bool(proof['passed']),
                     extras=extras,minimum_raw_m=proof['minimum_raw_m'],terminal_cycle_m=cycle,park_envelopes=park,
                     failed_checks=[k for k,v in dict(proof['checks'],**extras).items()if not v],
                     original_complete_final_stop_preserved=rows[-1]==[0.,0.,2200,0])
            trials.append(rec)
            if delay==wait:
                errors={k:float(abs(a-reference[k]).max())for k,a in [('states',ss),('controls',uu),('memory',mm)]}
                reference_error=max(errors.values());assert reference_error<=1e-8 and eligible,'SELECTED_SOURCE_RECONSTRUCTION_FAILED'
                result.update(selected_source_reproduced=True,selected_array_errors=errors)
            dump(O/f'PROGRESS_slot{slot:02}.json',dict(slot=slot,completed_windows=len(trials),total_windows=40,cpp_native=engine.native,wall_s=time.monotonic()-start))
        trials.sort(key=lambda t:t['wait_native']);selected_trial=next(t for t in trials if t['wait_native']==wait);zero=trials[0]
        assert len(trials)==40 and [t['wait_native']for t in trials]==list(range(0,2000,50))
        result.update(passed=True,selected_wait_native=wait,selected_wait_s=.01*wait,selected=selected_trial,without_wait=zero,
                      selected_reference_error=reference_error,passing_windows=[t['wait_native']for t in trials if t['complete_admission_passed']],
                      trials=trials,paired_outcome_changed=selected_trial['complete_admission_passed']!=zero['complete_admission_passed'],
                      conservative_stop_only=dict(policy_moves=False,navigation_outcome_measured=False),
                      scope='8 exposed EW saved-state controller inputs; source-admission ablation only, not actual navigation success',
                      measurements_independent_tasks=False,analytical_cpp_native=engine.native)
    except BaseException as exc:
        result.update(error=repr(exc),traceback=traceback.format_exc(),analytical_cpp_native=None if engine is not None and getattr(engine,'in_call',False)else getattr(engine,'native',0))
    finally:
        signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-start,cpu_s=time.process_time()-begin_cpu,
                                    no_physical_modules=not any(n in sys.modules for n in ['mujoco','vehicle','torch','rclpy']))
        dump(O/f'RESULT_slot{slot:02}.json',result)
    print(json.dumps({k:result.get(k)for k in ['slot','passed','error','selected_wait_s','paired_outcome_changed','wall_s','cpu_s','analytical_cpp_native']}),flush=True)
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
