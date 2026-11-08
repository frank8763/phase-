"""New task/authority orchestration qualification, with model and ROS imports blocked."""
import ast,copy,hashlib,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v864_rpp_static_regression';sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
class NoModels:
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0]in {'mujoco','torch','rclpy','vehicle','factory'}:raise RuntimeError('NO_MODEL_IMPORT')
sys.meta_path.insert(0,NoModels())
from authority import authorized,digest,DEADLINE
from handshake import verify_sources,ProtocolError,file_sha

def main():
 verify_sources(R,R/'experiments/v863_rpp_preparation/SOURCE_FREEZE.json')
 tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==5
 assert [x['case_id']for x in tasks]==['NORTH_SOUTH','EAST_WEST','WEST_EAST','NORTH_SOUTH','EAST_WEST']
 assert len(set(t['run_id']for t in tasks))==5 and len(set(t['output']for t in tasks))==5
 now=time.time();passed=[]
 for t in tasks:
  a=dict(models_authorized=True,scope='V864_FIVE_FIXED_STATIC_RPP_RUNS',source_freeze_sha256='qualify',run_id=t['run_id'],task_sha256=digest(t),started_unix=now-1,deadline_unix=DEADLINE)
  assert authorized(t,a,now,'qualify')==DEADLINE;passed.append(t['run_id'])
 task=tasks[0];auth=dict(models_authorized=True,scope='V864_FIVE_FIXED_STATIC_RPP_RUNS',source_freeze_sha256='qualify',run_id=task['run_id'],task_sha256=digest(task),started_unix=now-1,deadline_unix=DEADLINE)
 negative=[]
 for name,changes,taskchanges,when in [('false',{'models_authorized':False},{},now),('scope',{'scope':'ONE_STATIC_WEST_EAST'},{},now),('freeze',{'source_freeze_sha256':'wrong'},{},now),('run',{'run_id':'wrong'},{},now),('digest',{'task_sha256':'wrong'},{},now),('deadline_reset',{'deadline_unix':DEADLINE+1},{},now),('not_started',{'started_unix':now+1},{},now),('expired',{}, {},DEADLINE),('actor',{}, {'dynamic':True},now),('seed',{}, {'seed':999},now),('goal',{}, {'goal_xy':[0,0]},now),('budget',{}, {'wall_limit_s':999},now),('config',{}, {'nav2_params':'other'},now)]:
  bad=dict(auth,**changes);t=dict(task,**taskchanges)
  try:authorized(t,bad,when,'qualify')
  except ProtocolError:negative.append(name)
  else:raise AssertionError('ACCEPTED_NEGATIVE '+name)
 assert len(negative)==13
 # Real production entry must reject false authority before resolving physical dependencies.
 import native_worker
 try:native_worker.engine.run(task,dict(auth,models_authorized=False),'qualify')
 except ProtocolError:pass
 else:raise AssertionError('NATIVE_ENTRY_NOT_BLOCKED')
 for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 assert file_sha(R/'experiments/v863_rpp_preparation/nav2_params.yaml')==json.loads((R/'experiments/v863_rpp_preparation/SOURCE_FREEZE.json').read_text())['files']['experiments/v863_rpp_preparation/nav2_params.yaml']
 result=dict(passed=True,positive_registered_tasks=passed,negative_authority_cases=negative,false_receipt_real_backend_rejected_before_model=True,all_old358_sources_unchanged=True,controller_model_or_adapter_changes=0,models=0,integrations=0,ros_servers=0,at=time.time());(O/'ZERO_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
