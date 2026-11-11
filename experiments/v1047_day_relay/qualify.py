"""Exercise production relay gates and interfaces under a no-model import ban."""
import ast,copy,importlib.abc,subprocess,sys,tempfile
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from reverse_execute import execute
from audit import audit_native
from search import construct

def qpos(states,setup):
 q=np.zeros((len(states),11));q[:,:2]=states[:,:2];q[:,3]=np.cos(states[:,2]/2);q[:,6]=np.sin(states[:,2]/2);k=np.tan(states[:,6])/.6;q[:,setup['steering_qpos_addresses'][0]]=np.arctan(.6*k/(1-.27*k));q[:,setup['steering_qpos_addresses'][1]]=np.arctan(.6*k/(1+.27*k));return q
class Plant:
 def __init__(self,plan,offset=None):self.ss=np.asarray(plan['state_path']);self.requests=np.asarray(plan['planned_body_requests']);self.count=0;self.offset=offset
 def body(self):
  s=self.ss[self.count].copy()
  if self.offset and self.count==3:s[self.offset[0]]+=self.offset[1]
  return [*s[:4],s[5]]
 def step(self,*request):assert np.array_equal(request,self.requests[self.count]);self.count+=1
 def steering_sample(self):
  s=self.ss[self.count].copy()
  if self.offset and self.count==3 and self.offset[0]==6:s[6]+=self.offset[1]
  return np.r_[qpos(s[None,:],setup)[0,setup['steering_qpos_addresses']],[0.,0.]]
checks={};negative=[];fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());setup=fixture['setup']
for task in json.loads((C/'REVERSE_TASKS.json').read_text()):
 plan=json.loads((C/('REVERSE_PLAN_'+task['task_id']+'.json')).read_text());assert execute(Plant(plan),plan,time.time()+120)['passed'];checks['executor_'+task['task_id']]=True
 for name,offset in [('position',(0,.011)),('heading',(2,.009)),('steering',(6,.016))]:
  try:execute(Plant(plan,offset),plan,time.time()+120)
  except AssertionError:negative.append(task['task_id']+'_'+name)
  else:raise AssertionError('UNREJECTED_ERROR '+name)
 raw=R/'runs/v858_nav2_verified/v1047';raw.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=raw,prefix='software_fixture_')as folder:
  out=Path(folder);(out/'physics').mkdir();s=np.asarray(plan['state_path']);u=np.asarray(plan['predicted_actuator_controls']);req=np.asarray(plan['planned_body_requests']);q=qpos(s[1:],setup);v=np.zeros((700,10));v[:,0]=s[1:,3]*np.cos(s[1:,2])-s[1:,4]*np.sin(s[1:,2]);v[:,1]=s[1:,3]*np.sin(s[1:,2])+s[1:,4]*np.cos(s[1:,2]);v[:,5]=s[1:,5];z=dict(qpos=q,qvel=v,ctrl=u,clearance=np.full(700,.3),self_margin=np.full(700,.01));np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**z);commands=[[0.,*req[i,:2],s[i,3],s[i,5],float(req[i,2])]for i in range(700)];r=dict(passed=True,new_response_native=700,own_replay_native=700,physical=dict(fully_recorded_native=700,root_guard_native_count=700,bad_contacts=0),replay=dict(passed=True,maximum_qpos_qvel_ctrl_mocap_error=0.))
  for name,value in [('physics/SETUP.json',setup),('physics/BODY_COMMANDS.json',commands),('RESULT.json',r),('REGENERATED_PROFILE.json',plan)]:dump(out/name,value)
  local=dict(task,output=str(out));proof=audit_native(local);assert proof['passed'],proof;checks['saved_audit_'+task['task_id']]=True;z['qpos'][3,0]+=.02;np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**z);assert not audit_native(local)['passed'];negative.append(task['task_id']+'_saved_pose_tamper')
x=json.loads((O/'INPUT_SOURCE.json').read_text());engine=Expander(x['setup']);g=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);p=initial(x['packet']);assert stop_witness(engine,g,np.asarray(p['state']),np.r_[p['last_ctrl'],p['integral']],0)[0];checks['initial_complete_stop_positive']=True
# Reproduce the real observed nearest-prefix dead end, including full memory.
r=json.loads((R/'runs/v1046_retreat_entry_timed_route/RESULT.json').read_text());ss,uu,req,mm=predict(x['setup'],x['packet'],r['nearest_candidate_actions'],tail=False);safe,minimum=stop_witness(engine,g,ss[-1],mm[-1],len(req));assert not safe and minimum<REQUIRED;negative.append('real_nearest_dead_end_full_stop');checks['real_dead_end_now_not_admitted']=True
config=dict(json.loads((C/'CONFIGS.json').read_text())[0],maximum_expansions=12);result=construct(x,config,time.time()+20);assert result['models']==0 and result['expanded']==12 and not result['passed'];checks['production_search_small_work_cap']=True
# Import every actual entry without permitting any model initialization.
for name in ['driver','reverse_worker','full_worker','watchdog','close','start']:load('v1047_qualified_'+name,C/(name+'.py'))
checks['all_production_modules_import_without_models']=True
# Exact native command remains blocked before root authorization.
task=json.loads((C/'REVERSE_TASKS.json').read_text())[0];args=[str(R/'run_phase.sh'),'experiments/v1047_day_relay/reverse_worker.py',str(C/('TASK_'+task['task_id']+'.json')),str(O/'NOT_AUTHORIZED.json')];p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr;checks['actual_native_entry_pause_gate']=True
assert HARD_END==1794400200. and len(json.loads((C/'CONFIGS.json').read_text()))==16;checks['fixed_deadline_and_config_table']=True
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['all_sources_parse']=True;assert all(not Path(t['output']).exists()for t in json.loads((C/'REVERSE_TASKS.json').read_text())+json.loads((C/'FULL_TASKS.json').read_text()));checks['all_registered_outputs_new']=True
dump(O/'QUALIFICATION.json',dict(passed=all(checks.values()),checks=checks,rejected_negative_cases=negative,models=0,integrations=0,actual_goal_not_yet_passed=True));print(json.dumps(dict(passed=True,checks=checks,negative=negative,models=0)))
