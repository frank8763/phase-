"""Finite terminal-connection synthesis with an unchanged V1159 predictor."""
from pathlib import Path
import ast
import copy
import fcntl
import importlib.util
import itertools
import json
import math
import signal
import sys
import time
import traceback

C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1160_safe_terminal_connection'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE=apply()
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import REQUIRED
from source import initial
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'))
from geometry import Geometry
sys.path.insert(0,str(R/'experiments/v1151_retained_recovery_qualification'))
import qualify as helper
import tracking
sys.path.insert(0,str(R/'experiments/v1152_terminal_capture_qualification'))
import capture
import numpy as np


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


model=load('v1160_fixed_v1159_model',R/'experiments/v1159_bounded_steering_load/model.py')
accelerator=load('v1160_fixed_v1159_engine',R/'experiments/v1159_bounded_steering_load/engine.py')
dump=helper.dump;sha=helper.sha
GUARD='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
CASES=[('nominal',0.,0.,0.),('x_plus',.04,0.,0.),('x_minus',-.04,0.,0.),
       ('y_plus',0.,.04,0.),('y_minus',0.,-.04,0.),('yaw_plus',0.,0.,.035),('yaw_minus',0.,0.,-.035)]


def candidates(original):
    out=[dict(id=0,rows=copy.deepcopy(original),wait_native=1600,turn7=.16,turn9=-.16,role='original_control_reference')]
    for wait,a,b in itertools.product([1400,1500,1600,1700,1800],[.16,.24,.32],[-.16,-.08,0.,.08]):
        rows=[[0.,0.,wait,0]]+copy.deepcopy(original[8:])
        rows[7][0]=a;rows[9][0]=b
        out.append(dict(id=len(out),rows=rows,wait_native=wait,turn7=a,turn9=b,role='development_grid'))
    assert len(out)==61
    return out


def requests_of(rows):
    return np.array([[v,v*math.tan(t)/.6,0.]for t,v,n,mode in rows for _ in range(int(n))])


def proof(g,x,ss,uu,requests,mem):
    a,b=g.components(ss[:,:3],np.arange(len(ss)))
    low=float(np.minimum(a,b).min());cycle=float(g.cycle(ss[-1:,:3])[0])
    checks,upper=helper.checks(ss,uu,requests,x['packet'],x['setup'],np.array(x['goal']),low,REQUIRED)
    checks.update(terminal_cycle=cycle>=REQUIRED,full2200=bool((requests[-2200:]==0).all()),
        all_forward=bool((requests[:,0]>=0).all()and(requests[:,0]<=.12).all()),
        memory_shape=mem.shape==(len(ss),5),memory_controls=bool(np.array_equal(mem[1:,:4],uu)))
    return dict(passed=bool(all(checks.values())),checks=checks,
        failed_checks=[k for k,v in checks.items()if not v],minimum_raw_m=low,
        minimum_static_m=float(a.min()),minimum_dynamic_m=float(b.min()),
        terminal_cycle_raw_m=cycle,goal_upper_m=upper,native=len(uu),
        score=min(low,cycle),terminal_pose=ss[-1,:3])


