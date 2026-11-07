"""One-shot zero-model source/decompressed SHA readback of the night supplement."""
import gzip
import hashlib
import json
from pathlib import Path
import signal
import zipfile

repo = Path(__file__).resolve().parents[2]
dest = repo / 'evidence/global_dynamic_overnight_20261104_supplement'
assert not dest.exists()
dest.mkdir()
(dest/'blobs').mkdir()
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('600S_ARCHIVE_LIMIT')))
signal.alarm(600)
names = ['GLOBAL_DYNAMIC_OVERNIGHT_AUTHORIZATION_20261104.json',
    'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json', 'CURRENT_EXPERIMENT.json',
    'docs/GLOBAL_DYNAMIC_OVERNIGHT_20261104_PLAN.md',
    'docs/GLOBAL_DYNAMIC_OVERNIGHT_20261104_REPORT.md',
    'docs/RPCCR_TIME_REFERENCE_GLOBAL_V809_REPORT.md',
    'docs/RPCCR_FORWARD_REFERENCE_GLOBAL_V810_REPORT.md',
    'runs/global_dynamic_overnight_20261104/OVERNIGHT_HANDOFF.md',
    'runs/global_dynamic_overnight_20261104/RESERVED_CONFIRMATION_TASKS.json',
    'runs/v809_finalize.console', 'runs/v809_transport.console',
    'runs/v810_qualification.console', 'runs/v810_qualification_audit.console',
    'runs/v810_finalize.console']
for name in ['check_saved_arrival_v809.py','analyze_v809_closed.py','plot_v809_actual.py',
             'prepare_v810.py','archive_overnight_20261104_supplement.py']:
    names.append('experiments/dynamic_reactive_20261104_analysis/'+name)
for directory in ['runs/v809_closed_diagnosis','runs/report_materials_v809_20261104']:
    names.extend(str(p.relative_to(repo)) for p in sorted((repo/directory).rglob('*')) if p.is_file())
sha = lambda b: hashlib.sha256(b).hexdigest()
inventory = []
for name in sorted(set(names)):
    p = repo/name
    raw = p.read_bytes()
    h = sha(raw)
    blob = dest/'blobs'/(h+'.gz')
    if not blob.exists(): blob.write_bytes(gzip.compress(raw, mtime=0))
    inventory.append(dict(path=name, bytes=len(raw), sha256=h, blob=str(blob.relative_to(dest))))
for x in inventory:
    decoded = gzip.decompress((dest/x['blob']).read_bytes())
    assert len(decoded) == x['bytes'] and sha(decoded) == x['sha256']
    assert sha((repo/x['path']).read_bytes()) == x['sha256']
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
bundle = dest/'V809_V810_actual_results_and_trajectory.zip'
with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED) as z:
    for name in ['docs/GLOBAL_DYNAMIC_OVERNIGHT_20261104_REPORT.md',
        'runs/report_materials_v809_20261104/v809_actual_global_failure.png',
        'runs/report_materials_v809_20261104/PROVENANCE.json',
        'runs/v809_closed_diagnosis/RESULT.json',
        'runs/v809_closed_diagnosis/V810_FIXED_INPUT_COMPARISON.json']:
        z.write(repo/name,name)
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    for name in z.namelist(): assert sha(z.read(name)) == sha((repo/name).read_bytes())
manifest = [dict(path=str(p.relative_to(dest)), bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
    for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for x in manifest: assert sha((dest/x['path']).read_bytes()) == x['sha256']
summary = dict(status='NIGHT_SUPPLEMENT_SOURCE_AND_DECOMPRESSED_SHA_PASS',
    sources=len(inventory), raw_bytes=sum(x['bytes'] for x in inventory),
    manifest_entries=len(manifest), archive=str(dest.relative_to(repo)),
    bundle=str(bundle.relative_to(repo)), new_models=0, integrations=0, raw_deleted=False)
(repo/'runs/global_dynamic_overnight_20261104/SUPPLEMENT_ARCHIVE_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
signal.alarm(0)
print(json.dumps(summary))
