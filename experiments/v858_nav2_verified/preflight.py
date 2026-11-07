"""A true t0 scene/model/sensor query with zero native integration."""
import fcntl,json,os,sys,traceback
from pathlib import Path
from vehicle import Vehicle,R
from instrumentation import dump
out=R/'runs/v858_nav2_verified';task=json.loads(Path(sys.argv[1]).read_text());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=dict(passed=False,environment_initializations_attempted=1,native_integrations=0);v=None
try:
 os.environ['PHASE_COURSE_PHASE']=str(task['phase']);v=Vehicle(out/'preflights'/task['id'],task['case_id'],task['seed'],task['dynamic']);packet=v.scan();assert float(v.d.time)==0.;result.update(passed=True,initial_body=v.body(),clearance=v.min_clear,self_margin=v.min_self,bad_contacts=v.bad,noise_seed=task['seed'],range_rays=len(packet['ranges']),range_max=3.,true_actor_detected_at_t0=v.first_detection is not None,model_build=task['id']);assert not v.first_detection,'INITIAL_UNSEEN_ACTOR_ALREADY_DETECTED';assert len(packet['ranges'])==32;assert v.env.model is v.m and v.env.data is v.d
except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
finally:
 dump(out/'preflights'/(task['id']+'.RESULT.json'),result);print(json.dumps(result),flush=True)
sys.exit(0 if result['passed']else 1)
