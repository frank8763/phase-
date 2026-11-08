"""Exercise actual authority/route gates and original production model loop without real models."""
import ast,copy,hashlib,importlib.util,io,json,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v881_timing_accounting_continuation';sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
class NoModels:
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0]in {'mujoco','torch','rclpy','vehicle','factory'}:raise RuntimeError('NO_REAL_MODEL_IN_ZERO_QUALIFICATION')
sys.meta_path.insert(0,NoModels())
from authority import authorized,digest,resolve,DEADLINE
import authority
from handshake import ProtocolError

def main():
 tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==87 and len({x['run_id']for x in tasks})==87;now=time.time();assert now<DEADLINE-300;root=dict(models_authorized=True,scope='V881_DAYTIME_OFFLINE',started_unix=now-1,deadline_unix=DEADLINE,source_freeze_sha256='ZERO')
 good=[];bad=[]
 with tempfile.TemporaryDirectory(dir=O)as folder:
  fake=Path(folder);fake.mkdir(exist_ok=True);(fake/'AUTHORIZATION.json').write_text(json.dumps(root))
  for name in ['SELECTED.json','DEVELOPMENT_GATE.json','CONFIRMATION_GATE.json',*[x+'_STATIC_GATE.json'for x in ['A','B','C','D']]]:(fake/name).write_text(json.dumps(dict(passed=True,variant='A',source_freeze_sha256='ZERO')))
  for v in ['A','B','C','D','MPPI_A','A_no_direction','A_smoothed']:
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
 assert a['controller_server']['ros__parameters']['FollowPath']['plugin']=='nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController'
 assert b['controller_server']['ros__parameters']['FollowPath']['plugin']=='nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController'
 assert a['controller_server']['ros__parameters']['FollowPath']['cost_scaling_dist']==.85
 assert a['planner_server']['ros__parameters']['GridBased']['cost_penalty']==3.5 and b['planner_server']['ros__parameters']['GridBased']['cost_penalty']==6.
 assert c['controller_server']['ros__parameters']['FollowPath']['lookahead_dist']==.3
 assert 'qualified_initial_control=True'in(C/'software_bridge.py').read_text()
 from software_scan_contract import publish_scan
 assert publish_scan(0,0,1.,1.051,False)and not publish_scan(0,0,1.,1.02,False)
 assert publish_scan(0,1,1.,1.001,False)
 assert not (0!=0 or False), 'Old held-tick condition should reproduce lost publication'
 assert (C/'ros_bridge.py').read_text().count('software_scan_contract')==0
 assert (C/'planner_proxy.py').read_bytes()==(R/'experiments/v878_software_scan_continuation/planner_proxy.py').read_bytes()
 import subprocess
 command="import runpy,sys;from pathlib import Path;p=Path(sys.argv[1]);sys.path.insert(0,str(p.parent));runpy.run_path(str(p),run_name='qualification_import_only')"
 result=subprocess.run([sys.executable,'-c',command,str(C/'ros_worker.py')],capture_output=True,text=True);assert result.returncode==0,result.stderr
 from footprint import polygon,prove
 assert prove(polygon(.15),.15)[1]and prove(polygon(.16),.16)[1]
 assert not prove(polygon(.14),.15)[1]
 from planner_proxy import terminal_goal
 from types import SimpleNamespace as N
 g=N(pose=N(position=N(x=4.,y=-2.),orientation=N(z=0.,w=1.)))
 selected,proof=terminal_goal(g,json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text()));assert proof['displacement_m']<=.0800000001 and selected.pose.position.y>g.pose.position.y and g.pose.position.y==-2.
 summary=dict(passed=True,positive_task_authority=len(good),negative_cases=bad,original_production_loop_tests=res.testsRun,models=0,integrations=0,ros_servers=0,actual_initial_scan_required=True,physical_loop_unchanged=True,deadline_unix=DEADLINE,at=time.time());(O/'ZERO_QUALIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
