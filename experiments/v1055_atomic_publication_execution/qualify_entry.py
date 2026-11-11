"""New physical entry binding; unchanged science plus complete saved producer loop."""
import ast,copy,importlib.abc,json,math,subprocess,sys,tempfile,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1055_atomic_publication_execution';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from execute import execute,ProcessJob
def main():
 checks_={};x=json.loads((O/'INPUT_SOURCE.json').read_text());original=json.loads((O/'SELECTED_PLAN.json').read_text());original['goal']=x['goal'];previous=R/'experiments/v1054_atomic_publish'
 for name in ['handoff.py','atomic.py','execute.py','source_job.py']:assert(C/name).read_bytes()==(previous/name).read_bytes(),'SCIENCE_NOT_EXACT_COPY '+name
 checks_['scientific_and_executor_sources_exact_V1054']=True;assert ProcessJob.__init__.__globals__['C']==C,'PRODUCER_NAMESPACE_NOT_CURRENT';checks_['producer_namespace_current']=True
 worker=load('v1055_physical_entry',C/'full_worker.py');h,setup=worker.history_files();assert worker.execute.__code__.co_filename==str(C/'execute.py');assert len(json.loads((h/'physics/BODY_COMMANDS.json').read_text()))==23640;worker.regenerate(setup,x['packet'],original);checks_['actual_entry_history_resolver_and_full_regeneration']=True
 class Plant:
  def __init__(self):self.p=Predictor(x['setup'],initial(x['packet']),PARAMETERS);self.count=23640;self.adapter=self.p.adapter
  def step(self,*request):self.p.step(*request);self.count+=1
  def body(self):s=self.p.state;return [*s[:4],s[5]]
  def steering_sample(self):
   s=self.p.state;k=math.tan(s[6])/.6;kd=(1+math.tan(s[6])**2)/.6*s[7];front=np.array([math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]);rates=.6*kd/(np.array([1-.27*k,1+.27*k])**2+(.6*k)**2);return np.r_[front,rates]
  def scan(self):return dict(native_tick=self.count)
 def packet(v,discovered):
  now=time.monotonic();enc=v.steering_sample();return dict(body=v.body(),native_tick=v.count,sim_time=x['packet']['sim_time']+(v.count-23640)*.01,body_measured_at=now,sent_at=now,dynamic_discovered=True,steering=dict(position=enc[:2].tolist(),velocity=enc[2:].tolist(),native_tick=v.count,measured_at=now),controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral)))
 class Evidence:
  def update(self,scan):pass
  def source(self,v):return dict(source_native_tick=v.count,source_age_s=0.,decision_at=time.monotonic(),periodic=copy.deepcopy(x['source']['periodic']))
 class SavedProducer:
  def __init__(self,folder,payload):
   source=R/'runs/v1054_atomic_publish/software_full_executor/refresh'/folder.name;self.result=json.loads((source/'RESULT.json').read_text());assert np.max(abs(np.array(payload['packet']['body'])-self.result['packet']['body']))<=1e-8,'SOFTWARE_PREFIX_DIVERGED';folder.mkdir(parents=True,exist_ok=False)
  def finish(self):return self.result
  def close(self):pass
 with tempfile.TemporaryDirectory(dir=O,prefix='software_entry_fixture_')as temp:
  v=Plant();result=execute(v,x['setup'],original,time.time()+300,Evidence(),Path(temp),packet,job_class=SavedProducer,pace=False);assert result['passed']and result['epochs']==11 and result['maximum_publish_to_control_s']<=.05;assert np.linalg.norm(np.asarray(v.body()[:2])-x['goal'])<=.45;checks_['new_production_executor_all_11_saved_producer_epochs']=True;software=dict(result,actual_models=0,actual_integrations=0,not_new_mjb_audit=True)
 for name in ['driver','start','watchdog','close','delivery','audit','source_job']:load('v1055_qualification_'+name,C/(name+'.py'))
 checks_['all_actual_production_modules_import_without_models']=True
 p=subprocess.run([str(R/'run_phase.sh'),'experiments/v1055_atomic_publication_execution/full_worker.py',str(C/'TASK_full_main.json'),str(O/'NO_AUTHORITY.json')],cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr;checks_['actual_entry_pause_guard_blocks']=True
 for path in C.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
 checks_['all_sources_parse']=True;assert all(not Path(t['output']).exists()for t in json.loads((C/'FULL_TASKS.json').read_text()));assert HARD_END==1794400200.;checks_['new_outputs_and_same_absolute_deadline']=True
 dump(O/'ENTRY_QUALIFICATION.json',dict(passed=True,checks=checks_,software=software,models=0,integrations=0));print(json.dumps(dict(passed=True,checks=checks_,software=software,models=0)))
if __name__=='__main__':main()
