"""Archive closed raw evidence once, then decompress and hash every byte."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
root=repo/'evidence/rpccr_coupled_progress_v749_v752_20261103';root.mkdir(exist_ok=False);(root/'blobs').mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
paths=[]
for name in ['runs/v749_coupled_observation_progress','runs/v751_coupled_packet_schema_diagnosis','runs/v752_coupled_fixture_rehearsal','experiments/v749_coupled_observation_progress','experiments/v750_coupled_progress_audit','experiments/v751_coupled_packet_schema_diagnosis','experiments/v752_coupled_repair_preparation']:
 paths.extend(p for p in(repo/name).rglob('*')if p.is_file()and '__pycache__'not in str(p))
paths.extend(repo/n for n in ['runs/v749_launch.json','runs/v749_review_guard.before','runs/v749_probe.console','runs/v751_diagnosis.console','runs/v752_rehearsal.console','RPCCR_COUPLED_PROGRESS_AUTHORIZATION_20261103.json'])
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
(root/'README.md').write_text('# V749–V752校准异常与修复证据\n\n完整保留V749 STOPPED_EXCEPTION、264旧重放/328私有校准预测、新三个条件未执行；V751精确原始/派生模式复核与4071负例、V752全41旧帧离线修复预演。修复只在无物理入口的文本副本，原冻结源/失败/截止不改。全部RAW_INVENTORY条目逐字节解压回读，原始runs保留。\n')
manifest=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(root.rglob('*'))if p.is_file()]
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha((root/row['path']).read_bytes())==row['sha256']
result=dict(raw_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),manifest_entries=len(manifest),all_decompressed_and_source_readback_verified=True,archive=str(root.relative_to(repo)),raw_evidence_retained=True,new_integrations=0)
(repo/'runs/v752_archive_readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
