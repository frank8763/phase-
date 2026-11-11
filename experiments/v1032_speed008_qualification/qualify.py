"""Exercise actual entry, executor, saved audit and stop policy without models."""
import ast,copy,importlib.abc,importlib.util,json,math,subprocess,sys,tempfile,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1032_speed008_qualification';sys.path[:0]=[str(C),str(R/'experiments/v1027_timed_speed_source')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
def own(name):
 spec=importlib.util.spec_from_file_location('v1032_qualified_'+name,C/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
worker=own('worker');campaign=own('campaign');execute=own('execute').execute;audit=own('audit').audit
assert Path(worker.execute.__code__.co_filename).resolve()==C/'execute.py'
assert Path(audit.__code__.co_filename).resolve()==C/'audit.py'
from whole_input import initial,Predictor,PARAMETERS
fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());setup=fixture['setup'];checks={};negative=[]
def qpos(states):
 q=np.zeros((len(states),11));q[:,:2]=states[:,:2];q[:,3]=np.cos(states[:,2]/2);q[:,6]=np.sin(states[:,2]/2);k=np.tan(states[:,6])/.6;q[:,7]=np.arctan(.6*k/(1-.27*k));q[:,9]=np.arctan(.6*k/(1+.27*k));return q
class Plant:
 def __init__(self,plan,offset=None):self.states=np.asarray(plan['state_path']);self.requests=np.asarray(plan['planned_body_requests']);self.count=0;self.offset=offset
 def body(self):
  s=self.states[self.count].copy()
  if self.offset is not None and self.count==3:s[self.offset[0]]+=self.offset[1]
  return [*s[:4],s[5]]
 def step(self,*request):assert np.array_equal(request,self.requests[self.count]);self.count+=1
 def steering_sample(self):
  s=self.states[self.count].copy()
  if self.offset is not None and self.count==3 and self.offset[0]==6:s[6]+=self.offset[1]
  q=qpos(s[None,:])[0,[7,9]];return np.r_[q,[0.,0.]]
for task in json.loads((C/'TASKS.json').read_text()):
 plan=json.loads((C/('PLAN_'+task['task_id']+'.json')).read_text());assert execute(Plant(plan),plan,time.time()+100)['passed'];checks['production_executor_'+task['task_id']]=True
 for label,mutator in [('position',lambda p:Plant(p,(0,.011))),('heading',lambda p:Plant(p,(2,.009))),('steering',lambda p:Plant(p,(6,.016)))]:
  try:execute(mutator(plan),plan,time.time()+100)
  except AssertionError:negative.append(task['task_id']+'_'+label)
  else:raise AssertionError('NEGATIVE_NOT_REJECTED '+label)
 bad=copy.deepcopy(plan);bad['planned_body_requests'][-1][0]=.08
 try:execute(Plant(bad),bad,time.time()+100)
 except AssertionError:negative.append(task['task_id']+'_missing_tail')
 else:raise AssertionError('MISSING_TAIL_ACCEPTED')
 # Saved-audit interface uses the real schema with independently built pose
 # quaternions/encoder positions and original predictor controls.
 with tempfile.TemporaryDirectory(dir=O,prefix='software_fixture_')as folder:
  out=Path(folder);(out/'physics').mkdir();s=np.asarray(plan['state_path']);u=np.asarray(plan['predicted_actuator_controls']);rr=np.asarray(plan['planned_body_requests']);q=qpos(s[1:]);v=np.zeros((500,10));v[:,0]=s[1:,3]*np.cos(s[1:,2])-s[1:,4]*np.sin(s[1:,2]);v[:,1]=s[1:,3]*np.sin(s[1:,2])+s[1:,4]*np.cos(s[1:,2]);v[:,5]=s[1:,5]
  trace=dict(qpos=q,qvel=v,ctrl=u,clearance=np.full(500,.3),self_margin=np.full(500,.01));np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace)
  commands=[[0.,*rr[i,:2],s[i,3],s[i,5],float(rr[i,2])]for i in range(500)]
  result=dict(passed=True,navigation_native=500,own_replay_native=500,replay=dict(passed=True),physical=dict(bad_contacts=0))
  for name,value in [('physics/SETUP.json',setup),('physics/BODY_COMMANDS.json',commands),('RESULT.json',result),('REGENERATED_PROFILE.json',plan)]: (out/name).write_text(json.dumps(value)+'\n')
  local=dict(task,output=str(out));proof=audit(local);assert proof['passed'],proof;checks['independent_saved_schema_'+task['task_id']]=True
  trace['qpos'][3,0]+=.02;np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace);assert not audit(local)['passed'];negative.append(task['task_id']+'_saved_pose_tamper')
tree=ast.parse((C/'campaign.py').read_text());call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='Popen');task=json.loads((C/'TASKS.json').read_text())[0];rp=O/'NOT_AUTHORIZED.json';args=eval(compile(ast.Expression(call.args[0]),str(C/'campaign.py'),'eval'),dict(str=str,R=R,C=C,task=task,rp=rp));p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr;checks['exact_production_command_pause_guard']=True
assert campaign.permitted([])and campaign.permitted([dict(passed=True)])and not campaign.permitted([dict(passed=False)]);checks['actual_first_failure_policy']=True
assert len({t['output']for t in json.loads((C/'TASKS.json').read_text())})==3 and all(not Path(t['output']).exists()for t in json.loads((C/'TASKS.json').read_text()));checks['all_output_roots_new']=True
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['all_source_parses']=True;result=dict(passed=all(checks.values()),checks=checks,rejected_negative_cases=negative,models=0,integrations=0,navigation_started=False)
(O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
