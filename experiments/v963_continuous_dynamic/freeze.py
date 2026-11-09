"""Freeze live dependency closure, new science, protocols, tables and zero-model proofs."""
import hashlib
import json
import time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v963_continuous_dynamic'
assert not(O/'AUTHORIZATION.json').exists(),'FREEZE_AFTER_MODEL_AUTHORITY_FORBIDDEN'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R/'experiments/v959_hold_response18/SOURCE_FREEZE.json').read_text())['files']
files={};retired=[]
for rel,value in old.items():
    p=R/rel
    if rel.startswith('runs/'):
        retired.append(dict(path=rel,sha256=value,role='Old closed-run qualification moved to verified Release/records; not runtime dependency.'));continue
    assert p.is_file()and sha(p)==value,'FROZEN_OLD_SOURCE_CHANGED '+rel
    files[rel]=value
for name in ['v948_forward_navigation','v961_steering_continuity','v962_continuous_handoff','v963_continuous_dynamic','v964_continuous_closure']:
    for p in(R/'experiments'/name).iterdir():
        if p.is_file()and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
for name in ['ZERO_MODEL_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json','PREPARATION_FAILURES.json','USER_INSTRUCTION.json']:
    p=O/name;files[str(p.relative_to(R))]=sha(p)
for p in(R/'records/nav2_v955_v960_20261109').glob('*FINAL_INDEPENDENT_AUDIT.json'):files[str(p.relative_to(R))]=sha(p)
receipt=R/'runs/v961_steering_continuity/RESTORE_RECEIPT.json';files[str(receipt.relative_to(R))]=sha(receipt)
for row in json.loads(receipt.read_text())['restored']:
    p=R/row['path'];assert sha(p)==row['sha256'];files[row['path']]=row['sha256']
data=dict(final=True,files=files,retired_closed_run_inputs=retired,scope='V961–V966 current90min and conditional fixed08:00 chain',
    models_at_freeze=0,integrations_before_freeze=0,frozen_unix=time.time())
(C/'SOURCE_FREEZE.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(frozen_files=len(files),models=0,integrations=0)))
