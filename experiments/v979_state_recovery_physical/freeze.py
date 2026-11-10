"""Freeze V977 science plus bounded physical entry and exact saved evidence."""
import ast,hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v979_state_recovery_physical'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(O/'AUTHORIZATION.json').exists()
assert json.loads((O/'ZERO_MODEL_ENTRY_QUALIFICATION.json').read_text())['passed']
assert json.loads((O/'SOFTWARE_RESULTS_attempt3.json').read_text())['passed']
files={}
for rel,digest in json.loads((R/'experiments/v977_state_consistent_recovery/SOURCE_FREEZE.json').read_text())['files'].items():
    assert sha(R/rel)==digest;files[rel]=digest
for path in C.iterdir():
    if path.is_file()and path.name!='SOURCE_FREEZE.json':
        if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
        files[str(path.relative_to(R))]=sha(path)
for path in(O/'prior_v974').rglob('*'):
    if path.is_file()and not path.is_symlink():files[str(path.relative_to(R))]=sha(path)
for path in [O/'SEED_HISTORY_0.json',O/'SEED_HISTORY_1.json',O/'ZERO_MODEL_ENTRY_QUALIFICATION.json',O/'SOFTWARE_RESULTS_attempt3.json']:
    files[str(path.relative_to(R))]=sha(path)
for path in [R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json']:
    files[str(path.relative_to(R))]=sha(path)
(C/'SOURCE_FREEZE.json').write_text(json.dumps(dict(final=True,models_before_freeze=0,integrations_before_freeze=0,frozen_unix=time.time(),files=files),indent=2)+'\n')
print(json.dumps(dict(frozen=len(files),models=0,integrations=0)))
