"""One-shot closed-batch report archive; mutable metadata is snapshotted explicitly."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import signal
import zipfile

repo=Path(__file__).resolve().parents[2]
dest=repo/'evidence/rpccr_soft_global_reference_v812_20261105_supplement'
assert not dest.exists()
assert json.loads((repo/'runs/v812_soft_global_reference/FINALIZED.json').read_text())['archive']['all_source_and_decompressed_readback_verified']
dest.mkdir();(dest/'blobs').mkdir()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('600S_SUPPLEMENT_LIMIT')))
signal.alarm(600)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
snap=repo/'runs/temporal_progress_20261105/closure_snapshots';snap.mkdir(exist_ok=False)
snapshots=[]
for name in ['CURRENT_EXPERIMENT.json','RPCCR_TEMPORAL_PROGRESS_LEDGER_20261105.json',
    'RESEARCH_STATUS.md','runs/temporal_progress_20261105/HANDOFF.md']:
    source=repo/name;target=snap/source.name;target.write_bytes(source.read_bytes())
    snapshots.append(dict(origin=name,snapshot=str(target.relative_to(repo)),sha256=sha(source),
        captured_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        operational_source_may_later_change=True))
(snap/'SNAPSHOT_ORIGINS.json').write_text(json.dumps(snapshots,indent=2)+'\n')
files=[]
for directory in ['runs/v812_closed_diagnosis','runs/report_materials_v812_20261105',
    'runs/temporal_progress_20261105/closure_snapshots']:
    files.extend(p for p in sorted((repo/directory).rglob('*'))if p.is_file())
files.extend((repo/'experiments/temporal_progress_20261105_analysis').glob('*.py'))
for name in ['docs/RPCCR_SOFT_GLOBAL_REFERENCE_V812_REPORT.md',
    'docs/RPCCR_SOFT_GLOBAL_REFERENCE_V812_ANALYSIS.md',
    'docs/RPCCR_TEMPORAL_PROGRESS_REVIEW_20261105.md',
    'RPCCR_TEMPORAL_PROGRESS_AUTHORIZATION_20261105.json',
    'runs/v812_soft_global_reference/FINALIZED.json',
    'runs/v812_finalize.console','runs/v812_transport.console',
    'runs/v812_closed_analysis.console','runs/v812_actual_plot.console',
    'runs/v812_actual_plot_corrected.console']:
    files.append(repo/name)
inventory=[]
for p in sorted(set(files)):
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();blob=dest/'blobs'/(h+'.gz')
    if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
    inventory.append(dict(path=str(p.relative_to(repo)),sha256=h,bytes=len(raw),blob=str(blob.relative_to(dest))))
for x in inventory:
    raw=gzip.decompress((dest/x['blob']).read_bytes())
    assert len(raw)==x['bytes']and hashlib.sha256(raw).hexdigest()==x['sha256']and sha(repo/x['path'])==x['sha256']
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
bundle=dest/'V812_actual_failure_report_and_trajectory.zip'
with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED)as z:
    for name in ['docs/RPCCR_SOFT_GLOBAL_REFERENCE_V812_ANALYSIS.md',
        'docs/RPCCR_SOFT_GLOBAL_REFERENCE_V812_REPORT.md',
        'runs/report_materials_v812_20261105/v812_actual_global_failure.png',
        'runs/report_materials_v812_20261105/PROVENANCE.json',
        'runs/report_materials_v812_20261105/VISUAL_QA.json',
        'runs/v812_closed_diagnosis/RESULT.json','runs/v812_closed_diagnosis/RECOVERY_REJECTION_DETAIL.json']:
        z.write(repo/name,name)
with zipfile.ZipFile(bundle)as z:
    assert z.testzip()is None
    for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==sha(repo/name)
manifest=[dict(path=str(p.relative_to(dest)),sha256=sha(p),bytes=p.stat().st_size)
    for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for x in manifest:assert sha(dest/x['path'])==x['sha256']
result=dict(status='V812_SUPPLEMENT_SOURCE_AND_DECOMPRESSED_SHA_PASS',
    sources=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),manifest_entries=len(manifest),
    archive=str(dest.relative_to(repo)),bundle=str(bundle.relative_to(repo)),
    snapshot_scope='Mutable operational metadata was copied to immutable closure_snapshots before hashing. Later sync/deletion updates do not change archived snapshot sources.',
    new_models=0,integrations=0,raw_deleted=False)
(repo/'runs/temporal_progress_20261105/SUPPLEMENT_ARCHIVE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
signal.alarm(0);print(json.dumps(result))
