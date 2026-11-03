"""Archive this closed study without changing or deleting earlier evidence."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];out=repo/'evidence/rpccr_preemptive_observation_v740_v745_20261103';out.mkdir(exist_ok=False);(out/'blobs').mkdir();sha=lambda b:hashlib.sha256(b).hexdigest();paths=[]
for directory in ['experiments/v740_preemptive_observation_cycles','experiments/v741_preemptive_cycles_audit','experiments/v742_persistent_clearance_envelope','experiments/v743_persistent_envelope_audit','experiments/v744_scan_confidence_eligibility','experiments/v745_observation_handover_preparation','runs/v740_preemptive_observation_cycles','runs/v741_preemptive_cycles_audit','runs/v741_preemptive_timing_analysis','runs/v742_persistent_clearance_envelope','runs/v743_persistent_envelope_audit','runs/v743_persistent_math_checks','runs/v744_scan_confidence_eligibility']:
 paths.extend(p for p in(repo/directory).rglob('*')if p.is_file()and'__pycache__'not in p.parts)
for n in ['RPCCR_PREEMPTIVE_OBSERVATION_AUTHORIZATION_20261103.json','RPCCR_PERSISTENT_CERTIFICATE_AUTHORIZATION_20261103.json','RPCCR_PREEMPTIVE_OBSERVATION_CLOSED_20261103.json','docs/RPCCR_PREEMPTIVE_OBSERVATION_V740_REPORT.md','runs/v740_launch.json','runs/v740_review_guard.before','runs/v740_probe.console','runs/v741_audit.console','runs/v741_timing.console','runs/v742_verify.console','runs/v743_audit.console','runs/v743_math.console','runs/v744_verify.console']:paths.append(repo/n)
inventory=[]
for p in sorted(set(paths)):
 data=p.read_bytes();h=sha(data);compressed=gzip.compress(data,mtime=0);encoding='gzip'if len(compressed)<len(data)else'raw';encoded=compressed if encoding=='gzip'else data;blob='blobs/'+h+('.gz'if encoding=='gzip'else'.raw');target=out/blob
 if not target.exists():target.write_bytes(encoded)
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(data),sha256=h,blob=blob,encoding=encoding))
(out/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0));manifest=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(out.rglob('*'))if p.is_file()];(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha((out/row['path']).read_bytes())==row['sha256']
for row in json.loads(gzip.decompress((out/'RAW_INVENTORY.json.gz').read_bytes())):
 data=(out/row['blob']).read_bytes();data=gzip.decompress(data)if row['encoding']=='gzip'else data;assert len(data)==row['bytes']and sha(data)==row['sha256']and sha((repo/row['path']).read_bytes())==row['sha256']
result=dict(status='ALL_PREEMPTIVE_OBSERVATION_RAW_EVIDENCE_READ_BACK',raw_files=len(inventory),manifest_files=len(manifest),manifest_sha256=sha((out/'MANIFEST.json').read_bytes()),raw_evidence_retained=True)
(repo/'runs/v745_archive_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
