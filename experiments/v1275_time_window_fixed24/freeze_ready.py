"""Finalize evidence hashes once, after zero-model qualification, before start."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    assert not(O/'ROUND_WINDOW.json').exists()and not(O/'FROZEN_READY.json').exists(),'ONE_FINAL_FREEZE_BEFORE_MODELS'
    assert json.loads((O/'QUALIFICATION.json').read_text())['passed']and json.loads((O/'ISOLATED_QUALIFICATION.json').read_text())['passed']
    files=json.loads((C/'SOURCE_FREEZE.json').read_text())['files']
    assert all(sha(R/p)==h for p,h in files.items()),'SCIENCE_OR_OPERATIONS_CHANGED_SINCE_PREPARATION'
    for p in O.rglob('*'):
        if p.is_file()and not p.is_symlink()and p.name not in['AUTHORIZATION.json','APPROVAL.json']and not p.name.endswith('.console'):
            files[str(p.relative_to(R))]=sha(p)
    for name in ['SOURCE_FREEZE.json','WORKER_FREEZE.json']:
        (C/name).write_text(json.dumps(dict(files=files,qualified_before_physical=True,source_unchanged=True),indent=2)+'\n')
    assert all(sha(R/p)==h for p,h in files.items())
    result=dict(passed=True,source_unchanged=True,files=len(files),models=0,physical_native=0)
    (O/'FROZEN_READY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
