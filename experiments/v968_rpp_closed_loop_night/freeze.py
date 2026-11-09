"""Freeze live dependency closure, new science, protocols, tables and zero-model proofs."""
import hashlib
import json
import time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v968_rpp_closed_loop_night'
assert not(O/'AUTHORIZATION.json').exists(),'FREEZE_AFTER_MODEL_AUTHORITY_FORBIDDEN'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R/'experiments/v963_continuous_dynamic/SOURCE_FREEZE.json').read_text())['files']
files={};retired=[]
for rel,value in old.items():
    p=R/rel
    if rel.startswith(('runs/','records/')):
        retired.append(dict(path=rel,sha256=value,role='Previous closed-run metadata/input, not a live runtime dependency.'));continue
    assert p.is_file()and sha(p)==value,'FROZEN_OLD_SOURCE_CHANGED '+rel
    files[rel]=value
for name in ['v968_rpp_closed_loop_night','v969_rpp_night_closure']:
    for p in(R/'experiments'/name).iterdir():
        if p.is_file()and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
for p in O.glob('*.json'):files[str(p.relative_to(R))]=sha(p)
for rel in ['records/nav2_v955_v960_20261109/v960_hold_response_closure_FINAL_INDEPENDENT_AUDIT.json',
    'runs/v858_nav2_verified/v962/handoff_left/HANDOFF_ARRAYS.npz','runs/v858_nav2_verified/v962/handoff_left/SHAPING.json','runs/v858_nav2_verified/v962/handoff_left/QUALIFICATION.json']:
    files[rel]=sha(R/rel)
data=dict(final=True,files=files,retired_closed_run_inputs=retired,scope='V968 new independent actual closed-loop RPP night; old failed rounds remain closed',
    models_at_freeze=0,integrations_before_freeze=0,frozen_unix=time.time())
(C/'SOURCE_FREEZE.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(frozen_files=len(files),models=0,integrations=0)))
