"""New complete CPP backend CLI; default is explicit unadmitted refusal."""
import fcntl
import importlib.util
import json
from pathlib import Path
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1569_common',C/'common.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0)
    try:
        c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            capability=c.load('v1569_missing_admission',C/'capability.py')
            capability.Guard(lock=lock,method={},prepared_sources={})
            raise AssertionError('FULL_CPP_BATCH_OWNER_BUDGET_NOT_YET_QUALIFIED')
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        result['closed']=True
        c.put(c.O/'PRODUCTION_REFUSAL.json',result)
    return result

if __name__=='__main__':
    print(json.dumps(main(),allow_nan=False));raise SystemExit(1)
