"""Production authorization negatives and new actor-replay interface checks, zero real models."""
import ast,copy,hashlib,importlib.util,io,json,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v867_margin_navigation';sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
class NoModels:
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0]in {'mujoco','torch','rclpy','vehicle','factory'}:raise RuntimeError('REAL_MODELS_FORBIDDEN')
sys.meta_path.insert(0,NoModels())
from authority import authorized,digest
import authority
from handshake import ProtocolError

def main():
 tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==12 and len({t['run_id']for t in tasks})==12
 now=time.time();base=dict(models_authorized=True,scope='V867_STATIC_THEN_CONDITIONAL_DYNAMIC',source_freeze_sha256='SOFTWARE_QUAL',started_unix=now-1,deadline_unix=now-1+5400)
 tests=[]
 with tempfile.TemporaryDirectory(dir=O)as folder:
  fake=Path(folder);root=fake/'runs/v867_margin_navigation';root.mkdir(parents=True);(root/'AUTHORIZATION.json').write_text(json.dumps(base));(root/'STATIC_GATE.json').write_text(json.dumps(dict(passed=True)))
  with patch.object(authority,'R',fake):
   for t in tasks:
    a=dict(base,run_id=t['run_id'],task_sha256=digest(t));assert authorized(t,a,now,'SOFTWARE_QUAL')==a['deadline_unix'];tests.append(t['task_id'])
   t=tasks[0];auth=dict(base,run_id=t['run_id'],task_sha256=digest(t));negatives=[]
   for name,changes,tc in [('false',{'models_authorized':False},{}),('scope',{'scope':'old'},{}),('freeze',{'source_freeze_sha256':'old'},{}),('run',{'run_id':'bad'},{}),('digest',{'task_sha256':'bad'},{}),('duration',{'deadline_unix':base['deadline_unix']+1},{}),('goal',{}, {'goal_xy':[0,0]}),('seed',{}, {'seed':9}),('actor',{}, {'dynamic':True}),('budget',{}, {'wall_limit_s':999})]:
    try:authorized(dict(t,**tc),dict(auth,**changes),now,'SOFTWARE_QUAL')
    except ProtocolError:negatives.append(name)
    else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
   (root/'STATIC_GATE.json').write_text(json.dumps(dict(passed=False)));t=tasks[6]
   try:authorized(t,dict(base,run_id=t['run_id'],task_sha256=digest(t)),now,'SOFTWARE_QUAL')
   except ProtocolError:negatives.append('dynamic_without_static_gate')
   else:raise AssertionError('DEPENDENCY_BYPASSED')
 # Exercise the actual new replay function with nonphysical arrays; known actuator/mocap tamper must fail.
 import physical
 class D:
  def __init__(self,m):self.time=0.;self.qpos=np.zeros(2);self.qvel=np.zeros(2);self.ctrl=np.zeros(1);self.mocap_pos=np.zeros((1,3));self.mocap_quat=np.array([[1.,0.,0.,0.]]);self.contact=[]
 fake_mj=types.ModuleType('mujoco');fake_mj.MjData=D;fake_mj.mj_setState=lambda *args:None;fake_mj.mj_forward=lambda *args:None;fake_mj.mj_kinematics=lambda *args:None;fake_mj.mj_collision=lambda *args:None
 class Actor:
  def apply(self,m,d):d.mocap_pos[0,0]=d.time*.08
 class Catalog:
  def classify(self,*args):raise AssertionError('NO_SYNTHETIC_CONTACTS')
 def native(m,d):d.time+=.01;d.qpos[0]+=.01
 replay_cases=[]
 with tempfile.TemporaryDirectory(dir=O)as folder,patch.dict(sys.modules,{'mujoco':fake_mj}):
  for dynamic,corrupt in [(False,False),(True,False),(True,True)]:
   rows=[]
   for i in range(1,4):rows.append(dict(qpos=np.array([i*.01,0.]),qvel=np.zeros(2),ctrl=np.ones(1),mocap_pos=np.array([[i*.01*.08 if dynamic else 0.,0.,0.]]),mocap_quat=np.array([[1.,0.,0.,0.]])))
   if corrupt:rows[1]['mocap_pos'][0,0]+=.1
   obj=types.SimpleNamespace(m=object(),initial=np.zeros(1),spec=1,rows=rows,actor=Actor()if dynamic else None,native=native,catalog=Catalog(),contacts=[[],[],[],[]]);result=physical.replay(obj,time.time()+30,Path(folder));assert result['passed']==(not corrupt);replay_cases.append(dict(dynamic=dynamic,corrupt=corrupt,result=result,real_model_integrations=0))
 assert(C/'nav2_params.yaml').read_bytes()==(R/'experiments/v865_global_margin_preparation/nav2_params.yaml').read_bytes()
 for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 # Existing production loop10 cases are retained and exercised with its explicit fake dependencies.
 spec=importlib.util.spec_from_file_location('qualified_loop',R/'experiments/v862_backend_qualification/loop_fixture.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q);stream=io.StringIO();runner=unittest.TextTestRunner(stream=stream);res=runner.run(unittest.defaultTestLoader.loadTestsFromModule(q));(O/'ORIGINAL_BACKEND_LOOP_TESTS.console').write_text(stream.getvalue());assert res.wasSuccessful()
 summary=dict(passed=True,positive_authorization_tasks=tests,negative_authority_cases=negatives,replay_interface_cases=replay_cases,original_backend_loop_cases=res.testsRun,static_dependency_cannot_be_bypassed=True,model_initializations=0,model_integrations=0,ros_servers=0,scope='Interface and original loop qualification; synthetic replay cases do not prove real dynamic model replay',at=time.time());(O/'ZERO_QUALIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items()if k!='replay_interface_cases'}),flush=True)
if __name__=='__main__':main()
