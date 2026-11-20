"""Registered CPU2 complete saved-input witness audit, with original guard."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import signal
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','factory','physical','rclpy'}:raise AssertionError('NO_PHYSICAL_CURRENT_WITNESS_AUDIT:'+name)


def main():
    sys.meta_path.insert(0,NoPhysical());os.chdir(R);assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
    apply()
    path=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O/'model');exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope);sys.addaudithook(scope['write_guard'])
    io=exact('v1410_audit_evidence_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');review=exact('v1410_independent_full_method_audit',C/'audit.py').audit
    import numpy as np
    read=lambda p:json.loads(Path(p).read_text());out=O/'model';authority=read(out/'AUDIT_APPROVAL.json')
    if '--entry-check'in sys.argv:
        def forbid_model(frame,event,arg):
            if event=='call' and ((frame.f_code.co_name=='__init__' and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}) or (frame.f_code.co_name=='step' and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'})):
                raise AssertionError('AUDIT_ENTRY_MODEL_CONSTRUCTION_OR_STEP_FORBIDDEN')
        sys.setprofile(forbid_model)
        assert authority['mode']=='ZERO_MODEL_AUDIT_ENTRY'
        sys.meta_path.insert(0,NoPhysical());source=exact('v1410_source_audit_entry',C/'generator.py');source.binding();assert Path(review.__code__.co_filename).resolve()==C/'audit.py';assert Path(source.feedback.current.__code__.co_filename).resolve()==R/'experiments/v1409_scalar_steering_feedback/feedback.py'
        value=dict(passed=True,models=0,analytical_native=0,physical_native=0,actual_cpu=sorted(os.sched_getaffinity(0)),original_guard_and_real_audit_import=True)
        io.atomic(out/'AUDIT_ENTRY_CHECK.json',value);print(json.dumps(value));return 0
    assert read(out/'RESULT.json')['passed']and not(out/'INDEPENDENT_AUDIT.json').exists()
    def stop(*_):raise TimeoutError('CURRENT_COMPLETE_INDEPENDENT_AUDIT_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,min(1805,authority['hard_stop_monotonic']-time.monotonic()-10)))
    try:
        with np.load(out/'NOMINAL.npz',allow_pickle=False)as data:evidence={k:data[k].copy()for k in data.files}
        for k in ['journal','memory','modes']:evidence[k]=read(out/(k.upper()+'.json'))
        evidence['original_rpp_replies']=read(out/'MODELED_ACCEPTED.json')
        with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            result=review(read(out/'CURRENT_INPUT.json'),read(out/'SETUP.json'),evidence,out/'branches',authority=authority,lock=lock)
    except BaseException as exc:result=dict(passed=False,closed=True,error=repr(exc),traceback=traceback.format_exc(),audit_analytical_native=None,audit_inflight_unknown=True,physical_native=0)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    io.atomic(out/'INDEPENDENT_AUDIT.json',result);print(json.dumps({k:v for k,v in result.items()if k!='traceback'}));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
