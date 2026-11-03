"""Supplemental immutable diagnosis, separate from the original V721 failure archive."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];dest=repo/'evidence/rpccr_renewal_pilot_diagnosis_v721_20261103';read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert read(repo/'RPCCR_RECURSIVE_UNSEEN_CLOSED_20261103.json')['no_more_simulation_in_this_window']
if (dest/'MANIFEST.json').exists():
 for row in read(dest/'MANIFEST.json'):assert sha((dest/row['path']).read_bytes())==row['sha256']
 print('EXISTING_ARCHIVE_VERIFIED');raise SystemExit(0)
dest.mkdir();blobs=dest/'blobs';blobs.mkdir();paths=[p for p in(repo/'runs/v722_renewal_navigation_diagnosis').rglob('*')if p.is_file()and'mplconfig'not in p.parts]
paths.extend(repo/name for name in ['RPCCR_RECURSIVE_UNSEEN_CLOSED_20261103.json','docs/RPCCR_RENEWAL_PILOT_V721_ANALYSIS.md','runs/v721_recursive_unseen_navigation/AUTOMATION_STOPPED.json'])
inventory=[]
for p in sorted(set(paths)):
 raw=p.read_bytes();h=sha(raw);blob=blobs/(h+'.gz')
 if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
(dest/'README.md').write_text('# V721时序续证主任务未到达：补充零积分诊断\n\n保存同初态/模型/phase版本比较、首分叉44、最大位移.966154→1.452516m与两个反向尾，以及未发现时证书耗尽位置。原V721完整功能失败/原归档不改，1392导航/1392重放/724680私有精确；V722新增积分0。原始runs保留，不将局部进展叫验收通过。报告../../docs/RPCCR_RENEWAL_PILOT_V721_ANALYSIS.md。\n')
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(dest.rglob('*'))if p.is_file()];(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
 raw=gzip.decompress((dest/row['blob']).read_bytes());assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(status='ALL_ARCHIVED_BYTES_VERIFIED',raw_files=len(inventory),manifest_files=len(manifest),stored_bytes=sum(x['bytes']for x in manifest),raw_deleted=False,new_integrations=0)))
