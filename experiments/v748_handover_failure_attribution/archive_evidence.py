"""Archive closed raw evidence once, then decompress and hash every byte."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
root=repo/'evidence/rpccr_early_handover_v746_v748_20261103';root.mkdir(exist_ok=False);(root/'blobs').mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
paths=[]
for name in ['runs/v746_early_observation_handover','runs/v747_early_handover_audit','runs/v748_handover_failure_attribution','experiments/v746_early_observation_handover','experiments/v747_early_handover_audit','experiments/v748_handover_failure_attribution']:
 paths.extend(p for p in(repo/name).rglob('*')if p.is_file()and '__pycache__'not in str(p))
paths.extend(repo/n for n in ['runs/v746_launch.json','runs/v746_review_guard.before','runs/v746_probe.console','runs/v747_audit.console','runs/v748_attribution.console','RPCCR_EARLY_HANDOVER_AUTHORIZATION_20261103.json'])
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
(root/'README.md').write_text('# V746–V748完整原始证据\n\nRAW_INVENTORY.json.gz记录源路径、原始字节SHA和归档编码；所有条目已逐字节解压回读。原始runs未删除。旧模型、V735/V740来源和依赖由各INPUT_FREEZE及既有远端归档引用，原失败/截止保持。0完整导航/确认样本；组件资格false。\n')
manifest=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(root.rglob('*'))if p.is_file()]
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha((root/row['path']).read_bytes())==row['sha256']
result=dict(raw_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),manifest_entries=len(manifest),all_decompressed_and_source_readback_verified=True,archive=str(root.relative_to(repo)),raw_evidence_retained=True,new_integrations=0)
(repo/'runs/v748_archive_readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
