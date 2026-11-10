"""Actual audit pre-ARM classification and task-clock receipt negatives."""
import copy,hashlib,importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v991_coordinated_components'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import authority
import audit
from budget import create
def main():
    checks={};cases=[]
    for label,armed,count in [('prearm_zero',None,0),('prearm_unknown',None,None),('armed_missing_evidence',123.,None)]:
        out=O/label;out.mkdir()
        (out/'RESULT.json').write_text(json.dumps(dict(status='PREARM_ABORT'if armed is None else'FAILED',armed_at=armed,new_branch_native=count,error='ORIGINAL_FIXTURE_FAILURE')))
        result=audit.audit(dict(output=str(out),stage='component'))
        assert result['passed']is False
        if armed is None:
            assert result['reason']=='NO_ARM_COMPONENT_NOT_EXECUTED'and result['exact_new_branch_native']==count
            assert result['actuation']['status']=='NOT_EXECUTED'and not result['actuation']['passed']
            assert result['original_native_error']=='ORIGINAL_FIXTURE_FAILURE'
        else:assert 'error'in result and result.get('reason')!='NO_ARM_COMPONENT_NOT_EXECUTED'
        cases.append(dict(case=label,passed=True,original_failure_retained=True))
    checks['prearm_not_misreported_as_actuation_pass']=True
    out=O/'clock_receipt';out.mkdir();wall=time.time();root=wall+5000.
    task=dict(run_id='CLOCK_FIXTURE',output=str(out),stage='component',slot=0,wall_limit_s=40.,brake_s=2.,origin_native_tick=6083,origin_sim_time=60.83)
    auth=dict(deadline_unix=root);record=create(task,root)
    path=out/'TASK_CLOCK.json';path.write_text(json.dumps(record))
    receipt=dict(auth,run_id=task['run_id'],task_sha256=authority.digest(task),task_clock_sha256=authority.sha(path))
    saved_root=authority.root_authorized;saved_read=authority.read
    def read(p):return [task]if Path(p)==C/'TASKS.json'else saved_read(p)
    authority.root_authorized=lambda *args:auth;authority.read=read
    try:
        checks['actual_authority_accepts_exact_clock']=authority.authorized(task,receipt,wall,'FIXTURE')==root
        changed=copy.deepcopy(record);changed['hard_deadline_unix']+=1.;path.write_text(json.dumps(changed))
        try:authority.authorized(task,receipt,wall,'FIXTURE')
        except AssertionError:checks['actual_authority_rejects_extended_task_clock']=True
        else:checks['actual_authority_rejects_extended_task_clock']=False
        path.write_text(json.dumps(record));changed_receipt=dict(receipt,task_clock_sha256='0'*64)
        try:authority.authorized(task,changed_receipt,wall,'FIXTURE')
        except AssertionError:checks['actual_authority_rejects_false_clock_sha']=True
        else:checks['actual_authority_rejects_false_clock_sha']=False
    finally:authority.root_authorized=saved_root;authority.read=saved_read
    result=dict(passed=all(checks.values()),checks=checks,cases=cases,models=0,integrations=0,
        actual_audit_and_authority_seams=True,clock_fixture_not_physical_authority=True)
    (O/'REPORTING_CLOCK_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
if __name__=='__main__':main()
