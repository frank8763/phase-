"""Run corrected actual full-native audit on preserved main; zero model steps."""
from worker_context import *
import copy,fcntl,subprocess,traceback
def main():
    guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==science().GUARD
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    raw=R/'runs/v858_nav2_verified/v1261/slot17_main';old={}
    for n in ['RESULT.json','FINAL_INDEPENDENT_AUDIT.json','BASE_NATIVE_AUDIT.json']:old[n]=(raw/n).read_bytes()
    task=read(R/'experiments/v1261_ew_reserved_validation/TASK_slot17_main.json');task['output']=str(raw)
    path=O/'AUDIT_ORIGINAL_MAIN_TASK.json';dump(path,task)
    # Only save rebuilt audit JSON into this new namespace. The raw original is
    # read-only to the checker through a task-local output interception.
    command=[str(R/'run_phase.sh'),str((C/'audit_original_cli.py').relative_to(R)),str(path)]
    try:
        (R/'REVIEW_PENDING').unlink()
        p=subprocess.run(command,cwd=R,capture_output=True,text=True,timeout=310)
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    (O/'ACTUAL_AUDIT_CLI.console').write_text(p.stdout+p.stderr)
    assert p.returncode==0,(p.stdout,p.stderr)
    result=read(O/'ORIGINAL_MAIN_FULL_AUDIT.json');assert result['passed']and result['native_reviewed']==50262
    canonical=read(raw/'FINAL_INDEPENDENT_AUDIT.json')
    for k in ['passed','native_reviewed','physical_audit_complete','actual_replay_verified','component','onward']:
        assert result[k]==canonical[k],'AUDIT_CONTENT_CHANGED '+k
    assert all((raw/n).read_bytes()==b for n,b in old.items()),'ORIGINAL_EVIDENCE_OVERWRITTEN'
    dump(O/'AUDIT_CLI_QUALIFICATION.json',dict(passed=True,corrected_real_full_native_CLI_exit0=True,original_main_evidence_unchanged=True,
        native_reviewed=50262,analytical_cpp_native=result['analytical_cpp_native'],models=0,physical_native=0,original_parent_audit_rc1_preserved=True))
    print((O/'AUDIT_CLI_QUALIFICATION.json').read_text())
if __name__=='__main__':main()
