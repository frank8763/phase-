"""Freeze V977 science plus bounded physical entry and exact saved evidence."""
import ast,hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v982_precise_recovery_gate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(O/'AUTHORIZATION.json').exists()
assert json.loads((O/'ZERO_MODEL_ENTRY_QUALIFICATION.json').read_text())['passed']
assert json.loads((O/'SOFTWARE_QUALIFICATION.json').read_text())['passed']
assert json.loads((O/'BINDING_QUALIFICATION.json').read_text())['passed']
files={}
for rel,digest in json.loads((R/'experiments/v981_tracking_evidence_closure/SOURCE_FREEZE.json').read_text())['files'].items():
    assert sha(R/rel)==digest;files[rel]=digest
for path in C.iterdir():
    if path.is_file()and path.name!='SOURCE_FREEZE.json':
        if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
        files[str(path.relative_to(R))]=sha(path)
for path in [O/'SEED_HISTORY_0.json',O/'SEED_HISTORY_1.json',O/'ZERO_MODEL_ENTRY_QUALIFICATION.json',O/'SOFTWARE_QUALIFICATION.json',O/'BINDING_QUALIFICATION.json']:
    files[str(path.relative_to(R))]=sha(path)
for path in [R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json']:
    files[str(path.relative_to(R))]=sha(path)
(C/'SOURCE_FREEZE.json').write_text(json.dumps(dict(final=True,awaiting_explicit_physical_approval=True,models_before_freeze=0,integrations_before_freeze=0,frozen_unix=time.time(),files=files),indent=2)+'\n')
print(json.dumps(dict(frozen=len(files),models=0,integrations=0)))
