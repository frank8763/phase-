"""Exercise actual authority/route gates and original production model loop without real models."""
import ast,copy,hashlib,importlib.util,io,json,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v875_euclidean_daytime';sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
class NoModels:
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0]in {'mujoco','torch','rclpy','vehicle','factory'}:raise RuntimeError('NO_REAL_MODEL_IN_ZERO_QUALIFICATION')
sys.meta_path.insert(0,NoModels())
from authority import authorized,digest,resolve,DEADLINE
import authority
from handshake import ProtocolError

def main():
 tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==51 and len({x['run_id']for x in tasks})==51;now=time.time();assert now<DEADLINE-300;root=dict(models_authorized=True,scope='V875_DAYTIME_OFFLINE',started_unix=now-1,deadline_unix=DEADLINE,source_freeze_sha256='ZERO')
 good=[];bad=[]
 with tempfile.TemporaryDirectory(dir=O)as folder:
  fake=Path(folder);fake.mkdir(exist_ok=True);(fake/'AUTHORIZATION.json').write_text(json.dumps(root))
  for name in ['SELECTED.json','DEVELOPMENT_GATE.json','CONFIRMATION_GATE.json',*[x+'_STATIC_GATE.json'for x in ['A','B','C']]]:(fake/name).write_text(json.dumps(dict(passed=True,variant='A',source_freeze_sha256='ZERO')))
  for v in ['A','B','C','MPPI','A_no_direction','A_smoothed']:
   p=fake/'software'/v;p.mkdir(parents=True);(p/'QUALIFICATION.json').write_text(json.dumps(dict(passed=True)))
  with patch.object(authority,'O',fake):
   for t in tasks:
    t=resolve(t,'A');a=dict(root,run_id=t['run_id'],task_sha256=digest(t));assert authorized(t,a,now,'ZERO')==DEADLINE;good.append(t['task_id'])
   t=resolve(tasks[0],'A');a=dict(root,run_id=t['run_id'],task_sha256=digest(t))
   for name,ta,aa,at in [('false',t,dict(a,models_authorized=False),now),('deadline',t,dict(a,deadline_unix=DEADLINE+1),now),('expired',t,a,DEADLINE),('start',t,dict(a,started_unix=now),now),('task',dict(t,seed=9),a,now),('truth',dict(t,actor_truth=[0,0]),a,now),('freeze',t,a,now)]:
    try:authorized(ta,aa,at,'WRONG'if name=='freeze'else'ZERO')
    except (ProtocolError,KeyError,FileNotFoundError):bad.append(name)
    else:raise AssertionError('UNSAFE_AUTHORITY_ACCEPTED '+name)
   for gate,task in [('A_STATIC_GATE.json',next(x for x in tasks if x['variant']=='A'and x['dynamic'])),('CONFIRMATION_GATE.json',next(x for x in tasks if x['role']=='comparison')),('DEVELOPMENT_GATE.json',next(x for x in tasks if x['role']=='confirmation'))]:
    old=(fake/gate).read_bytes();(fake/gate).write_text('{"passed":false}');t=resolve(task,'A')
    try:authorized(t,dict(root,run_id=t['run_id'],task_sha256=digest(t)),now,'ZERO')
    except ProtocolError:bad.append(gate)
    else:raise AssertionError('DEPENDENCY_BYPASSED '+gate)
    (fake/gate).write_bytes(old)
 for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 assert 'INITIAL_SCAN.json'in(C/'preflight.py').read_text();assert 'plan:=smac_search_plan'in(C/'routing_stack.py').read_text();assert 'self.publisher.publish(result.path)'in(C/'planner_proxy.py').read_text()
 spec=importlib.util.spec_from_file_location('loop_fixture',R/'experiments/v862_backend_qualification/loop_fixture.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q);stream=io.StringIO();res=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromModule(q));(O/'ORIGINAL_BACKEND_LOOP_TESTS.console').write_text(stream.getvalue());assert res.wasSuccessful()
 # Current new replay module is byte-identical to already qualified V867 production replay.
 assert(C/'physical.py').read_bytes()==(R/'experiments/v867_margin_navigation/physical.py').read_bytes()
 cfg={v:json.loads((C/(v+'.yaml')).read_text())for v in ['A','B','C']};a,b,c=[cfg[v]for v in ['A','B','C']]
 def canonical(x):
  x=copy.deepcopy(x);x['controller_server']['ros__parameters']['FollowPath']['lookahead_dist']=0;return x
 assert canonical(a)==canonical(b)==canonical(c)
 from footprint import polygon,prove
 assert prove(polygon(.15),.15)[1]and prove(polygon(.16),.16)[1]
 assert not prove(polygon(.14),.15)[1]
 summary=dict(passed=True,positive_task_authority=len(good),negative_cases=bad,original_production_loop_tests=res.testsRun,models=0,integrations=0,ros_servers=0,actual_initial_scan_required=True,physical_loop_unchanged=True,deadline_unix=DEADLINE,at=time.time());(O/'ZERO_QUALIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
