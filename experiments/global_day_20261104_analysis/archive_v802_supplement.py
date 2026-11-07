"""One immutable archive of V800 saved interpretation and operation metadata."""
import gzip, hashlib, json
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
dest = repo / 'evidence/rpccr_exact_rejection_global_v802_20261104_supplement'
assert not dest.exists()
assert (repo / 'REVIEW_PENDING').exists()
read = lambda p: json.loads(p.read_text())
assert read(repo / 'runs/v802_exact_rejection_global/FINAL_INDEPENDENT_AUDIT.json')['source_unchanged']
assert read(repo/'runs/v802_pointwise_witness_supplement/RESULT.json')['status']=='POINTWISE_WITNESS_SUPPLEMENT_PASS'
files=set()
for name in ['runs/v801_exact_rejection_qualification','runs/v802_saved_comparison','runs/v802_saved_diagnosis','runs/v802_pointwise_witness_supplement']:
    files.update(p for p in(repo/name).rglob('*')if p.is_file())
for name in [
 'experiments/global_day_20261104_analysis/analyze_v802_closed.py',
 'experiments/global_day_20261104_analysis/analyze_closed_navigation.py',
 'experiments/global_day_20261104_analysis/audit_v802_pointwise_supplement.py',
 'experiments/global_day_20261104_analysis/archive_v802_supplement.py',
 'experiments/global_day_20261104_analysis/transport_archive.py',
 'experiments/global_day_20261104_analysis/reconstruct_transport.py',
 'docs/RPCCR_EXACT_ACCELERATION_V801_V802_ANALYSIS.md',
 'docs/RPCCR_EXACT_REJECTION_GLOBAL_V802_REPORT.md',
 'RPCCR_EXACT_ACCELERATION_AUTHORIZATION_20261104.json',
 'RPCCR_EXACT_ACCELERATION_LEDGER_20261104.json',
 'CURRENT_EXPERIMENT.json','AGENTS.md','RESEARCH_STATUS.md',
 'runs/v802_exact_rejection_global/FINALIZED.json',
 'runs/v802_exact_rejection_global/FINAL_INDEPENDENT_AUDIT.json',
 'runs/v802_exact_rejection_global/CLOSURE_HANDOFF.md',
 'runs/v802_exact_rejection_global/REVIEW_PENDING.before',
 'runs/v801_acceleration_initial_scan.json','runs/v801_qualification.console','runs/v801_audit.console',
 'runs/v802_preparation_review.json','runs/v802_adapter_check.console',
 'runs/v802_driver.console','runs/v802_finalize.console','runs/v802_saved_comparison.console',
 'runs/v802_diagnosis.console','runs/v802_pointwise_supplement.console','runs/v802_transport.console',
 'runs/v802_compact_monitor.jsonl','runs/v802_final_verification.json',
 'evidence/rpccr_exact_rejection_global_v802_20261104_transport/TRANSPORT_MANIFEST.json',
]:files.add(repo/name)
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
(repo / 'runs/v802_supplement_archive_result.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
