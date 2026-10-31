"""Two preregistered repeats after an offline contact-provenance diagnosis."""
import datetime
from pathlib import Path
import signal
import time
import traceback
from bounded_execution import Window, read, dump

src = Path(__file__).resolve().parent
deadline = datetime.datetime.fromisoformat('2026-11-01T08:00:00+08:00').timestamp()
window = Window(src,'v654_static_overnight','development01',2400,deadline)
assert read(window.root/'CONTACT_PATH_DIAGNOSIS.json')['passed']
assert read(window.root/'ZERO_STEP_CONTACT_REGRESSION.json')['passed']
assert read(window.repo/'runs/v653_static_log_recovery/continuation01/COMPLETION.json')['status']=='GATE_FAILED_REPEAT'
repeats = []; status = 'DEVELOPMENT_RUNNING'
def stop(*_): raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
try:
    for seed,scene in [(93000045,'single_event'),(91000002,'single_event')]:
        row = window.run(f'dev01_repeat_{seed}_{scene}',seed,scene)
        if row is None:
            status='BUDGET_INCOMPLETE';break
        base = window.repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
        record = window.repeat(row,base); repeats.append(record)
        dump(window.path/'REPEAT_AUDIT.json',repeats)
        if not record['matched']:
            status='DEVELOPMENT_REPEAT_FAILED';break
    else:
        status='VALIDATOR_DEVELOPMENT_READY_FOR_FRESH_CONFIRMATION'
except BaseException as error:
    status='STOPPED_EXCEPTION'
    dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
    passed=status=='VALIDATOR_DEVELOPMENT_READY_FOR_FRESH_CONFIRMATION' and window.remaining()>=0
    dump(window.path/'COMPLETION.json',{'status':status,'development_passed':passed,
         'static_acceptance_passed':False,'elapsed_s':time.monotonic()-window.started,
         'limit_s':window.limit,'repeats_attempted':len(repeats),'training_updates':0,'dynamic_started':False})
    dump(window.path/'ACTIVE.json',{'status':status,'completed':True})
    print('DEVELOPMENT_COMPLETE',status,flush=True)
