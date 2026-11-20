"""Separate saved-evidence audit; stdout uses durable normalized JSON only."""
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
S=O/'model'


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical','rclpy'}:
            raise AssertionError('SAVED_WITNESS_AUDIT_NO_PHYSICAL:'+name)


def main():
    sys.meta_path.insert(0,NoPhysical());os.chdir(R)
    assert os.environ.get('PHASE_REPO')==str(R) and sorted(os.sched_getaffinity(0))==[2]
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
    from resource_policy import apply
    apply()
    io=exact('v1417_original_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
    out=O/'model';out.mkdir(exist_ok=True)
    guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
    node=next(n for n in ast.parse(guard.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='write_guard')
    scope=dict(Path=Path,os=os,OUT=out);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
    read=lambda p:json.loads(p.read_text())
    def publish(path,value):
        io.atomic(path,value)
        durable=read(path)
        print(json.dumps(durable,allow_nan=False))
        return durable
    if '--entry-check' in sys.argv:
        def forbid(frame,event,arg):
            if event=='call' and frame.f_code.co_name in {'__init__','step'} and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
                raise AssertionError('SAVED_AUDIT_ENTRY_MODEL_CALL_FORBIDDEN')
        sys.setprofile(forbid)
    source=exact('v1417_unchanged_independent_scalar_audit',R/'experiments/v1415_unified_causal_witness/audit.py')
    generator=exact('v1417_unchanged_scalar_generator',R/'experiments/v1415_unified_causal_witness/generator.py')
    generator.binding()
    assert Path(source.audit.__code__.co_filename).resolve()==R/'experiments/v1415_unified_causal_witness/audit.py'
    assert Path(generator.feedback.current.__code__.co_filename).resolve()==R/'experiments/v1409_scalar_steering_feedback/feedback.py'
    import numpy as np
    if '--entry-check' in sys.argv:
        assert not read(R/'runs/v1382_weekend_campaign/LEDGER.json')['models_now_authorized']
        probe=dict(passed=np.bool_(True),nested=[np.bool_(False),np.float64(.22),np.int64(3940)])
        durable=publish(out/'SERIALIZER_ROUNDTRIP.json',probe)
        assert durable==dict(passed=True,nested=[False,.22,3940])
        publish(out/'ENTRY_CHECK.json',dict(passed=True,models=0,analytical_native=0,physical_native=0,actual_cpu=[2],original_guard=True,constructor_step_profile_refusal=True,real_audit_and_getter_source=True,saved_normalized_JSON_stdout=True))
        return 0
    authority=read(out/'AUDIT_APPROVAL.json');started=False
    assert not(out/'INDEPENDENT_AUDIT.json').exists()
    def stop(*_):raise TimeoutError('SAVED_INDEPENDENT_AUDIT_DUAL_CLOCK_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop)
    signal.setitimer(signal.ITIMER_REAL,max(.01,min(1805,authority['hard_stop_monotonic']-time.monotonic()-10,authority['absolute_deadline_unix']-time.time()-10)))
    try:
        assert authority['source_generation']==str(S.relative_to(R))
        assert authority['maximum_steps']==402000
        assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in authority['source_hashes'].items())
        assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in authority['generated_data_hashes'].items())
        with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            generated=read(S/'RESULT.json');assert generated['passed'] and generated['closed'] and not generated['analytical_inflight_unknown'] and 200<=generated['nominal_native']<=2000
            with np.load(S/'NOMINAL.npz',allow_pickle=False)as data:evidence={k:data[k].copy()for k in data.files}
            for key in ['journal','memory','modes']:evidence[key]=read(S/(key.upper()+'.json'))
            evidence['original_rpp_replies']=read(S/'MODELED_ACCEPTED.json')
            started=True
            result=source.audit(read(S/'CURRENT_INPUT.json'),read(S/'SETUP.json'),evidence,S/'branches',authority=authority,lock=lock)
    except BaseException as exc:
        result=dict(passed=False,closed=True,error=repr(exc),traceback=traceback.format_exc(),audit_analytical_native=None if started else 0,audit_inflight_unknown=started,physical_native=0)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    durable=publish(out/'INDEPENDENT_AUDIT.json',result)
    return 0 if durable['passed']else 1


if __name__=='__main__':raise SystemExit(main())
