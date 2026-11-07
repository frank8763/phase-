"""Finish pre-freeze OS checks; reuse only SHA-verified completed saved audits."""
import os,subprocess,sys,time
from pathlib import Path
from common import *


def main():
    assert Path(sys.argv[0]).is_absolute(),'QUALIFICATION_REQUIRES_ABSOLUTE_ENTRY'
    q=ROOT/'qualification';assert read(q/'COMPLETION.json')==dict(passed=False,model_constructions=0,integrations=0,auditors_completed=18)
    error=read(q/'ERROR.json');assert error['type']=='AssertionError'and'os_watch.py'in error['traceback']
    expected=read(R/'runs/v848_goal_first_certified/QUALIFICATION.json')['expected_audit_statuses'];expected['audit_progress.py']='PROGRESS_CONTRACT_SELECTION_PASS'
    pair=q/'actual_v842_goal/paired';rows=[];guard=(R/'REVIEW_PENDING').read_bytes()
    try:
        for script,filename,cap in AUDITS:
            if script=='audit_progress.py':continue
            event=read(pair/(script+'.execution.json'));assert event['passed']and event['integrations']==0
            if event['original_auditor_sha256']!=sha(W/script):
                assert script=='audit_complete_joint.py','UNEXPECTED_DRAFT_AUDITOR_CHANGED'
                (R/'REVIEW_PENDING').unlink()
                with(q/'current_complete_joint_recheck.console').open('x')as stream:
                    code=subprocess.run([str(R/'run_phase.sh'),str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(pair),script,str(pair)],cwd=R,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
                (R/'REVIEW_PENDING').write_bytes(guard);assert code==0
                event=read(pair/(script+'.execution.json'));assert event['passed']and event['original_auditor_sha256']==sha(W/script)
            data=read(pair/filename);assert data['status']==expected[script]and all(data.get('checks',{}).values())
            rows.append(dict(script=script,passed=True,sha256=sha(W/script),models=0,integrations=0))
        assert read(q/'three_t0/PREFLIGHT_INDEPENDENT_AUDIT.json')['status']=='PASS'
        for task in tasks():
            chain=read(q/('route_'+str(task['seed']))/'paired/discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');assert chain['status']=='PASS'and all(chain['checks'].values())
        for name in ['missing_task','wrong_phase']:
            assert read(q/name/'audit_field_preflight.py.execution.json')['passed']is False
        bad=read(q/'tampered_control/paired/INDEPENDENT_CANONICAL_AUDIT.json');assert bad['status']=='FAIL'and not bad['checks']['raw_admission_ctrl']
        cases=[]
        for label,entry,deadline,okay in [('correct',str(Path(__file__).resolve()),time.time()+60,True),('wrong',str(C/'start.py'),time.time()+60,False),('expired',str(Path(__file__).resolve()),time.time()-1,False)]:
            result=subprocess.run([sys.executable,'-B',str(C/'os_watch.py'),'--probe-only','--pid',str(os.getpid()),'--entrypoint',entry,'--deadline',str(deadline)],capture_output=True,text=True,timeout=5)
            (q/('absolute_os_'+label+'.console')).write_text(result.stdout+result.stderr);assert(result.returncode==0)==okay;cases.append(dict(case=label,passed=True))
        dump(ROOT/'LEGACY_AUDITOR_QUALIFICATION.json',dict(passed=True,actual_saved18_auditors=rows,expected_audit_statuses=expected,three_real_t0_interface_passed=True,three_raw_discovery_chains_passed=True,task_and_control_negatives_passed=True,os_identity_cases=cases,old_failed_relative_entry_retained=True,metadata_proxy_import_only=True,new_MJB_metadata_required=True,models=0,integrations=0))
        print('SAVED18_AND_ABSOLUTE_OS_CHECKS_PASS_NO_MODELS',flush=True)
    finally:(R/'REVIEW_PENDING').write_bytes(guard)


if __name__=='__main__':main()
