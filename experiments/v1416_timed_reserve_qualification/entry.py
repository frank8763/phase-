"""Guarded actual reserve callback and independent fresh full200 comparison."""
import ast
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


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','factory','physical','rclpy'}:raise AssertionError('RESERVE_QUALIFICATION_NO_PHYSICAL:'+name)


def main():
    assert os.environ.get('PHASE_REPO')==str(R) and sorted(os.sched_getaffinity(0))==[2]
    sys.meta_path.insert(0,NoPhysical());entry='--entry-check'in sys.argv
    if entry:
        def forbid(frame,event,arg):
            if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:raise AssertionError('RESERVE_ENTRY_NO_MODEL_CALL')
        sys.setprofile(forbid)
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
    apply();path=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope);sys.addaudithook(scope['write_guard'])
    io=exact('v1416_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
    source=exact('v1416_current_reserve_callback',R/'experiments/v1415_unified_causal_witness/reserve.py');generator=exact('v1416_original_model_bindings',R/'experiments/v1415_unified_causal_witness/generator.py');Predictor,initial,kernel,Adapter,Geometry,_,_=generator.binding()
    read=lambda p:json.loads(p.read_text())
    if entry:
        value=dict(passed=True,models=0,analytical_native=0,physical_native=0,actual_cpu=[2],real_callback_source=True,original_guard=True,constructor_step_profile_refusal=True)
        io.atomic(O/'ENTRY_CHECK.json',value);print(json.dumps(value));return 0
    a=read(O/'APPROVAL.json');parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']==C.name and parent['models_now_authorized']
    assert a['maximum_analytical_native']==400 and a['maximum_predictor_constructions']==2
    assert a['models_authorized']and a['physical_admission']is False
    data=read(O/'FIXED_INPUTS.json');current=data['current_input'];packet=current['origin'];modes=current['mode_history'];setup=read(O/'SETUP.json');snapshot=current['causal_snapshot']
    counter=dict(analytical_native=0,predictor_constructions=0,analytical_inflight_unknown=False,construction_inflight_unknown=False)
    result=dict(passed=False,closed=False,fresh_native=0,fresh_inflight_unknown=False,fresh_constructions=0,fresh_construction_unknown=False,physical_native=0,mujoco_models=0,replay_native=0,physical_admission=False)
    def stop(*_):raise TimeoutError('CURRENT_RESERVE_QUALIFICATION_DUAL_CLOCK_STOP')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,min(60,a['absolute_deadline_unix']-time.time()-10,a['hard_stop_monotonic']-time.monotonic()-10)))
    sink=None;expected=[];commands=[]
    try:
        import numpy as np
        with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            sink_module=exact('v1416_real_complete_reserve_store',R/'experiments/v1415_unified_causal_witness/evidence_sink.py')
            sink=sink_module.EvidenceSink(O/'reserve_evidence',identity=current['input_sha256'],np=np,atomic=io.atomic,maximum_branches=1)
            begin=time.monotonic();callback=source.CurrentReserve(setup=setup,current=current,authority=a,lock=lock,accounting=counter,save_complete=sink.reserve_complete,save_partial=sink.reserve_partial);result['prepare_all_source_walk_s']=time.monotonic()-begin
            before=source.digest(packet);begin=time.monotonic();proof,states,ctrl=callback(packet,modes);result['callback_wall_s']=time.monotonic()-begin
            result['callback_proof']=proof
            result['complete_callback_branch_saved_before_gate']=len(sink.store.rows)==1
            assert source.digest(packet)==before and proof['passed']and proof['complete_native']==200
            result['fresh_construction_unknown']=True;p=Predictor(setup,initial(packet),kernel.PARAMETERS);result['fresh_constructions']=1;result['fresh_construction_unknown']=False
            p.adapter.encoders=lambda owner=p:generator.feedback.current(owner);p.adapter.parked_target=None;p.adapter._steering_motion_active=packet['steering_motion_active']
            assert p.coupled_episode==modes['coupled_episode']
            expected=[p.state.copy()];commands=[]
            for _ in range(200):
                assert time.time()<a['absolute_deadline_unix']-30 and time.monotonic()<a['hard_stop_monotonic']-30
                result['fresh_inflight_unknown']=True;s,u=p.step(0.,0.,False);result['fresh_native']+=1;result['fresh_inflight_unknown']=False;expected.append(s.copy());commands.append(u.copy())
            maximum=max(float(np.max(abs(states-np.asarray(expected)))),float(np.max(abs(ctrl-np.asarray(commands)))))
            with(O/'FULL200_COMPARISON.npz').open('xb')as stream:np.savez_compressed(stream,states=states,ctrl=ctrl,independent_states=np.asarray(expected),independent_ctrl=np.asarray(commands))
            assert maximum<=1e-8
            result.update(passed=True,maximum_state_ctrl_error=maximum,complete200_branch_passed=True,proof=proof,mode_history_derived_coupled_episode=modes['coupled_episode'],saved_actual_input_not_fresh_wire=True)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if sink is not None:
            try:sink.close(dict(actual_native=0,physical_native=0,callback_accounting=counter))
            except BaseException as exc:result.update(passed=False,reserve_store_close_error=repr(exc))
        if result.get('error')and expected:
            try:
                with(O/'INDEPENDENT_PARTIAL.npz').open('xb')as stream:np.savez_compressed(stream,states=np.asarray(expected),ctrl=np.asarray(commands))
                io.atomic(O/'INDEPENDENT_PARTIAL.json',dict(fresh_native=result['fresh_native'],fresh_inflight_unknown=result['fresh_inflight_unknown'],first_error=result['error']))
            except BaseException as exc:result['independent_partial_save_error']=repr(exc)
        unchanged=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in a['tested_source_hashes'].items())
        result.update(closed=True,callback_accounting=counter,analytical_native=counter['analytical_native']+result['fresh_native'],analytical_inflight_unknown=counter['analytical_inflight_unknown']or result['fresh_inflight_unknown'],explicit_predictor_constructions=counter['predictor_constructions']+result['fresh_constructions'],construction_inflight_unknown=counter['construction_inflight_unknown']or result['fresh_construction_unknown'],source_unchanged=unchanged)
        result['passed']=result['passed']and unchanged;io.atomic(O/'RESULT.json',result)
    print(json.dumps(read(O/'RESULT.json'),allow_nan=False));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