def main():
    assert not(O/'COMPLETION.json').exists()and not(C/'SOURCE_FREEZE.json').exists(),'ONE_FIXED_SEARCH_ONLY'
    assert json.loads((R/'runs/v1159_bounded_steering_load/COMPLETION.json').read_text())['regression_accepted']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')==GUARD
    begin=time.monotonic();dump(O/'ROUND_WINDOW.json',dict(software_only=True,models_authorized=False,
        started_unix=time.time(),hard_stop_monotonic=begin+600,absolute_deadline_unix=time.time()+600,
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('FINITE_SEARCH_600S')));signal.setitimer(signal.ITIMER_REAL,600)
    engine=None;python_native=0;inside=False;frozen={};error=None;nominal=[];trials=[];selected=None
    try:
        parent=R/'runs/v1148_overnight_causal_recovery'
        selected_path=parent/'v120_e200_h15/SELECTED.json';table_path=parent/'actual_source/JOINT_TABLE.npz'
        old=json.loads(selected_path.read_text());x=old['input'];grid=candidates(old['rows'])
        dump(C/'CANDIDATES.json',dict(candidates=grid,selection='nominal score descending,goal upper ascending,id ascending; max8 fixed7 tests'))
        with np.load(table_path)as z:table={k:z[k].copy()for k in ['bounds','centers']}
        g=Geometry(x,table);params=json.loads((R/'experiments/v1159_bounded_steering_load/PARAMETERS.json').read_text())
        model.validate(params);origin=dict(initial(x['packet']),steering_load_episode=False)
        files=[*C.glob('*.py'),C/'PROTOCOL.md',C/'CANDIDATES.json',selected_path,table_path,
            R/'experiments/v1159_bounded_steering_load/PARAMETERS.json',R/'runs/v1159_bounded_steering_load/profile.so',
            R/'runs/v1159_bounded_steering_load/COMPLETION.json',R/'runs/v1159_bounded_steering_load/FINAL_SAVED_AUDIT.json',
            R/'runs/v1159_bounded_steering_load/recovery_nominal.npz',
            R/'experiments/v1159_bounded_steering_load/profile.cpp',
            O/'BASELINE_REPRODUCTION.json']
        for module in list(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path and Path(path).resolve().is_relative_to(R)and Path(path).suffix=='.py':files.append(Path(path).resolve())
        frozen={str(p.relative_to(R)):sha(p)for p in set(files)}
        dump(C/'SOURCE_FREEZE.json',dict(files=frozen,model_unchanged=True,finite_candidates=61,max_feedback_candidates=8))
        engine=accelerator.Engine(x['setup'],params['coefficients'])
        for item in grid:
            ss,uu,mem=engine.simulate(origin,item['rows']);requests=requests_of(item['rows'])
            p=proof(g,x,ss,uu,requests,mem);row={**item,**p};nominal.append(row)
            dump(O/'PROGRESS.json',dict(stage='nominal_search',complete=len(nominal),analytical_cpp_native=engine.native,analytical_python_native=python_native))
        dump(O/'NOMINAL_SEARCH.json',dict(cases=nominal,passed=sum(r['passed']for r in nominal)))
        # Original reference must reproduce the saved V1159 trajectory exactly.
        original_ss,original_uu,original_mem=engine.simulate(origin,grid[0]['rows'])
        with np.load(R/'runs/v1159_bounded_steering_load/recovery_nominal.npz')as z:
            err=max(float(abs(original_ss-z['states'][:len(original_ss)]).max()),float(abs(original_uu-z['controls'][:len(original_uu)]).max()),float(abs(original_mem-z['memory'][:len(original_mem)]).max()))
        assert err<=1e-8 and not nominal[0]['passed'],'ORIGINAL_FAILURE_REPRODUCTION'
        dump(O/'ORIGINAL_CONTROL_REPLAY.json',dict(passed=True,maximum_state_control_memory_error=err,original_safety_failed=True))
        ranked=sorted([r for r in nominal if r['passed']],key=lambda r:(-r['score'],r['goal_upper_m'],r['id']))[:8]
        dump(O/'FIXED_FEEDBACK_QUEUE.json',dict(ids=[r['id']for r in ranked],nominal_qualified_total=sum(r['passed']for r in nominal)))
        for item in ranked:
            assert time.monotonic()<begin+550,'TIME_RESERVE_FOR_FEEDBACK'
            ref,_,_=engine.simulate(origin,item['rows']);target=ref[-1,:3].copy()
            schedule=[(t,v)for t,v,n,mode in item['rows']for _ in range(int(n))];results=[]
            for name,dx,dy,dyaw in CASES:
                packet=copy.deepcopy(x['packet']);packet['body'][0]+=dx;packet['body'][1]+=dy;packet['body'][2]+=dyaw
                one=dict(x,packet=packet);org=dict(initial(packet),steering_load_episode=False);p=model.Predictor(x['setup'],org)
                ss=[p.state.copy()];uu=[];mem=[np.r_[p.adapter.last,p.adapter.integral]];requests=[]
                def step(v,w):
                    nonlocal python_native,inside
                    inside=True;s,u=p.step(v,w,False);inside=False;python_native+=1
                    ss.append(s);uu.append(u);mem.append(np.r_[p.adapter.last,p.adapter.integral]);requests.append([v,w,0.])
                for i,(t,v)in enumerate(schedule):
                    v,w,_=tracking.request(p.state,ref[i],t,v);step(v,w)
                needed=np.linalg.norm(p.state[:2]-target[:2])>.025;status='NOT_REQUIRED';capture_n=0
                if needed:
                    for _ in range(600):
                        v,w,status=capture.request(p.state,target)
                        if status!='CAPTURING':break
                        step(v,w);capture_n+=1
                    else:status='CAPTURE_WORK_CAP'
                for _ in range(2200):step(0.,0.)
                ss,uu,mem,requests=map(np.array,[ss,uu,mem,requests]);result=proof(g,one,ss,uu,requests,mem)
                position=float(np.linalg.norm(ss[-1,:2]-target[:2]));heading=abs(math.atan2(math.sin(ss[-1,2]-target[2]),math.cos(ss[-1,2]-target[2])))
                cs,cu,cm=engine.simulate(org,[accelerator.row(v,w)for v,w,_ in requests])
                diff=max(float(abs(cs-ss).max()),float(abs(cu-uu).max()),float(abs(cm-mem).max()))
                assert diff<=1e-8,'CPP_PYTHON_STATE_CONTROL_MEMORY'
                result['checks'].update(terminal_position=position<=.025,terminal_heading=heading<=.1,
                    capture_complete=status not in ['CAPTURE_WORK_CAP','NO_FORWARD_CAPTURE'])
                result.update(case=name,candidate_id=item['id'],passed=bool(all(result['checks'].values())),
                    failed_checks=[k for k,v in result['checks'].items()if not v],capture_native=capture_n,
                    terminal_position_error_m=position,terminal_heading_error_rad=heading,cpp_python_error=diff)
                prefix=f"c{item['id']:02d}_{name}"
                dump(O/(prefix+'.json'),result);np.savez_compressed(O/(prefix+'.npz'),states=ss,controls=uu,memory=mem,requests=requests,reference=ref)
                results.append(result)
                dump(O/'PROGRESS.json',dict(stage='fixed_feedback',candidate_id=item['id'],complete=len(results),analytical_cpp_native=engine.native,analytical_python_native=python_native))
            trial=dict(id=item['id'],passed=all(r['passed']for r in results),cases=results);trials.append(trial)
            dump(O/'FEEDBACK_TRIALS.json',dict(trials=trials))
            if trial['passed']:
                selected=dict(candidate=item,input=x,table_path=str(table_path.relative_to(R)),cases=results,
                    finite_seven_only=True,physical_eligible=False,model_disturbance_verified=False,feedback_tube_verified=False)
                dump(O/'SELECTED.json',selected);break
    except BaseException as exc:
        error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        result=dict(closed=True,error=error,nominal_candidates=len(nominal),nominal_qualified=sum(r['passed']for r in nominal),
            feedback_candidates=len(trials),feedback_case_count=sum(len(t['cases'])for t in trials),
            finite_seven_passed=selected is not None,selected_id=None if selected is None else selected['candidate']['id'],
            analytical_cpp_native=engine.native if engine else 0,analytical_python_native=python_native,
            analytical_cpp_inflight_unknown=bool(engine and engine.in_call),analytical_python_inflight_unknown=inside,
            source_unchanged=all(sha(R/p)==h for p,h in frozen.items()),guard_original=sha(R/'REVIEW_PENDING')==GUARD,
            models=0,physical_native=0,training_updates=0,physical_eligible=False,model_disturbance_verified=False,
            feedback_tube_verified=False,new24=False,wall_s=time.monotonic()-begin,
            stop_reason='FIXED_DEVELOPMENT_QUEUE_COMPLETE'if error is None else'SOFTWARE_OPERATION_OR_EVIDENCE_ERROR')
        dump(O/'COMPLETION.json',result);print(json.dumps(result));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None and result['source_unchanged']else 1


if __name__=='__main__':sys.exit(main())
