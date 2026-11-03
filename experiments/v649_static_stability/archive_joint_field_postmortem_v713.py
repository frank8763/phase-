"""Freeze supplemental diagnosis, without changing original finalized archives."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];dest=repo/'evidence/rpccr_joint_field_diagnosis_v713_20261103'
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text())
assert read(repo/'RPCCR_JOINT_FIELD_CLOSED_20261103.json')['automatic_additional_simulation'] is False
if (dest/'MANIFEST.json').exists():
 for row in read(dest/'MANIFEST.json'):assert sha((dest/row['path']).read_bytes())==row['sha256']
 print('EXISTING_ARCHIVE_VERIFIED');raise SystemExit(0)
dest.mkdir();blobs=dest/'blobs';blobs.mkdir();sources=[]
for name in ['runs/v711_field_audit_entry','runs/v713_unseen_frontier_diagnosis','runs/joint_geometry_review_20261103']:
 sources.extend(p for p in (repo/name).rglob('*') if p.is_file() and 'mplconfig'not in p.parts)
for name in ['RPCCR_JOINT_FIELD_CLOSED_20261103.json','docs/RPCCR_JOINT_FIELD_20261103_REPORT.md','docs/RPCCR_JOINT_GEOMETRY_V708_V709_REPORT.md','docs/RPCCR_FIELD_AUDIT_ENTRY_V711_REPORT.md','runs/v710_prelaunch_source_check.json','runs/v712_joint_field_continuation/HANDOFF.md','runs/v712_joint_field_continuation/AUTOMATION_STOPPED.json']:
 sources.append(repo/name)
inventory=[]
for p in sorted(set(sources)):
 raw=p.read_bytes();h=sha(raw);blob=blobs/(h+'.gz')
 if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
(dest/'README.md').write_text('# 联合场地首导航失败后的零积分诊断\n\n三路线几何与真实t0资格已过，首导航未发现actor、145公开步未到达。保存全部146原始包因果复核、未更新初始排除盘的证书时间界、32规划元数据一致性与3尾几何重算。原V710/V712失败与原审核及归档不改，不把补充核验称验收通过。导航1160/重放1160/私有529144，诊断新增积分0，24确认未执行。报告../../docs/RPCCR_JOINT_FIELD_20261103_REPORT.md；原始runs全部保留。\n')
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
 raw=gzip.decompress((dest/row['blob']).read_bytes());assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(status='ALL_ARCHIVED_BYTES_VERIFIED',raw_files=len(inventory),manifest_files=len(manifest),stored_bytes=sum(x['bytes']for x in manifest),deleted=False,verification_integrations=0)))
