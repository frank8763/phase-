"""Exact frozen write-guard reproduction, no file writes at tested paths or models."""
import ast,hashlib,importlib.abc,json,os,sys
from pathlib import Path
from types import SimpleNamespace
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('POSTSTOP_DIAGNOSIS_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
R=Path(__file__).resolve().parents[2]


def main():
    root=R/'runs/v850_poststop_saved_diagnosis';root.mkdir(exist_ok=False)
    campaign=R/'runs/v850_progress_consistent_return';worker=R/'experiments/v850_progress_consistent_worker'
    frozen=json.loads((R/'experiments/v850_progress_consistent_return/CANDIDATE_FREEZE.json').read_text())['files']
    assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in frozen.items())
    assert json.loads((campaign/'ROUND_WINDOW.json').read_text())['round_closed']
    guard_source=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';tree=ast.parse(guard_source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='write_guard')
    paired=R/'runs/v850_progress_consistent_worker/v850_t0_slot01/paired';outer=paired.parent
    namespace=dict(Path=Path,os=os,OUT=paired);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(guard_source),'exec'),namespace)
    failed=outer/'OPERATION_PROFILE.json';allowed=paired/'OPERATION_PROFILE.json'
    try:namespace['write_guard']('open',(str(failed),'w',os.O_WRONLY|os.O_CREAT|os.O_TRUNC))
    except PermissionError as e:message=str(e)
    else:raise AssertionError('ACTUAL_PARENT_OUTPUT_GUARD_DID_NOT_REJECT')
    namespace['write_guard']('open',(str(allowed),'w',os.O_WRONLY|os.O_CREAT|os.O_TRUNC))
    assert not failed.exists()and not allowed.exists(),'DIAGNOSIS_MUST_NOT_WRITE_TESTED_PATHS'
    source=ast.parse((worker/'run_static.py').read_text());loop=next(n for n in ast.walk(source)if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='condition')
    values=eval(compile(ast.Expression(body=loop.iter),str(worker/'run_static.py'),'eval'),dict(a=SimpleNamespace(feasibility_only=True,preflight_only=False,conditions='geometry_memory')))
    assert values==[]
    initial=json.loads((paired/'INITIALIZATION_PROVENANCE.json').read_text());task=json.loads((paired/'TASK_FEASIBILITY.json').read_text())
    assert initial['zero_integration_bootstrap']and initial['initial_time']==0 and initial['bootstrap_repair']['bootstrap_integrations']==0 and task['navigation_steps']==0
    component=json.loads((campaign/'component01/INDEPENDENT_AUDIT.json').read_text());assert component['passed']
    result=dict(status='EXACT_FROZEN_WRITE_SCOPE_FAILURE_REPRODUCED_ZERO_MODEL',cause='New explicit operation-profile final flush targets outer run directory while frozen physical runner write guard permits only paired subtree',rejected_path=str(failed.relative_to(R)),actual_exception=message,proposed_path_scope_allowed=str(allowed.relative_to(R)),proposed_fix_not_applied=True,real_write_guard_source=str(guard_source.relative_to(R)),real_write_guard_sha256=hashlib.sha256(guard_source.read_bytes()).hexdigest(),t0_geometric_eligible=task['eligible'],t0_bootstrap_and_feasibility_integrations=0,t0_navigation_branch_iterator_empty=True,actual_new_navigation=0,planned_navigation_unexecuted=6,physical_component_passed=True,component_counts=component['counts'],original_frozen_sources_exact=True,new_models=0,new_integrations=0,new_model_reads=0,restart_executed=False,limitation='Pure guard proof of proposed output scope; not a patched runner, new t0, navigation result, or relaxation of failed frozen batch')
    (root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
