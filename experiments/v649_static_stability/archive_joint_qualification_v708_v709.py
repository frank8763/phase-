"""Zero-integration content-addressed snapshot; never remove original evidence."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];dest=repo/'evidence/rpccr_joint_geometry_v708_v709_20261103'
read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
roots=[repo/'runs/v708_joint_field_qualification',repo/'runs/v709_joint_reference_certificate']
for root in roots:assert read(root/'COMPLETION.json')['round_closed']
if (dest/'MANIFEST.json').exists():
 for row in read(dest/'MANIFEST.json'):assert sha((dest/row['path']).read_bytes())==row['sha256']
 print('EXISTING_ARCHIVE_VERIFIED');raise SystemExit(0)
dest.mkdir(exist_ok=False);blobs=dest/'blobs';blobs.mkdir();inventory=[]
for root in roots:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or p.suffix=='.lock':continue
  raw=p.read_bytes();h=sha(raw);blob=blobs/(h+'.gz')
  if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
  inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
(dest/'README.md').write_text('# RP-CCR完整场地联合几何资格\n\nV708两路线通过、南北未通过；V709在明确修改南北附近观测课程条件并补齐连续参考证书后，三路线独立标量几何审计通过。零MuJoCo初始化/积分/训练。不是动态导航或独立确认；保留全部拒绝候选和原始runs。报告../../docs/RPCCR_JOINT_GEOMETRY_V708_V709_REPORT.md。\n')
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
 raw=gzip.decompress((dest/row['blob']).read_bytes());assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(status='ALL_ARCHIVED_BYTES_VERIFIED',raw_files=len(inventory),manifest_files=len(manifest),stored_bytes=sum(x['bytes'] for x in manifest),deleted=False,verification_integrations=0)))
