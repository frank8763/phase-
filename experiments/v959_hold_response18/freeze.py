"""Lock one candidate and operation source before first authorized model."""
import hashlib
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent;OUT=ROOT/'runs/v959_hold_response18'
assert not(OUT/'AUTHORIZATION.json').exists()
assert json.loads((OUT/'ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
files={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in json.loads((ROOT/'experiments/v953_stop_align_components/SOURCE_FREEZE.json').read_text())['files'].items():
    if p.startswith('runs/'):continue
    assert sha(ROOT/p)==h,'OLD_FROZEN_SOURCE_CHANGED '+p
    files[p]=h
for folder in [CODE,ROOT/'experiments/v958_hold_steering_contract']:
    for p in folder.iterdir():
        if p.is_file()and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(ROOT))]=sha(p)
p=ROOT/'experiments/v956_damped_response18/evaluate.py'
files[str(p.relative_to(ROOT))]=sha(p)
for p in [OUT/'ZERO_MODEL_QUALIFICATION.json',OUT/'USER_INSTRUCTION.json',ROOT/'runs/v958_hold_steering_contract/ZERO_MODEL_QUALIFICATION.json']:
    files[str(p.relative_to(ROOT))]=sha(p)
result=dict(files=files,scope='V959_ORIGINAL18_HOLD_RESPONSE_ONLY',models_at_freeze=0,integrations_at_freeze=0,frozen_unix=time.time())
with(CODE/'SOURCE_FREEZE.json').open('x')as f:json.dump(result,f,indent=2)
print(json.dumps(dict(files=len(files),models=0,integrations=0)))
