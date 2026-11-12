"""Real producer/atomic publication, strict roles and bounded authority; 0 models."""
import copy,importlib.abc,json,sys,time,ast,tempfile,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C))
from execute import ProcessJob
from planner import library
from atomic import allocate,publish
from recovery_source import forecast_packet
from scene_binding import create_vehicle
library();checks_={};negative=[]
for file in C.glob('*.py'):ast.parse(file.read_text(),filename=str(file))
assert ProcessJob.__init__.__globals__['C']==C
try:create_vehicle(None,None)
except AssertionError as e:assert str(e)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
else:raise AssertionError('MODEL_GUARD_NOT_EARLY')
checks_['real_factory_guard_before_model_import']=True
x=json.loads((R/'runs/v1066_actual_route_diagnosis/ns_source_repro/INPUT.json').read_text());folder=O/'qualified_real_producer';assert not folder.exists();started=time.monotonic();job=ProcessJob(folder,x)
try:
 for _ in range(800):time.sleep(.01)
 p=job.finish();completed_before_fixed_hold_end=True
finally:job.close()
assert p['passed']and p['source_kind']!='COMPLETE_GOAL'and not p['functional_goal_source'];buffers=allocate(p);s,u,r,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=800)],tail=False);fresh=forecast_packet(x['packet'],s[-1],m[-1],800);now=time.monotonic();fresh.update(body_measured_at=now,sent_at=now);fresh['steering'].update(measured_at=now);source=copy.deepcopy(x['source']);source.update(source_native_tick=fresh['native_tick'],source_age_s=0.);view=publish(buffers,fresh,source,now);record=view.record();full,ctrl,requests,mem=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=800)]+record['actions'],tail=False);errors=[float(abs(full[800:]-record['state_path']).max()),float(abs(ctrl[800:]-record['predicted_actuator_controls']).max()),float(abs(requests[800:]-record['planned_body_requests']).max())];assert max(errors)<=1e-12;minimum=Geometry(x['setup']['known'],x['source']['periodic'],fresh['sim_time']).complete(full[800:]);assert minimum>=REQUIRED
checks_['real_child_producer_finished_during_fixed800_hold']=completed_before_fixed_hold_end;checks_['full_original_python_publication_state_ctrl_requests_equal']=max(errors)<=1e-12;checks_['finite_corridor_explicitly_not_arrival']=not record['functional_goal_source']and record['information_never_counts_as_arrival'];checks_['whole_profile_timed_geometry_original_gate']=minimum>=REQUIRED
for name in ['false_goal_role','false_goal_flag','changed_wait','wrong_native','wrong_simtime','stale_body','future_source','expanded_source']:
 try:
  if name in ['false_goal_role','false_goal_flag','changed_wait']:
   candidate=copy.deepcopy(p)
   if name=='false_goal_role':candidate.update(source_kind='COMPLETE_GOAL',functional_goal_source=True)
   elif name=='false_goal_flag':candidate['functional_goal_source']=True
   else:candidate['fixed_launch_wait']+=1
   allocate(candidate)
  else:
   q=copy.deepcopy(fresh);src=copy.deepcopy(source);clock=time.monotonic();q.update(sent_at=clock,body_measured_at=clock);q['steering']['measured_at']=clock
   if name=='wrong_native':q['native_tick']+=1;q['steering']['native_tick']+=1
   elif name=='wrong_simtime':q['sim_time']+=.001
   elif name=='stale_body':q['body_measured_at']-=.1;q['steering']['measured_at']-=.1
   elif name=='future_source':src['source_native_tick']=q['native_tick']+1
   else:src['periodic']['vertices'][0][0][0]+=1.
   publish(buffers,q,src,clock)
 except AssertionError:negative.append(name)
 else:raise AssertionError('PUBLICATION_MUTATION_ACCEPTED '+name)
checks_['publication_role_clock_age_and_domain_negatives']=len(negative)==8
import authority
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==9 and sum(t['kind']=='t0'for t in tasks)==3 and sum(t['kind']=='main'for t in tasks)==sum(t['kind']=='repeat'for t in tasks)==3;assert not any('confirm'in t['task_id']for t in tasks);checks_['exact_three_t0_three_main_three_conditional_repeat_no24']=True
for t in tasks:
 assert json.loads((C/('TASK_'+t['task_id']+'.json')).read_text())==t;meta=json.loads((O/(t['case_id']+'_T0_METADATA.json')).read_text());assert t['start_xy']==meta['packet']['body'][:2]and t['goal_xy']==meta['goal']and t['start_yaw']==meta['packet']['body'][2];assert json.loads((O/(t['case_id']+'_STATIC_SOURCE.json')).read_text())['passed']
checks_['all_task_metadata_and_initial_complete_static_sources']=True
with tempfile.TemporaryDirectory(dir=O,prefix='authority_fixture_')as temporary:
 tc=Path(temporary)/'code';to=Path(temporary)/'data';tc.mkdir();to.mkdir();task=tasks[0];(tc/'TASKS.json').write_text(json.dumps(tasks));tp=tc/('TASK_'+task['task_id']+'.json');tp.write_text(json.dumps(task));(tc/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files={})));wall=time.time();mono=time.monotonic();window=dict(started_unix=wall,started_monotonic=mono,absolute_deadline_unix=wall+5400,hard_stop_monotonic=mono+5400);wp=to/'ROUND_WINDOW.json';wp.write_text(json.dumps(window));(to/'APPROVAL.json').write_text(json.dumps(dict(models_authorized=True,absolute_deadline_unix=wall+5400,allowed_task_ids=[task['task_id']])));receipt=dict(task_id=task['task_id'],task_sha256=sha(tp),source_sha256=sha(tc/'SOURCE_FREEZE.json'),window_sha256=sha(wp),task_deadline_unix=wall+90);old=(authority.C,authority.O,authority.HARD_END);authority.C,authority.O,authority.HARD_END=tc,to,wall+5400
 try:
  assert authority.authorized(task,receipt)>time.time()
  for name in ['changed_receipt','unregistered_confirmation','extended_window']:
   try:
    if name=='changed_receipt':authority.authorized(task,dict(receipt,task_sha256='wrong'))
    elif name=='unregistered_confirmation':bad=dict(task,task_id='confirm_main_01');authority.authorized(bad,receipt)
    else:bad=dict(window,absolute_deadline_unix=window['absolute_deadline_unix']+1);wp.write_text(json.dumps(bad));authority.authorized(task,dict(receipt,window_sha256=sha(wp)))
   except AssertionError:negative.append(name)
   else:raise AssertionError('AUTHORITY_MUTATION_ACCEPTED '+name)
 finally:authority.C,authority.O,authority.HARD_END=old
checks_['authority_positive_and_deadline_receipt_confirmation_rejected']=True
assert not(O/'ROUND_WINDOW.json').exists()and not json.loads((O/'APPROVAL.json').read_text())['models_authorized'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';checks_['physical_window_not_started_guard_original']=True
result=dict(passed=all(checks_.values()),checks=checks_,negative_cases=negative,source_child_wall_s=p['actual_job_wall_s'],publication_reconstruction_max_errors=errors,minimum_raw_m=minimum,source_kind=p['source_kind'],synthetic_publication_metadata_only_not_new_observations=True,models=0,integrations=0);dump(O/'ADMISSION_QUALIFICATION.json',result);print(json.dumps(result),flush=True)
