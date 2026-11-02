"""One bounded bootstrap reconstruction with all integrations disabled."""
import faulthandler,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v703_bootstrap_trace'
root.mkdir(exist_ok=True);started=time.monotonic();phase='IMPORTS';calls=[];status='INITIALIZING';error=None
class HardStop(BaseException):pass
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(HardStop('V703_SINGLE_ZERO_BOOTSTRAP_45S')));signal.alarm(45)
stack=(root/'stack_samples.txt').open('w');faulthandler.enable(file=stack,all_threads=True);faulthandler.dump_traceback_later(5,repeat=True,file=stack)
def event(name):
    with (root/'stages.jsonl').open('a') as stream:stream.write(json.dumps({'stage':name,'elapsed_s':time.monotonic()-started})+'\n')
try:
    event(phase);import mujoco
    def forbidden(*args,**kwargs):
        calls.append({'phase':phase,'elapsed_s':time.monotonic()-started})
        raise HardStop('ALL_MUJOCO_INTEGRATIONS_FORBIDDEN')
    for name in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,name,forbidden)
    sys.path.insert(0,str(repo/'experiments/v702_rpccr_prospective_compute'));from factory import initialize
    task=json.loads((repo/'experiments/v702_rpccr_prospective_compute/TASK_LIST.json').read_text())[-1]
    os.environ['PHASE_COURSE_DISTANCE']='8';os.environ['PHASE_COURSE_PHASE']=str(task['phase']);os.environ['PHASE_PROPOSAL_MODEL']=str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json');os.environ['PHASE_RECOVERY_ABLATION']='FULL'
    phase='FROZEN_FACTORY_INITIALIZE';event(phase)
    context,native=initialize(task['seed'],root/'initialization_only')
    assert float(context['env'].data.time)==0. and not calls
    phase='FACTORY_RETURNED_TIME_ZERO';event(phase);status='BOOTSTRAP_RETURNED_ZERO_TIME_NOT_NAVIGATION'
except BaseException as e:
    error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};status='DIAGNOSTIC_STOPPED'
finally:
    signal.alarm(0);faulthandler.cancel_dump_traceback_later();stack.flush()
    value={'status':status,'stage':phase,'elapsed_s':time.monotonic()-started,'seed':99010004,'error':error,'forbidden_integration_attempts':calls,'actual_integrations':0,'navigation_trials':0,'private_predictions':0,'training_updates':0,'review_guard_retained':(repo/'REVIEW_PENDING').exists(),'original_v702_remains_closed':True,'scope':'One zero-integration factory-only reconstruction, not original preflight retry, algorithm test, or proof timeout fixed.'}
    (root/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
