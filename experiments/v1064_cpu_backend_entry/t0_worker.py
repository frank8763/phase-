"""One declared physical t0, no integrations; phase-specific actual model hash."""
import sys,os,json,time,signal,fcntl,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
RESOURCE=apply()
from authority import authorized
from kernel import *
task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());end=authorized(task,receipt);assert task['kind']=='t0';lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out=Path(task['output']);out.mkdir(parents=True,exist_ok=False);v=None;result=dict(passed=False,model_initializations=None,navigation_native=0,own_replay_native=0,historical_replay_native=0,private_mujoco_native=0,resource_policy=RESOURCE)
def halt(*_):raise TimeoutError('T0_OR_ROOT_DEADLINE')
signal.signal(signal.SIGALRM,halt);signal.signal(signal.SIGTERM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,min(90.,end-time.time())))
try:
 factory=load('v1062_t0_factory',C/'scene_binding.py');v=factory.create_vehicle(out/'physics',task);result['model_initializations']=1;pin_threads();setup=json.loads((out/'physics/SETUP.json').read_text());scan=v.scan();summary=v.finish();meta=json.loads((O/(task['case_id']+'_T0_METADATA.json')).read_text());assert v.count==0 and v.d.time==0. and not v.rows and not v.commands;assert v.first_detection is None and summary['minimum_actual_clearance_m']>=.15 and summary['bad_contacts']==0;assert np.max(abs(np.asarray(v.body())-meta['packet']['body']))<=1e-8,'DECLARED_INITIAL_BODY_MISMATCH'
 for k in ['known','limits','actuator_ids','slew_per_second','dt']:assert setup[k]==meta['setup'][k],'ORIGINAL_MODEL_CONTRACT_CHANGED '+k
 assert json.loads((O/(task['case_id']+'_STATIC_SOURCE.json')).read_text())['passed'];result.update(passed=True,status='TRUE_T0_PREFLIGHT_PASS',setup=setup,output=str(out),actual_native=0,summary=summary,scan=scan,body=list(v.body()),steering=v.steering_sample().tolist(),task=task)
except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
finally:
 signal.setitimer(signal.ITIMER_REAL,0)
 if v is not None:result['physical']=v.finish()
 result['closed']=True
 from entry_record import save
 save(out,result)
sys.exit(0 if result['passed']else 1)
