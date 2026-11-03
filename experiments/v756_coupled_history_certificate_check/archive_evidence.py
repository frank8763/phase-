"""Archive closed raw evidence once, then decompress and hash every byte."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
root=repo/'evidence/rpccr_coupled_progress_v753_v756_20261103';root.mkdir(exist_ok=False);(root/'blobs').mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
paths=[]
for name in ['runs/v753_coupled_progress_repaired','runs/v753_prelaunch_compatibility','runs/v754_coupled_progress_repaired_audit','runs/v755_coupled_failure_attribution','runs/v756_coupled_history_certificate_check','experiments/v753_coupled_progress_repaired','experiments/v754_coupled_progress_repaired_audit','experiments/v755_coupled_failure_attribution','experiments/v756_coupled_history_certificate_check']:
 paths.extend(p for p in(repo/name).rglob('*')if p.is_file()and '__pycache__'not in str(p))
paths.extend(repo/n for n in ['runs/v753_launch.json','runs/v753_review_guard.before','runs/v753_probe.console','runs/v753_prelaunch.console','runs/v754_audit.console','runs/v755_attribution.console','runs/v756_history.console','RPCCR_COUPLED_REPAIR_AUTHORIZATION_20261103.json'])
inventory=[]
for p in sorted(set(paths)):
 data=p.read_bytes();digest=sha(data);compressed=gzip.compress(data,compresslevel=6,mtime=0);use_gzip=len(compressed)<len(data);payload=compressed if use_gzip else data;rel='blobs/'+digest+('.gz'if use_gzip else'.raw');out=root/rel
 if out.exists():assert out.read_bytes()==payload
 else:out.write_bytes(payload)
 decoded=gzip.decompress(out.read_bytes())if use_gzip else out.read_bytes();assert decoded==data
 inventory.append(dict(source=str(p.relative_to(repo)),bytes=len(data),sha256=digest,archive=rel,archive_sha256=sha(payload),encoding='gzip'if use_gzip else'raw'))
index=root/'RAW_INVENTORY.json.gz';index.write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),compresslevel=6,mtime=0))
back=json.loads(gzip.decompress(index.read_bytes()));assert back==inventory
for row in back:
 payload=(root/row['archive']).read_bytes();assert sha(payload)==row['archive_sha256'];data=gzip.decompress(payload)if row['encoding']=='gzip'else payload
 assert len(data)==row['bytes']and sha(data)==row['sha256']and(repo/row['source']).read_bytes()==data
(root/'README.md').write_text('# V753–V756完整原始证据\n\nV753物理校准通过，原三固定组件条件全部实际执行但资格0/3，旧安全尾完整停稳；V754独立保存审核通过。V755静态/未知域归因、V756既有历史距离证书及直接全历史核验均零新增物理。完整RAW_INVENTORY逐字节解压回读，原始runs保留，旧V749失败/全部截止保持。\n')
manifest=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(root.rglob('*'))if p.is_file()]
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha((root/row['path']).read_bytes())==row['sha256']
result=dict(raw_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),manifest_entries=len(manifest),all_decompressed_and_source_readback_verified=True,archive=str(root.relative_to(repo)),raw_evidence_retained=True,new_integrations=0)
(repo/'runs/v756_archive_readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
