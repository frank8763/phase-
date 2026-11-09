"""Freeze complete old runtime closure plus new recovery sources and prerequisites."""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v943_rpccr_segment_navigation'
assert not(OUT/'AUTHORIZATION.json').exists(),'FREEZE_AFTER_AUTHORITY_FORBIDDEN'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


original=json.loads((ROOT/'experiments/v934_rpccr_certified_recovery/SOURCE_FREEZE.json').read_text())['files']
base={p:h for p,h in original.items() if '__pycache__' not in Path(p).parts and not p.endswith('.pyc')}
assert all(sha(ROOT/p)==value for p,value in base.items()),'FROZEN_BASE_CHANGED'
files=dict(base)
for folder in [CODE,*[ROOT/'experiments'/name for name in ['v936_rpccr_corridor_search','v938_rpccr_recovery_segments','v939_rpccr_rpp_handoff','v941_rpccr_reference_loss_binding']]]:
    for path in folder.iterdir():
        if path.is_file() and path.name!='SOURCE_FREEZE.json':files[str(path.relative_to(ROOT))]=sha(path)
for path in OUT.glob('*QUALIFICATION.json'):files[str(path.relative_to(ROOT))]=sha(path)
for path in (OUT/'prior_t0').iterdir():files[str(path.relative_to(ROOT))]=sha(path)
result=dict(files=files,scope='V943_REF_LOSS_SEGMENT_NAVIGATION',models_at_freeze=0,
            integrations_before_freeze=0,frozen_unix=time.time(),
            excluded_derived_bytecode_entries=len(original)-len(base),
            final=sys.argv[-1]=='final')
(CODE/'SOURCE_FREEZE.json').write_text(json.dumps(result,indent=2)+'\n')
if not result['final']:(OUT/'PRELIMINARY_SOURCE_FREEZE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(files=len(files),final=result['final'],models=0,integrations=0)))
