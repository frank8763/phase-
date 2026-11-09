"""Execute exact production Bridge callback against fixed historical snapshots."""
import ast,copy,gzip,importlib.abc,json,sys,types,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v934_rpccr_certified_recovery'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical','rclpy'}:raise AssertionError('MODEL_OR_ROS_IMPORT '+name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(C),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v887_exact_lidar_software'),str(R/'experiments/v884_feasible_rpp'),str(R/'experiments/v862_ready_static')]
from handshake import require
from command_tube import admit
from recovery_audit import check as independent_recovery
# Exact AST production function, not a handwritten model of its branch logic.
tree=ast.parse((C/'ros_bridge.py').read_text());method=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='dispatch_command');module=ast.Module(body=[method],type_ignores=[])
S=R/'runs/v933_rpccr_certified_recovery/saved';rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));known=json.loads((S/'SETUP.json').read_text())['known'];goal=json.loads((S/'TASK.json').read_text())['goal_xy'];checks={};results=[]
class Stub:
 def __init__(self,row,retained=None):
  self.latest=row['packet'];self.motion=types.SimpleNamespace(decision_snapshot=lambda:(copy.deepcopy(row['packet']),copy.deepcopy(row['source'])));self.planner_proxy=types.SimpleNamespace(known=known);self.retained_proof=retained;self.tube_decisions=[];self.command_sequence=0;self.commands=[];self.admission_deferrals=[];self.guard_failure=None;self.last_nominal_at=row['proof']['issued_at'];self.sent=[]
 def send(self,packet):self.sent.append(packet)
def run(row,renewal=False,retained=None):
 fixed=row['proof']['issued_at'];space=dict(time=types.SimpleNamespace(monotonic=lambda:fixed),task=dict(goal_xy=goal),require=require);exec(compile(module,str(C/'ros_bridge.py'),'exec'),space);stub=Stub(row,retained);v,w=(0.,0.)if renewal else row['wanted'];space['dispatch_command'](stub,types.SimpleNamespace(linear=types.SimpleNamespace(x=v),angular=types.SimpleNamespace(z=w)),renewal);return stub
for label,target in [('early',9000),('recovery',11000),('late',13000)]:
 row=[r for r in rows if not r.get('wait_renewal')and r['packet']['native_tick']<=target][-1];stub=run(row);sent=[p for p in stub.sent if p['kind']=='command'];checks[label+'_single_or_zero_dispatch']=len(sent)<=1
 for p in sent:assert p['tube']==admit(row['packet'],row['source'],p['v'],p['w'],known,row['proof']['issued_at'])and p['tube']['passed']
 if label=='recovery':checks['saved_10998_actual_callback_dispatches_certified_reverse']=len(sent)==1 and sent[0]['v']<0
 if label=='late':checks['late_no_fake_admission']=not sent and stub.guard_failure is not None
 independent_recovery(stub.tube_decisions,goal);results.append(dict(label=label,tick=row['packet']['native_tick'],sent=stub.sent,decisions=stub.tube_decisions,guard_failure=stub.guard_failure))
 if label=='early':
  waiting=run(row,renewal=True);checks['silence_zero_renewal_never_creates_recovery']=all(x.get('recovery')is None for x in waiting.tube_decisions)and all(p['kind']!='command'or p['v']==p['w']==0 for p in waiting.sent)
nominal=next(r for r in rows if admit(r['packet'],r['source'],*r['wanted'],known,r['proof']['issued_at'])['passed']);stub=run(nominal);checks['passed_nominal_unchanged']=len(stub.commands)==1 and stub.commands[0][1:]==nominal['wanted']and stub.tube_decisions[0]['recovery']is None
bad=copy.deepcopy(results[1]['decisions']);bad[0]['recovery']['selected']=[.1,.1]
try:independent_recovery(bad,goal)
except AssertionError:checks['independent_selected_control_tamper_rejected']=True
else:checks['independent_selected_control_tamper_rejected']=False
proof=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,production_ast_callback=True,results=results);(O/'RECOVERY_CALLBACK_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='results'}));assert proof['passed']
