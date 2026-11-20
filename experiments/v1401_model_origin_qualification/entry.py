"""Bounded model-origin/deepcopy qualification, never a vehicle owner."""
import argparse
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','factory','physical','rclpy'}:raise AssertionError('NO_PHYSICAL_MODEL_QUALIFICATION:'+name)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--entry-check',action='store_true');args=parser.parse_args()
    sys.meta_path.insert(0,NoPhysical());os.chdir(R)
    if args.entry_check:
        def no_construction(frame,event,arg):
            if event=='call'and frame.f_code.co_name=='__init__'and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
                raise AssertionError('MODEL_CONSTRUCTION_DURING_ENTRY_CHECK')
        sys.setprofile(no_construction)
    assert os.environ.get('PHASE_REPO')==str(R) and sorted(os.sched_getaffinity(0))==[2]
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
    from resource_policy import apply
    apply()
    # Exact original guard with this new output root; no relaxed /dev/null path.
    import ast
    guard_source=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';tree=ast.parse(guard_source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='write_guard');space=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard_source),'exec'),space);sys.addaudithook(space['write_guard'])
    source=exact('v1401_qualified_origin_generator',R/'experiments/v1398_current_event_witness/response_generator.py')
    Predictor,initial,kernel,Adapter,Geometry,Gear,Capture=source.binding()
    io=exact('v1401_exact_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
    if args.entry_check:
        value=dict(passed=True,models_constructed=0,analytical_native=0,actual_cpu=sorted(os.sched_getaffinity(0)),guard_original=True,origin_binding_file=str(Path(initial.__code__.co_filename).resolve().relative_to(R)),physical_admission=False)
        io.atomic(O/'ENTRY_CHECK.json',value);print(json.dumps(value));sys.setprofile(None);return 0
    authority=read(O/'APPROVAL.json');window=read(O/'ROUND_WINDOW.json');parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert authority['mode']=='MODEL_ORIGIN_QUALIFICATION' and authority['maximum_analytical_native']==804 and parent['active_round']==C.name and parent['models_now_authorized']
    assert not(O/'RESULT.json').exists() and not(R/'REVIEW_PENDING').exists()
    assert window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and window['absolute_deadline_unix']<=1795395600
    frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
    fixed=read(O/'FIXED_INPUTS.json');assert sha(R/fixed['origin_file'])==fixed['origin_sha256'] and sha(R/fixed['setup_file'])==fixed['setup_sha256']
    original=read(R/fixed['origin_file']);setup=read(R/fixed['setup_file'])
    assert original['native_tick']==10775 and original['coupled_episode']is False and original['steering_motion_active']is False
    import numpy as np
    result=dict(passed=False,closed=False,analytical_native=0,analytical_inflight_unknown=False,explicit_predictor_constructions=0,predictor_construction_inflight_unknown=False,private_branch_copies=0,internal_allocator_constructions=None,mujoco_models=0,physical_native=0,replay_native=0,physical_admission=False,cases=[])
    started=time.monotonic();deadline=min(started+300,window['hard_stop_monotonic']-10)
    def stop(*_):raise TimeoutError('MODEL_ORIGIN_QUALIFICATION_STOP')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,deadline-started))
    def step(p,v,w):
        assert result['analytical_native']<804 and time.monotonic()<deadline and time.time()<window['absolute_deadline_unix']-10, 'MODEL_ORIGIN_BUDGET_OR_DUAL_CLOCK'
        result['analytical_inflight_unknown']=True;s,u=p.step(v,w,False);result['analytical_native']+=1;result['analytical_inflight_unknown']=False;return s,u
    def create(packet):
        assert result['explicit_predictor_constructions']<6
        result['predictor_construction_inflight_unknown']=True;p=Predictor(setup,initial(packet),kernel.PARAMETERS);result['explicit_predictor_constructions']+=1;result['predictor_construction_inflight_unknown']=False
        assert p.adapter.__class__is Adapter
        p.adapter.parked_target=None;p.adapter._steering_motion_active=packet['steering_motion_active']
        assert p.coupled_episode==packet['coupled_episode']
        assert np.max(abs(p.state[[0,1,2,3,5]]-packet['body']))<=1e-8 and abs(p.state[4]-packet['body_lateral'])<=1e-8
        assert np.max(abs(p.front-packet['steering']['position']))<=1e-8 and np.max(abs(p.front_rate-packet['steering']['velocity']))<=1e-8
        assert np.max(abs(p.adapter.last-packet['controller_memory']['last_ctrl']))<=1e-8 and p.adapter.integral==packet['controller_memory']['integral']
        return p
    def snapshot(p):return dict(state=p.state.copy(),front=p.front.copy(),front_rate=p.front_rate.copy(),last=p.adapter.last.copy(),integral=p.adapter.integral,coupled=p.coupled_episode,active=getattr(p.adapter,'_steering_motion_active',False))
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            for active in [False,True]:
                packet=copy.deepcopy(original);packet['coupled_episode']=active;packet['steering_motion_active']=active
                owner=create(packet);fresh=create(packet);nominal=create(packet);before=snapshot(owner)
                branch=source.clone_private_branch(owner,lambda a,b:np.r_[a,b]);result['private_branch_copies']+=1
                states=[branch.state.copy()];controls=[];maximum=0.
                for _ in range(200):
                    a,u=step(branch,0.,0.);b,v=step(fresh,0.,0.);maximum=max(maximum,float(abs(a-b).max()),float(abs(u-v).max()));states.append(a.copy());controls.append(u.copy());assert maximum<=1e-8,'PRIVATE_BRANCH_AND_FRESH_MODEL_DIVERGED'
                after=snapshot(owner);unchanged=all(np.array_equal(before[k],after[k])for k in before)
                assert unchanged, 'PRIVATE_BRANCH_MUTATED_NOMINAL_OWNER'
                a,u=step(owner,.1,0.);b,v=step(nominal,.1,0.);maximum=max(maximum,float(abs(a-b).max()),float(abs(u-v).max()));assert maximum<=1e-8
                np.savez_compressed(O/('branch_mode_'+str(int(active))+'.npz'),states=np.asarray(states),ctrl=np.asarray(controls))
                result['cases'].append(dict(modeled_mode_fixture=active,saved_actual_packet_not_new_physics=True,branch_native=200,fresh_comparison_native=200,nominal_pair_native=2,full_model_error=maximum,nominal_owner_unchanged=unchanged,passed=True))
                io.atomic(O/'PARTIAL.json',result)
            result['passed']=len(result['cases'])==2 and result['analytical_native']==804
        except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            result.update(closed=True,wall_s=time.monotonic()-started,source_unchanged=all(sha(R/n)==h for n,h in frozen.items()))
            result['passed']=result['passed']and result['source_unchanged'];io.atomic(O/'RESULT.json',result)
    print(json.dumps({k:v for k,v in result.items()if k!='traceback'}));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
