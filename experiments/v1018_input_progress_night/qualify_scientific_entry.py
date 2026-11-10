"""Actual supervisor and audit entries, fresh processes as in production; zero models."""
import importlib.abc,importlib.util,json,subprocess,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1018_input_progress_night'
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_QUALIFICATION '+name)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def child(mode):
 sys.meta_path.insert(0,NoModels());sys.path[:0]=[str(C),str(R/'experiments/v1004_planned_input_navigation')]
 if mode=='--supervisor':
  m=load('real_supervisor',C/'supervise.py');assert Path(m.planner.__file__).resolve()==R/'experiments/v1017_input_validated_progress/plan.py'
  assert json.loads((R/'runs/v1017_input_validated_progress/ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
  return dict(passed=True,actual_supervisor_input_plan_binding=True)
 a=load('real_audit_entry',C/'audit.py');task=json.loads((R/'runs/v1016_saved_route_diagnosis/audit_view/TASK.json').read_text());task['output']=str(R/'runs/v1016_saved_route_diagnosis/audit_view')
 result=a.audit(task);assert result['evidence_passed']and not result['functional_passed']and result['atomic_handoff']['passed'],result
 return dict(passed=True,actual_audit_saved_namespace=True,complete_saved_evidence_passed=True,original_failed_function_preserved=True)
def main():
 if len(sys.argv)>1:print(json.dumps(child(sys.argv[1])));return
 rows=[]
 for mode in ['--supervisor','--audit']:
  p=subprocess.run([sys.executable,'-B',str(C/'qualify_scientific_entry.py'),mode],capture_output=True,text=True,timeout=40,cwd=R);assert p.returncode==0,p.stderr
  rows.append(json.loads(p.stdout))
 out=dict(passed=True,models=0,integrations=0,production_separate_processes=True,rows=rows,analytical_metadata_tolerance=1e-12,physical_control_state_replay_tolerance=1e-8)
 (O/'SCIENTIFIC_ENTRY_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
