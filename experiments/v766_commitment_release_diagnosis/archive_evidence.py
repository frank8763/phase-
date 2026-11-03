"""Archive closed raw evidence once, then decompress and hash every byte."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
root=repo/'evidence/rpccr_observation_commitment_v762_v768_20261103';root.mkdir(exist_ok=False);(root/'blobs').mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
paths=[]
for name in ['runs/v762_observation_commitment', 'runs/v762_prelaunch', 'runs/v762_selection_prelaunch', 'runs/v763_observation_commitment_audit', 'runs/v764_observation_progress_cycle', 'runs/v764_prelaunch', 'runs/v764_selection_prelaunch', 'runs/v765_observation_progress_cycle_audit', 'runs/v766_commitment_release_diagnosis', 'runs/v767_certified_progress_release', 'runs/v767_prelaunch', 'runs/v767_selection_prelaunch', 'runs/v768_certified_progress_release_audit', 'experiments/v762_observation_commitment', 'experiments/v763_observation_commitment_audit', 'experiments/v764_observation_progress_cycle', 'experiments/v765_observation_progress_cycle_audit', 'experiments/v766_commitment_release_diagnosis', 'experiments/v767_certified_progress_release', 'experiments/v768_certified_progress_release_audit']:
 paths.extend(p for p in(repo/name).rglob('*')if p.is_file()and '__pycache__'not in str(p))
paths.extend(repo/n for n in ['RPCCR_OBSERVATION_COMMITMENT_AUTHORIZATION_20261103.json', 'RPCCR_OBSERVATION_CYCLE_AUTHORIZATION_20261103.json', 'RPCCR_CERTIFIED_RELEASE_AUTHORIZATION_20261103.json', 'RPCCR_OBSERVATION_ROUND_CLOSED_20261103.json', 'docs/RPCCR_OBSERVATION_COMMITMENT_V762_V768_REPORT.md', 'runs/v766_final_attribution.console', 'runs/v767_selection_preparation_failure.json', 'runs/v762_launch.json', 'runs/v762_review_guard.before', 'runs/v762_probe.console', 'runs/v764_launch.json', 'runs/v764_review_guard.before', 'runs/v764_probe.console', 'runs/v767_launch.json', 'runs/v767_review_guard.before', 'runs/v767_probe.console', 'runs/v763_audit.console', 'runs/v765_audit.console', 'runs/v768_audit.console'])
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
(root/'README.md').write_text('# V762–V768提前观察承诺全证据\n\nV762有限96主动组件主/完整重复及独立审核通过；V764与V767长周期未通过，原失败/窗口保持。V767两次真实解除观察，但首次解除后仅.091m进展未达1m。全部原生/传感/源模型/因果/接触/全状态独立证据通过；组件不等于完整动态验收。1752旧重放/527424私有/4544新实际/568新包，逐字节来源/解压哈希回读，原始runs保留。详见docs/RPCCR_OBSERVATION_COMMITMENT_V762_V768_REPORT.md。\n')
manifest=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(root.rglob('*'))if p.is_file()]
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha((root/row['path']).read_bytes())==row['sha256']
result=dict(raw_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),manifest_entries=len(manifest),all_decompressed_and_source_readback_verified=True,archive=str(root.relative_to(repo)),raw_evidence_retained=True,new_integrations=0)
(repo/'runs/v768_archive_readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
