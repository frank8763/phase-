"""Real saved-failure audit seam, production imports, paths and native guard."""
import ast,importlib.abc,json,shutil,sys,tempfile,subprocess
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1053_parked_refresh_handoff';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from audit import audit_native
from handoff import planes
import copy
def main():
 for name in ['full_worker','driver','watchdog','start','close','source_job']:load('v1053_entry_'+name,C/(name+'.py'))
 worker=load('v1053_qualified_physical_entry',C/'full_worker.py');h,setup=worker.history_files();assert len(json.loads((h/'physics/BODY_COMMANDS.json').read_text()))==23640
 x=json.loads((O/'INPUT_SOURCE.json').read_text());original=json.loads((O/'SELECTED_PLAN.json').read_text());ss,uu,rr,mm=worker.regenerate(setup,x['packet'],original);assert len(rr)==17251
 negative=[]
 with tempfile.TemporaryDirectory(dir=O,prefix='saved_audit_fixture_')as temp:
  out=Path(temp);out.joinpath('physics').mkdir();H=O/'inputs'
  for name in ['SETUP.json','NATIVE_TRACE.npz','BODY_COMMANDS.json']:out.joinpath('physics',name).symlink_to(H/'physics'/name)
  result=json.loads((H/'RESULT.json').read_text());dump(out/'RESULT.json',result);view=dict(original,planning_packet=x['packet'],planning_source=x['source'],publication_source=x['source'],published_packet=x['packet'],publication_age_s=0.);dump(out/'ADOPTED_PLAN.json',view)
  # audit loads the producer RESULT beside ADOPTED_PLAN. Keep the native
  # result outside that epoch directory to exercise the exact production path.
  epoch=out/'refresh/epoch00';epoch.mkdir(parents=True);dump(epoch/'ADOPTED_PLAN.json',view);dump(epoch/'RESULT.json',dict(source_planes=planes(x['source']['periodic']['vertices'])));dump(out/'EXECUTION_SEGMENTS.json',[dict(kind='REQUALIFIED_INPUT',start_native=23640,executed_native=14144,state_path=original['state_path'],adopted_plan=str((epoch/'ADOPTED_PLAN.json').relative_to(R)))])
  proof=audit_native(dict(output=str(out),goal_xy=x['goal']));assert proof['safety_passed']and not proof['passed']and not proof['prediction']['passed'];assert abs(proof['prediction']['position_m']-.04000001184448314)<1e-10;negative.append('original_V1051_40mm_failure_preserved_in_new_saved_audit')
 # Every software-produced adoption must regenerate at its declared anchor
 # and pass the complete shifted-time geometry under its actual publish clock.
 verified_adoptions=0
 for plan_file in sorted((O/'software_full_executor/refresh').glob('*/ADOPTED_PLAN.json')):
  adopted=json.loads(plan_file.read_text());s,u,rr,m=predict(setup,adopted['planning_packet'],adopted['actions'],tail=False);assert abs(s-np.array(adopted['state_path'])).max()<=1e-8;geometry=Geometry(setup['known'],adopted['planning_source']['periodic'],adopted['published_packet']['sim_time']);low=geometry.complete(s);gates,upper=checks(s,u,rr,adopted['planning_packet'],setup,np.array(x['goal']),low,REQUIRED);assert all(gates.values());verified_adoptions+=1
 assert verified_adoptions==11
 p=subprocess.run([str(R/'run_phase.sh'),'experiments/v1053_parked_refresh_handoff/full_worker.py',str(C/'TASK_full_main.json'),str(O/'NO_AUTHORITY.json')],cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr
 for path in C.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
 assert all(not Path(t['output']).exists()for t in json.loads((C/'FULL_TASKS.json').read_text()));assert HARD_END==1794400200.;dump(O/'ENTRY_QUALIFICATION.json',dict(passed=True,production_imports=6,history_all_sha=True,original_full_source_regenerated=True,native_guard_blocks=True,source_parse=True,software_complete_adoptions_independently_regenerated=verified_adoptions,outputs_new=True,deadline_unchanged=True,negative_cases=negative,models=0,integrations=0,new_mjb_audit=False));print(json.dumps(dict(passed=True,negative=negative,models=0)))
if __name__=='__main__':main()
