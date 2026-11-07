"""Freeze actual sources, saved regressions, negative cases and first-model boundary."""
import ast
import importlib.abc
import sys
import time


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('PREPARATION_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
from common import *
from registration import ANCHORS
import engine


def main():
    assert not(C/'CANDIDATE_FREEZE.json').exists()
    assert read(ROOT/'POLICY_QUALIFICATION.json')['passed']and read(ROOT/'QUALIFICATION.json')['passed']
    assert read(ROOT/'INHIBITOR_CAPABILITY_CHECK.json')['passed']
    assert (C/'TASK_LIST.json').read_bytes()==(R/'experiments/v843_three_route_regression/TASK_LIST.json').read_bytes()
    for base in [C,W]:
        for p in base.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    old_worker=R/'experiments/v842_staged_long_navigation'
    allowed={'planner.py','early_joint.py','early_joint_independent.py','run_static.py','audit_early_joint.py','audit_proposal_separation.py'}
    changed={p.name for p in old_worker.glob('*.py')if sha(p)!=sha(W/p.name)}
    assert changed==allowed,('UNDECLARED_SCIENTIFIC_OR_AUDIT_CHANGE',changed)
    assert {p.name for p in W.glob('*.py')}-{p.name for p in old_worker.glob('*.py')}=={'audit_candidate_policy.py'}
    original=(old_worker/'run_static.py').read_text()
    restored=(W/'run_static.py').read_text().replace("'v848_goal_first_worker'/a.name","'v842_staged_long_navigation'/a.name").replace("'V848_GOAL_REFERENCE_AND_FIRST_CERTIFIED_NOMINAL'","'V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS'")
    assert restored==original,'UNDECLARED_RUNNER_CHANGE'
    for name in ['KNOWN_FIELD.json','SCENE_CASES.json']:assert sha(W/name)==sha(old_worker/name)
    dry=ROOT/'operations_dry_run';dry.mkdir(exist_ok=False)
    stage=engine.Stage(1794009600.,phase=dry);calls=[]
    class Boundary(BaseException):pass
    def block(script,args,log,cap,models=False,on_launch=None):
        calls.append(dict(script=script,args=list(map(str,args)),cap=cap,models=models))
        assert script=='run_static.py'and models and'--feasibility-only'in args and args[args.index('--name')+1]=='v848_t0_slot02'and int(args[args.index('--seed')+1])==10010002 and cap==125
        raise Boundary()
    stage.execute=block
    try:stage.run_steps()
    except Boundary:pass
    else:raise AssertionError('MODEL_BOUNDARY_NOT_REACHED')
    assert len(calls)==1 and not stage.rows
    dump(dry/'MODEL_BOUNDARY_CHECK.json',dict(passed=True,actual_engine_run_steps=True,calls=calls,models=0,integrations=0))
    class Finished:
        def wait(self,timeout):assert 0<timeout<=10;return 0
    assert engine.wait_bounded(Finished(),5,True,time.time()+5)==0
    try:engine.wait_bounded(Finished(),5,True,time.time()-1)
    except TimeoutError:pass
    else:raise AssertionError('EXPIRED_MODEL_WAIT_ACCEPTED')
    assert not PHASE.exists()and all(not(RAW/name).exists()for name in names())
    from repeat import compare
    base=R/'runs/v842_staged_long_navigation/long_main08/paired';self_repeat=compare(base,base)
    assert self_repeat['passed'];dump(dry/'SELF_REPEAT_INTERFACE.json',self_repeat)
    checks=dict(passed=True,scientific_candidates=1,declared_scientific_changes=2,
        original_model_and_safety_modules_unchanged=True,old_red_new_green=True,
        actual_saved_complete_certificates=True,actual_saved18_auditor_calls=True,
        first_real_t0_boundary=True,three_original_tasks_byte_exact=True,
        absolute_model_deadline_unix=1794009600.,no_network_dependency=True,
        no_training=True,no_new24=True,models=0,integrations=0)
    dump(ROOT/'OPERATIONS_CHECK.json',checks)
    old=read(R/'experiments/staged_audit_completion_20261106/DEVELOPMENT_FREEZE.json')
    files={p:h for p,h in old['files'].items()if(R/p).is_file()}
    # The original snapshot must still match; original failures are never repaired.
    assert all(sha(R/p)==h for p,h in files.items()),'OLD_FROZEN_DEPENDENCY_CHANGED'
    files.update(read(ROOT/'POLICY_INPUT_FILES.json')['files'])
    for base in [C,W]:
        for p in base.iterdir():
            if p.is_file()and p.name!='CANDIDATE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
    for name in ['AUTHORIZATION.json','QUALIFICATION.json','POLICY_QUALIFICATION.json','OPERATIONS_CHECK.json','SOURCE_CHANGE_RECORD.json','ENTRY_EXCEPTION.json','PREPARATION_CONTINUATION.json','OPERATIONAL_CONTINUATION_PATCHES.json']:
        p=ROOT/name;files[str(p.relative_to(R))]=sha(p)
    for relative in ANCHORS.values():
        for name in ['dynamic_native.jsonl.gz','v648_execution.jsonl']:
            p=R/relative/name;files[str(p.relative_to(R))]=sha(p)
    for name in ['FINALIZED.json','references/RESULTS.json','references/COMPLETION.json']:
        p=R/'runs/v847_gpu_reference_diagnosis'/name;files[str(p.relative_to(R))]=sha(p)
    p=R/'docs/RPCCR_THREE_ROUTE_V848_20261106_PLAN.md';files[str(p.relative_to(R))]=sha(p)
    dump(C/'CANDIDATE_FREEZE.json',dict(files=files,frozen_unix=time.time(),scientific_revisions=1,declared_changes=2,
         scientific_worker=str(W.relative_to(R)/'run_static.py'),absolute_model_deadline_unix=1794009600.,new24=0))
    dump(ROOT/'PREPARED.json',dict(freeze_sha256=sha(C/'CANDIDATE_FREEZE.json'),files=len(files),models=0,integrations=0))
    print(json.dumps(dict(status='V848_FROZEN_READY',files=len(files),models=0,integrations=0)))


if __name__=='__main__':main()
