"""One explicit pre-freeze absolute-entry correction; no scientific or physical retry."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from common import R,C,ROOT,W,read,dump,complete_gate,model_fits
from registration import prefix_anchor


def qualify_entry():
    assert not(C/'CANDIDATE_FREEZE.json').exists()and not(ROOT/'LAUNCH_CLAIM.json').exists()
    assert read(ROOT/'NIGHT_COMPLETION.json')['closed']
    error=read(ROOT/'qualification/ERROR.json')
    assert 'os_watch.py'in error['traceback']and 'expected_ok'in error['traceback']
    rows=read(ROOT/'qualification/RESULTS.json')
    assert len(rows)==18 and all(row['exit']==0 for row in rows)
    expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses']
    expected['audit_candidate_policy.py']='GOAL_FIRST_CERTIFIED_POLICY_PASS'
    from common import AUDITS,tasks
    pair=ROOT/'qualification/actual_v842_goal/paired'
    for script,filename,_ in AUDITS:
        result=read(pair/filename);execution=read(pair/(script+'.execution.json'))
        assert result['status']==expected[script]and all(result.get('checks',{}).values())
        assert execution['passed']and execution['original_auditor_sha256']==hashlib.sha256((W/script).read_bytes()).hexdigest()
    for task in tasks():
        path=ROOT/f'qualification/route_{task["seed"]}/paired/discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json'
        result=read(path);assert result['status']=='PASS'and all(result['checks'].values())
        assert prefix_anchor(task['seed']).is_dir()
    assert read(ROOT/'qualification/three_t0/PREFLIGHT_INDEPENDENT_AUDIT.json')['status']=='PASS'
    for name in ['missing_task','wrong_phase']:
        execution=read(ROOT/f'qualification/{name}/audit_field_preflight.py.execution.json')
        text=(ROOT/f'qualification/{name}.console').read_text()
        assert not execution['passed']and execution['original_assertions_preserved']
        assert 'AssertionError'in text and 'assert [x[\'task\'] for x in records]==tasks'in text
    bad=read(ROOT/'qualification/tampered_control/paired/INDEPENDENT_CANONICAL_AUDIT.json')
    assert bad['status']=='FAIL'and not bad['checks']['raw_admission_ctrl']
    synthetic=[dict(task=t,role=role,physical_passed=True,functional_passed=True,repeat_passed=role=='REPEAT')for t in tasks()for role in ['MAIN','REPEAT']]
    assert complete_gate(synthetic)
    for changed in [synthetic[:-1],list(reversed(synthetic)),[dict(x,functional_passed=False)if i==0 else x for i,x in enumerate(synthetic)],[dict(x,repeat_passed=False)if i==1 else x for i,x in enumerate(synthetic)]]:assert not complete_gate(changed)
    try:prefix_anchor(99999999)
    except AssertionError:pass
    else:raise AssertionError('UNKNOWN_TASK_NOT_REJECTED')
    assert model_fits(1000,0,720)and not model_fits(100,99,2)
    cases=[]
    for name,entry,deadline,wanted in [('absolute',str(Path(__file__).resolve()),time.time()+60,True),('wrong',str(R/'experiments/staged_90_then12_20261106/campaign.py'),time.time()+60,False),('expired',str(Path(__file__).resolve()),time.time()-1,False)]:
        result=subprocess.run([sys.executable,'-B',str(C/'os_watch.py'),'--probe-only','--pid',str(os.getpid()),'--entrypoint',entry,'--deadline',str(deadline)],capture_output=True,text=True,timeout=5)
        (ROOT/f'continuation_os_{name}.console').write_text(result.stdout+result.stderr)
        assert(result.returncode==0)==wanted
        cases.append(dict(case=name,expected=wanted,returncode=result.returncode))
    qualification=dict(passed=True,actual_saved17_auditors=rows,actual_saved_auditors=18,
        expected_audit_statuses=expected,three_real_t0_interface_passed=True,
        three_actual_saved_discovery_chains_passed=True,negative_cases=10,policy_negative_cases=16,
        os_identity_cases=cases,model_constructions=0,integrations=0,
        canonical_metadata_proxy_is_only_import_exercise=True,actual_MJB_metadata_required_in_new_stage=True,
        original_qualification_failure_preserved=True,original_error='qualification/ERROR.json',
        operational_correction='Absolute process-entry invocation only; all 18 positive audits and all three discovery chains reused by unchanged source SHA.',
        absolute_model_deadline_unix=1794009600.,scientific_changes_from_preparation=0,new24=0)
    dump(ROOT/'QUALIFICATION.json',qualification)
    dump(ROOT/'PREPARATION_CONTINUATION.json',dict(passed=True,closed=True,models=0,integrations=0,original_failed_completion_preserved=True,os_identity_cases=cases,absolute_model_deadline_unix=1794009600.))


def main():
    if '--prepare-only'in sys.argv:
        qualify_entry();print('ABSOLUTE_ENTRY_AND_RETAINED_EVIDENCE_QUALIFIED_ZERO_MODELS',flush=True);return
    assert read(ROOT/'QUALIFICATION.json')['passed']and read(ROOT/'PREPARATION_CONTINUATION.json')['passed']
    with(ROOT/'ENTRY_CONTINUATION_LAUNCH_CLAIM.json').open('x')as stream:
        json.dump(dict(pid=os.getpid(),started_unix=time.time(),attempts=1,models_already_started=False,original_failure_preserved=True),stream)
    source=(C/'night.py').read_text();original=source
    patches=[("NIGHT_","CONTINUATION_"),("'night.lock'","'continuation.lock'"),("'night_inhibitor.console'","'continuation_inhibitor.console'"),("ROOT/'qualification/COMPLETION.json'","ROOT/'PREPARATION_CONTINUATION.json'"),("rpccr_v848_night_closed_operations_20261106","rpccr_v848_continuation_closed_operations_20261106"),("RPCCR_V848_OVERNIGHT_20261106_MORNING_REPORT.md","RPCCR_V848_CONTINUATION_OVERNIGHT_20261106_MORNING_REPORT.md")]
    for before,after in patches:
        assert before in source;source=source.replace(before,after)
    restored=source
    for before,after in reversed(patches):restored=restored.replace(after,before)
    assert restored==original,'UNREGISTERED_OPERATIONAL_CHANGE'
    dump(ROOT/'OPERATIONAL_CONTINUATION_PATCHES.json',dict(original_sha256=hashlib.sha256(original.encode()).hexdigest(),patches=patches,science_changes=0,models=0,integrations=0,absolute_model_deadline_unix=1794009600.))
    exec(compile(source,str(C/'night.py'),'exec'),dict(__name__='__main__',__file__=str(Path(__file__).resolve())))


if __name__=='__main__':main()
