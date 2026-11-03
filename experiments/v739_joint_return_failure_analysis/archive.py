"""Preserve closed diagnostic evidence and verify every archived raw byte."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];out=repo/'evidence/rpccr_joint_return_v737_v739_20261103';out.mkdir(exist_ok=False);(out/'blobs').mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();paths=[]
for directory in ['experiments/v737_joint_return_qualification','experiments/v738_joint_return_saved_audit','experiments/v739_joint_return_failure_analysis','runs/v737_joint_return_qualification','runs/v738_joint_return_saved_audit','runs/v739_joint_return_failure_analysis']:
 paths.extend(p for p in(repo/directory).rglob('*')if p.is_file()and'__pycache__'not in p.parts)
for name in ['RPCCR_JOINT_RETURN_AUTHORIZATION_20261103.json','RPCCR_JOINT_RETURN_CLOSED_20261103.json','runs/v737_launch.json','runs/v737_review_guard.before','runs/v737_probe.console','runs/v738_audit.console','runs/v739_analysis.console','docs/RPCCR_JOINT_RETURN_V737_REPORT.md','docs/RPCCR_JOINT_RETURN_RELATED_WORK_20261103.md']:
 paths.append(repo/name)
inventory=[]
for p in sorted(set(paths)):
 data=p.read_bytes();h=sha(data);compressed=gzip.compress(data,mtime=0);encoded=compressed if len(compressed)<len(data)else data;encoding='gzip'if len(compressed)<len(data)else'raw';target='blobs/'+h+('.gz'if encoding=='gzip'else'.raw');dest=out/target
 if not dest.exists():dest.write_bytes(encoded)
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(data),sha256=h,blob=target,encoding=encoding))
(out/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
manifest=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(out.rglob('*'))if p.is_file()]
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for item in manifest:assert sha((out/item['path']).read_bytes())==item['sha256']
for item in json.loads(gzip.decompress((out/'RAW_INVENTORY.json.gz').read_bytes())):
 data=(out/item['blob']).read_bytes();data=gzip.decompress(data)if item['encoding']=='gzip'else data;assert len(data)==item['bytes']and sha(data)==item['sha256']and sha((repo/item['path']).read_bytes())==item['sha256']
result=dict(status='ALL_CLOSED_JOINT_RETURN_RAW_EVIDENCE_READ_BACK',raw_files=len(inventory),manifest_files=len(manifest),manifest_sha256=sha((out/'MANIFEST.json').read_bytes()),old_evidence_retained=True)
(repo/'runs/v739_archive_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
