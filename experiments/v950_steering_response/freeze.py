"""Freeze complete retained old source closure and the new component candidate."""
import hashlib
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v950_steering_response'
assert not(OUT/'AUTHORIZATION.json').exists(),'FREEZE_AFTER_AUTHORITY_FORBIDDEN'
assert json.loads((OUT/'ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
files={};removed=[]
base=json.loads((ROOT/'experiments/v945_rpccr_observation_liveness/SOURCE_FREEZE.json').read_text())['files']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for relative,expected in base.items():
    p=ROOT/relative
    if relative.startswith('runs/'):continue
    assert p.is_file()and sha(p)==expected,'OLD_SOURCE_CHANGED '+relative
    files[relative]=expected
for folder in [CODE,ROOT/'experiments/v949_steering_handoff']:
    for p in folder.iterdir():
        if p.is_file()and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(ROOT))]=sha(p)
for p in [OUT/'USER_WINDOW_APPROVAL.json',OUT/'ZERO_MODEL_QUALIFICATION.json',ROOT/'runs/v949_steering_handoff/QUALIFICATION.json']:
    files[str(p.relative_to(ROOT))]=sha(p)
result=dict(files=files,scope='18_FIXED_RESPONSES_THEN_ONE_HANDOFF_ONLY',models_at_freeze=0,
            integrations_at_freeze=0,frozen_unix=time.time(),navigation_authorized=False)
(CODE/'SOURCE_FREEZE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(files=len(files),models=0,integrations=0)))
