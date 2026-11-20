"""Guarded complete-witness generation; no approval or launch is implicit."""
import argparse
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
from branch_store import BranchStore

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','factory','physical','rclpy'}:raise AssertionError('CURRENT_WITNESS_NO_PHYSICAL:'+name)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output');args=parser.parse_args()
    out=Path(args.output).resolve();assert out.is_relative_to(O)and out!=O and out.is_dir()
    assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
    os.chdir(R);sys.meta_path.insert(0,NoPhysical())
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
    apply()
    guard_path=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(n for n in ast.parse(guard_path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='write_guard');scope=dict(Path=Path,os=os,OUT=out);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard_path),'exec'),scope);sys.addaudithook(scope['write_guard'])
    io=exact('v1402_atomic_evidence',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
    read=lambda p:json.loads(Path(p).read_text())
    authority=read(out/'APPROVAL.json');current=read(out/'CURRENT_INPUT.json');setup=read(out/'SETUP.json')
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert authority['models_authorized']is True and authority['round_id']==parent['active_round']and parent['models_now_authorized']
    assert authority['current_input_sha256']==current['input_sha256']and authority['scope']=='CURRENT_EVENT_COMPLETE_MODEL_WITNESS'
    assert read(R/'runs/v1401_model_origin_qualification/COMPLETION.json')['passed'], 'CURRENT_MODEL_ORIGIN_NOT_QUALIFIED'
    assert authority['tested_source_hashes']and all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in authority['tested_source_hashes'].items())
    assert authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    source=exact('v1402_immutable_complete_generator',R/'experiments/v1398_current_event_witness/response_generator.py')
    client_module=exact('v1402_bound_modeled_client',R/'experiments/v1398_current_event_witness/modeled_client.py')
    source.binding();import numpy as np
    client=None;store=None;result=None;data=None;started=time.monotonic()
    fallback=dict(passed=False,closed=False,analytical_native=None,analytical_inflight_unknown=True,explicit_predictor_constructions=None,physical_native=0,mujoco_initializations=0,replay_native=0,physical_admission=False)
    def stop(*_):raise TimeoutError('CURRENT_COMPLETE_WITNESS_DUAL_CLOCK_STOP')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop)
    signal.setitimer(signal.ITIMER_REAL,max(.01,min(authority['hard_stop_monotonic']-time.monotonic(),authority['absolute_deadline_unix']-time.time())-10))
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            assert not(out/'RESULT.json').exists()
            store=BranchStore(out/'branches',input_sha256=current['input_sha256'],np=np,atomic=io.atomic)
            client=client_module.ModeledClient(out,run_id=authority['run_id'],input_sha256=current['input_sha256'])
            # The CPU3 peer is launched and deadline-monitored by the future
            # registered owner. It may write only inside this event directory.
            result,data=source.generate(current,setup,authority=authority,lock=lock,peer_command=client.command,save_branch=store.append)
        except BaseException as exc:
            fallback.update(error=repr(exc),traceback=traceback.format_exc())
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);save_errors=[]
            def persist(label,fn):
                try:fn()
                except BaseException as exc:save_errors.append(dict(operation=label,error=repr(exc)))
            if store is not None:persist('branch_index',store.close)
            if client is not None:
                persist('RPC_SENT',lambda:io.atomic(out/'MODELED_SENT.json',client.sent))
                persist('RPC_REPLIES',lambda:io.atomic(out/'MODELED_ACCEPTED.json',client.replies))
                persist('RPC_RETIRED',lambda:io.atomic(out/'MODELED_RETIRED.json',client.retired))
                persist('close_modeled_client',client.close)
            if data is not None:
                for key in ['journal','memory','modes']:persist(key,lambda key=key:io.atomic(out/(key.upper()+'.json'),data[key]))
                def states():
                    with(out/'NOMINAL.npz.pending').open('xb')as stream:np.savez_compressed(stream,states=np.asarray(data['states']),ctrl=np.asarray(data['ctrl']))
                    (out/'NOMINAL.npz.pending').replace(out/'NOMINAL.npz')
                persist('nominal_arrays',states)
            final=result if result is not None else fallback
            final.update(closed=True,wall_s=time.monotonic()-started,evidence_write_errors=save_errors,complete_branch_steps_saved_lower_bound=0 if store is None else len(store.rows)*200,
                         lower_bound_does_not_include_unsaved_or_nominal_native=True)
            final['passed']=final['passed']and not save_errors
            io.atomic(out/'RESULT.json',final)
    print(json.dumps({k:v for k,v in final.items()if k!='traceback'}));return 0 if final['passed']else 1


if __name__=='__main__':raise SystemExit(main())
