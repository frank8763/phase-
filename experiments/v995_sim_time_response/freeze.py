"""Freeze this execution bridge and the exact original scientific dependencies."""
import ast,fcntl,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v995_sim_time_response';ROOT=R/'runs/sim_time_recovery_20261110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    files=json.loads((R/'experiments/v993_steering_transient_diagnosis/SOURCE_FREEZE.json').read_text())['files'].copy()
    for p,h in files.items():assert sha(R/p)==h,p
    for p in list(C.iterdir())+[O/'QUALIFICATION.json',O/'EXECUTION_QUALIFICATION.json',O/'ENTRY_QUALIFICATION.json',O/'RESTORE_RECEIPT.json',ROOT/'USER_AUTHORIZATION.json']:
        if p.is_file()and p.name!='SOURCE_FREEZE.json':
            if p.suffix=='.py':ast.parse(p.read_text())
            files[str(p.relative_to(R))]=sha(p)
    assert all(json.loads((O/n).read_text())['passed']for n in ['QUALIFICATION.json','EXECUTION_QUALIFICATION.json','ENTRY_QUALIFICATION.json','RESTORE_RECEIPT.json'])
    with(C/'SOURCE_FREEZE.json').open('x')as f:json.dump(dict(final=True,models_before_freeze=0,scientific_changes=0,execution_mode='SIMULATION_TIME_FIXED_INPUT_NOT_REALTIME',files=files),f,indent=2)
    print(json.dumps(dict(frozen_files=len(files),models=0)))
