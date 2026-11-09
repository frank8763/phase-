"""Preregistered task/authority positive and negative checks, zero models."""
import ast, hashlib, json, pathlib, sys
from unittest.mock import patch

R=pathlib.Path(__file__).resolve().parents[2]
C=R/'experiments/v905_reference_execution_separation'
O=R/'runs/v905_reference_execution_separation'
sys.path.insert(0,str(C))
import authority

def main():
    tasks=json.loads((C/'TASKS.json').read_text())
    root=dict(models_authorized=True,started_unix=100000.,deadline_unix=105400.,source_freeze_sha256='SAVED_SHA')
    checks={}
    def read(path):
        path=pathlib.Path(path)
        if path.name in ['AUTHORIZATION.json','ROUND_WINDOW.json']:return root
        if path.name=='platform_continuation_result.json':return {'passed':True}
        if path.name=='TASKS.json':return tasks
        if path.name=='NAVIGATION_FREEZE.json':return {'source_freeze_sha256':'SAVED_SHA'}
        if path.name=='PREFLIGHTS.json':return {x['case_id']:{'passed':True}for x in tasks}
        if path.name=='INDEPENDENT_AUDIT.json':return {'passed':True}
        raise AssertionError(str(path))
    now=root['started_unix']+1
    def receipt(task):return dict(models_authorized=True,scope=authority.SCOPE,deadline_unix=root['deadline_unix'],run_id=task['run_id'],task_sha256=authority.digest(task),source_freeze_sha256='SAVED_SHA')
    with patch.object(authority,'read',read):
        for task in tasks:
            checks['allowed_'+task['task_id']]=authority.authorized(task,receipt(task),now,'SAVED_SHA')==root['deadline_unix']
        t=tasks[1]
        variants=[('models',dict(models_authorized=False),now,'SAVED_SHA'),('scope',dict(scope='OLD'),now,'SAVED_SHA'),('deadline',dict(deadline_unix=root['deadline_unix']+1),now,'SAVED_SHA'),('digest',dict(task_sha256='BAD'),now,'SAVED_SHA'),('source',{},now,'BAD'),('expired',{},root['deadline_unix']-29,'SAVED_SHA')]
        for label,changes,when,sha in variants:
            a=receipt(t);a.update(changes)
            try:authority.authorized(t,a,when,sha)
            except RuntimeError:checks['reject_'+label]=True
            else:checks['reject_'+label]=False
        changed=dict(t,phase=t['phase']+.01)
        try:authority.authorized(changed,receipt(changed),now,'SAVED_SHA')
        except RuntimeError:checks['reject_changed_task']=True
        else:checks['reject_changed_task']=False
    for source in C.glob('*.py'):ast.parse(source.read_text(),filename=str(source))
    checks['tasks_exact_three_routes_six_navigation']=len(tasks)==6 and sum(t['role']!='dynamic_t0'for t in tasks)==6 and len({t['case_id']for t in tasks})==3
    result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,scope='Actual authority function on fixed synthetic dependency receipts; genuine physics/dependency gates remain separate')
    (O/'RELEASE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1

if __name__=='__main__':sys.exit(main())
