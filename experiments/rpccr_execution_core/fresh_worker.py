"""A genuinely fresh t0 NS navigation. Never reads historical physical traces."""
import sys,json,time,signal,fcntl,traceback
from pathlib import Path
CORE=Path(__file__).resolve().parent;R=CORE.parents[1]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
RESOURCE=apply();sys.path.insert(0,str(CORE));import numpy as np
from physical_ops import dump,factory,bind
from native_worker import entry,sha
from kernel import law,load
import fresh_pipeline as pipeline
import live_reference as live

def install_history_guard(output):
 output=Path(output).resolve()
 def hook(event,args):
  if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(__import__('os').fsdecode(args[0])).resolve()
  if p.name in ['NATIVE_TRACE.npz','BODY_COMMANDS.json','SENSORS.json.gz','CONTACTS.json.gz','ACTUAL_CAUSAL_ENTRY_INPUT.json']and not p.is_relative_to(output):raise AssertionError('FRESH_NAVIGATION_HISTORY_READ_FORBIDDEN '+p.name)
 sys.addaudithook(hook)

def main():
 assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task,O,cfg,out=entry(sys.argv[1]);assert task['kind']in ['main','repeat']and task['historical_prefix_native']==0
 w=json.loads((O/'ROUND_WINDOW.json').read_text());a=json.loads((O/'APPROVAL.json').read_text());assert a['models_authorized']and task['task_id']in a['allowed_task_ids'];assert all(sha(R/p)==h for p,h in json.loads(Path(cfg['source_freeze']).read_text())['files'].items());assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>120
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);end=min(w['absolute_deadline_unix']-30,time.time()+900);v=None;native=None;inside=False;creating=False;f=factory(O);owner=pipeline.configure(O);r=dict(passed=False,vehicle_initializations=0,internal_factory_model_constructions='unknown',historical_replay_native=0,new_actual_native=0,navigation_native=0,own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,training_updates=0,fresh_native_zero=True,analytical_prediction_scope='Live recovery trajectory forecasts only; original static C++ previews and static predictions not counted in this field',new_main_samples=0,resource_policy=RESOURCE)
 def halt(*_):raise TimeoutError('TASK_OR_ROOT_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  install_history_guard(out)
  creating=True;v=f.create_vehicle(out/'physics',task);creating=False;r['vehicle_initializations']=1;assert v.count==0 and v.d.time==0.;import mujoco as mj
  setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8';meta=json.loads((O/'NORTH_SOUTH_T0_METADATA.json').read_text());load('fresh_public_setup_contract',R/'experiments/v1067_causal_replan_brake_reserve/initial_contract.py').check_setup(setup,meta);assert list(v.body()[:3])==meta['packet']['body'][:3]
  bind(v,law.Adapter,mj);native=v.native
  def counted(*args):
   nonlocal inside
   assert v.count<85000 and time.time()<end-120,'NATIVE_OR_REPLAY_RESERVE';inside=True;x=native(*args);inside=False;return x
  v.native=counted
  owner.execute=lambda *args:pipeline.execute(*args,output=O)
  owner.navigate(v,setup,task,end,out,r);r['new_main_samples']=1 if task['kind']=='main'else 0
 except BaseException as e:r.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  evidence=r.pop('_evidence',None);segments=r.pop('_direct_segments',[]);dump(out/'DIRECT_SEGMENTS.json',segments)
  if creating:r['vehicle_initializations']=None
  r['new_actual_native']=r['navigation_native']=None if inside else v.count if v else 0;r['analytical_prediction_native']=live.PREDICTION_NATIVE
  if v is not None:
   try:
    r['physical']=v.finish();r['evidence_saved']=True
    if evidence is not None:dump(out/'CAUSAL_EVIDENCE.json',dict(first=evidence.first,rows=evidence.snapshots,periodic_constraints=evidence.periodic.constraints))
   except BaseException as e:r.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not inside and r.get('evidence_saved')and v.count and time.time()<end-15:
    try:v.native=native;r['own_replay_native']=None;r['replay_state_initializations']=None;rep=f.replay(v,end,out/'physics');r.update(replay=rep,own_replay_native=rep['replay_native'],replay_state_initializations=1);r['passed']=r['passed']and rep['passed']
    except BaseException as e:r.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);r['closed']=True;load('fresh_entry_result',R/'experiments/v1067_causal_replan_brake_reserve/entry_record.py').save(out,r)
 return 0 if r['passed']else 1
if __name__=='__main__':sys.exit(main())
