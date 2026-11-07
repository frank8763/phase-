"""Verify one output-only continuation and freeze original-deadline inputs."""
import ast,fcntl,os,subprocess,sys,time
from pathlib import Path
from common import *

class Boundary(BaseException):pass


def main():
    assert Path(sys.argv[0]).is_absolute()
    prior=read(R/'runs/v850_progress_consistent_return/FINALIZED.json');assert prior['status']=='NOT_PASSED'and prior['component_passed']and prior['unexecuted_navigation']==6 and prior['source_and_decompressed_sha_verified']
    deadline=read(R/'runs/v850_progress_consistent_return/ROUND_WINDOW.json')['absolute_deadline_unix'];assert deadline==1794022529.6441045 and time.time()+2400<deadline
    assert read(ROOT/'OUTPUT_QUALIFICATION.json')['passed']
    assert read(ROOT/'reused_t0_slot01/paired/field_preflight/INITIAL_UNSEEN_AUDIT_V699.json')['status']=='PASS'
    for folder in [C,W]:
        for p in folder.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    old=R/'experiments/v850_progress_consistent_worker';changed=[]
    for p in W.glob('*.py'):
        previous=(old/p.name).read_text();current=p.read_text()
        if current==previous:continue
        changed.append(p.name)
        if p.name=='run_static.py':assert current==previous.replace("'v850_progress_consistent_worker'/a.name","'v851_profile_output_worker'/a.name")
        elif p.name=='operation_profile.py':assert current==previous.replace("(Path(outer)/'OPERATION_PROFILE.json')","(Path(outer)/'paired'/'OPERATION_PROFILE.json')")
        else:raise AssertionError('UNAUTHORIZED_SCIENTIFIC_OR_AUDITOR_CHANGE:'+p.name)
    assert set(changed)=={'run_static.py','operation_profile.py'}
    # Actual new engine call site stopped immediately before first unexecuted
    # t0 process. The reused first task is independently checked above.
    import engine
    phase=ROOT/'engine_qualification';phase.mkdir();calls=[];original_popen=engine.subprocess.Popen;original_unchanged=engine.unchanged
    engine.unchanged=lambda:None
    def launch(command,**kwargs):calls.append(list(map(str,command)));raise Boundary()
    engine.subprocess.Popen=launch
    try:
        stage=engine.Stage(deadline,phase=phase,raw=ROOT/'unused_raw')
        try:stage.t0(tasks()[1])
        except Boundary:pass
        else:raise AssertionError('FIRST_NS_T0_BOUNDARY_NOT_REACHED')
    finally:engine.subprocess.Popen=original_popen;engine.unchanged=original_unchanged
    assert len(calls)==1 and calls[0][0]==str(R/'run_phase.sh')and calls[0][1]=='experiments/v851_profile_output_worker/run_static.py'and'10010002'in calls[0]
    cases=[]
    for name,entry,end,expect in [('correct',str(Path(__file__).resolve()),time.time()+60,True),('wrong',str(C/'start.py'),time.time()+60,False),('expired',str(Path(__file__).resolve()),time.time()-1,False)]:
        p=subprocess.run([sys.executable,'-B',str(C/'os_watch.py'),'--probe-only','--pid',str(os.getpid()),'--entrypoint',entry,'--deadline',str(end)],capture_output=True,text=True,timeout=5)
        (ROOT/('os_'+name+'.console')).write_text(p.stdout+p.stderr);assert(p.returncode==0)==expect;cases.append(dict(case=name,passed=True))
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as stream:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert(R/'REVIEW_PENDING').exists()
    files=read(R/'experiments/v850_progress_consistent_return/CANDIDATE_FREEZE.json')['files'].copy();assert all(sha(R/p)==h for p,h in files.items())
    for directory in [C,W]:
        for p in directory.iterdir():
            if p.is_file()and p.suffix in ['.py','.md','.json']:files[str(p.relative_to(R))]=sha(p)
    for p in [ROOT/'SOURCE_EQUIVALENCE.json',ROOT/'AUTHORIZATION.json',ROOT/'OUTPUT_QUALIFICATION.json',R/'runs/v850_progress_consistent_return/component01/INDEPENDENT_AUDIT.json',R/'runs/v850_progress_consistent_return/FINALIZED.json']:
        files[str(p.relative_to(R))]=sha(p)
    dump(ROOT/'OPERATIONS_CHECK.json',dict(passed=True,actual_new_engine_first_unexecuted_model_boundary=True,commands=calls,os_cases=cases,old18_plus_progress_auditor_source_exact=True,reused_original_component_and_t0_causal_audit=True,real_output_guard_and_finally_cases=True,models=0,integrations=0))
    files[str((ROOT/'OPERATIONS_CHECK.json').relative_to(R))]=sha(ROOT/'OPERATIONS_CHECK.json')
    dump(C/'CANDIDATE_FREEZE.json',dict(files=files,frozen_unix=time.time(),scientific_revisions_added=0,operational_repair='OPERATION_PROFILE output under paired only; worker output namespace',original_started_unix=1794017129.6441045,absolute_model_deadline_unix=deadline,new24=0))
    dump(ROOT/'PREPARED.json',dict(passed=True,freeze_sha256=sha(C/'CANDIDATE_FREEZE.json'),files=len(files),new_models=0,new_integrations=0,original_deadline_unix=deadline))
    unchanged();print(read(ROOT/'PREPARED.json'),flush=True)


if __name__=='__main__':main()
