"""Freeze before any new V953 model, retaining original source bytes."""
import hashlib
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent;OUT=ROOT/'runs/v953_stop_align_components'
assert not(OUT/'AUTHORIZATION.json').exists(),'SOURCE_FREEZE_AFTER_AUTHORITY_FORBIDDEN'
assert json.loads((OUT/'ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
assert json.loads((ROOT/'runs/v952_stopped_steering_alignment/ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((ROOT/'experiments/v950_steering_response/SOURCE_FREEZE.json').read_text())['files'];files={}
for relative,expected in base.items():
    if relative.startswith('runs/'):continue
    path=ROOT/relative;assert path.is_file()and sha(path)==expected,'OLD_SOURCE_CHANGED '+relative
    files[relative]=expected
for folder in [CODE,ROOT/'experiments/v952_stopped_steering_alignment']:
    for path in folder.iterdir():
        if path.is_file()and path.name!='SOURCE_FREEZE.json':files[str(path.relative_to(ROOT))]=sha(path)
for path in [OUT/'USER_WINDOW_APPROVAL.json',OUT/'ZERO_MODEL_QUALIFICATION.json',ROOT/'runs/v952_stopped_steering_alignment/ZERO_MODEL_QUALIFICATION.json',ROOT/'runs/v952_stopped_steering_alignment/RESTORE_RECEIPT.json']:
    files[str(path.relative_to(ROOT))]=sha(path)
result=dict(files=files,scope='V953_ORIGINAL18_THEN_STOP_ALIGN_FORWARD_1P2M',models_at_freeze=0,
    integrations_at_freeze=0,frozen_unix=time.time(),navigation_authorized=False)
(CODE/'SOURCE_FREEZE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(files=len(files),models=0,integrations=0)))
