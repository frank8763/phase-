"""Freeze diagnostic sources/inputs under the existing immutable20:00 root."""
import fcntl,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v993_steering_transient_diagnosis'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert json.loads((O/'QUALIFICATION.json').read_text())['passed']
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    files=json.loads((R/'experiments/v991_coordinated_components/SOURCE_FREEZE.json').read_text())['files'].copy()
    for n,h in files.items():assert sha(R/n)==h,n
    for p in list(C.iterdir())+[O/'QUALIFICATION.json',R/'runs/daytime_20261110_until20/USER_AUTHORIZATION.json']:
        if p.is_file()and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
    frozen=dict(final=True,models_before_freeze=0,absolute_model_deadline_unix=1794312000.,diagnostic_only=True,files=files)
    p=C/'SOURCE_FREEZE.json';assert not p.exists();p.write_text(json.dumps(frozen,indent=2)+'\n')
    print(json.dumps(dict(frozen_files=len(files),models=0,deadline_unix=1794312000.)))
if __name__=='__main__':main()
