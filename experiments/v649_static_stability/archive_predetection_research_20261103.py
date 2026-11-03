"""Closed-stage snapshots only; never touch the running V721 task evidence."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];dest=repo/'evidence/rpccr_predetection_research_v714_v720_20261103'
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text())
names=['v714_observed_free_certificate','v715_submaximum_free_certificate','v716_observation_ambiguity','v717_temporal_free_viability','v718_recursive_unseen_reachability','v720_first_intervention_entry']
for name in names:assert read(repo/'runs'/name/'COMPLETION.json')['round_closed']
assert read(repo/'runs/v719_ENTRY_FAILURE_CLOSED.json')['private_prediction_integrations']==0
if (dest/'MANIFEST.json').exists():
 for row in read(dest/'MANIFEST.json'):assert sha((dest/row['path']).read_bytes())==row['sha256']
 print('EXISTING_ARCHIVE_VERIFIED');raise SystemExit(0)
dest.mkdir();blobs=dest/'blobs';blobs.mkdir();paths=[]
for name in names:
 paths.extend(p for p in (repo/'runs'/name).rglob('*')if p.is_file()and p.suffix not in ['.lock','.pyc'])
for name in ['v721_saved_renewal_validation','v721_saved_renewal_validation02','v721_saved_renewal_validation03']:
 paths.extend(p for p in (repo/'runs'/name).rglob('*')if p.is_file())
for name in ['runs/v719_ENTRY_FAILURE_CLOSED.json','runs/v719_probe.console','runs/v720_probe.console','runs/v721_saved_renewal_DIAGNOSIS.json','docs/RPCCR_PREDETECTION_RENEWAL_20261103.md']:
 paths.append(repo/name)
inventory=[]
for p in sorted(set(paths)):
 raw=p.read_bytes();h=sha(raw);blob=blobs/(h+'.gz')
 if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
(dest/'README.md').write_text('# 首次发现前时序空域续证研究\n\n保存V714/V715不足、V716有限家族无反例、V717节点用尽和全未判定状态、V718早checkpoint改善/末checkpoint不足、V719模型读取前导入失败、V720固定原生控制验证以及V721启动前全部零积分入口失败和最终校准。V720积分单列512重放/984私有/984状态验证，0导航；其他阶段全部0初始化积分。原始证据保留，不把闭批归档叫动态验收通过。报告../../docs/RPCCR_PREDETECTION_RENEWAL_20261103.md。\n')
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
 raw=gzip.decompress((dest/row['blob']).read_bytes());assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(status='ALL_ARCHIVED_BYTES_VERIFIED',raw_files=len(inventory),manifest_files=len(manifest),stored_bytes=sum(x['bytes']for x in manifest),raw_deleted=False,new_integrations=0)))
