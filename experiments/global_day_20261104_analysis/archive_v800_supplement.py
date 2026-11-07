"""One immutable archive of V800 saved interpretation and operation metadata."""
import gzip, hashlib, json
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
dest = repo / 'evidence/rpccr_spatial_nominal_global_v800_20261104_supplement'
assert not dest.exists()
assert (repo / 'REVIEW_PENDING').exists()
read = lambda p: json.loads(p.read_text())
assert read(repo / 'runs/v800_spatial_nominal_global/FINAL_INDEPENDENT_AUDIT.json')['source_unchanged']
assert all(x['all_original_audits_passed']for x in read(repo/'runs/v800_spatial_nominal_global/FINAL_INDEPENDENT_AUDIT.json')['records'])
files=set()
for name in ['runs/v800_saved_comparison','runs/v800_saved_diagnosis','runs/v800_saved_geometry_profile','runs/v800_saved_geometry_warm_profile','runs/v800_archive_preparation_error']:
    files.update(p for p in(repo/name).rglob('*')if p.is_file())
for name in [
    'experiments/global_day_20261104_analysis/analyze_v800_closed.py',
    'experiments/global_day_20261104_analysis/analyze_closed_navigation.py',
    'experiments/global_day_20261104_analysis/profile_v800_saved_geometry.py',
    'experiments/global_day_20261104_analysis/profile_v800_warm_queries.py',
    'experiments/global_day_20261104_analysis/archive_v800_supplement.py',
    'experiments/global_day_20261104_analysis/transport_archive.py',
    'experiments/global_day_20261104_analysis/reconstruct_transport.py',
    'docs/RPCCR_SPATIAL_NOMINAL_V799_V800_ANALYSIS.md',
    'docs/RPCCR_SPATIAL_NOMINAL_GLOBAL_V800_REPORT.md',
    'docs/RPCCR_SPATIAL_PREFIX_V799_REPORT.md',
    'RPCCR_SPATIAL_NOMINAL_AUTHORIZATION_20261104.json',
    'RPCCR_SPATIAL_NOMINAL_LEDGER_20261104.json',
    'CURRENT_EXPERIMENT.json','AGENTS.md','RESEARCH_STATUS.md',
    'runs/v800_spatial_nominal_global/FINALIZED.json',
    'runs/v800_spatial_nominal_global/FINAL_INDEPENDENT_AUDIT.json',
    'runs/v800_spatial_nominal_global/CLOSURE_HANDOFF.md',
    'runs/v800_spatial_nominal_global/REVIEW_PENDING.before',
    'runs/v800_driver_launch.json','runs/v800_driver.console','runs/v800_finalize.console',
    'runs/v800_saved_comparison.console','runs/v800_diagnosis.console',
    'runs/v800_geometry_profile.console','runs/v800_geometry_warm_profile.console',
    'runs/v800_transport.console',
    'evidence/rpccr_spatial_nominal_global_v800_20261104_transport/TRANSPORT_MANIFEST.json',
]:
    files.add(repo/name)
dest.mkdir(); (dest / 'blobs').mkdir()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
inventory = []
for p in sorted(files):
    raw = p.read_bytes(); h = sha(raw); blob = dest / 'blobs' / (h+'.gz')
    packed = gzip.compress(raw, mtime=0)
    if blob.exists(): assert blob.read_bytes() == packed
    else: blob.write_bytes(packed)
    inventory.append(dict(path=str(p.relative_to(repo)), bytes=len(raw), sha256=h,
                          blob=str(blob.relative_to(dest))))
(dest / 'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
    raw = gzip.decompress((dest / row['blob']).read_bytes())
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    assert sha((repo / row['path']).read_bytes())==row['sha256']
manifest=[dict(path=str(p.relative_to(dest)), bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
          for p in sorted(dest.rglob('*')) if p.is_file()]
(dest / 'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha((dest / r['path']).read_bytes())==r['sha256'] for r in manifest)
summary=dict(status='SUPPLEMENT_SOURCE_AND_DECOMPRESSED_BYTES_VERIFIED',
    source_files=len(inventory),raw_bytes=sum(r['bytes'] for r in inventory),
    manifest_entries=len(manifest),model_initializations=0,integrations=0,raw_deleted=False)
(repo / 'runs/v800_supplement_archive_result.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
