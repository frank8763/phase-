"""Archive closed raw evidence once, then decompress and hash every byte."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
root=repo/'evidence/rpccr_state_feedback_v757_v761_20261103';root.mkdir(exist_ok=False);(root/'blobs').mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
paths=[]
for name in ['runs/v757_state_feedback_qualification','runs/v758_state_feedback_audit','runs/v759_prelaunch','runs/v759_state_feedback_execution','runs/v760_state_feedback_execution_audit','runs/v761_feedback_failure_diagnosis','experiments/v757_state_feedback_qualification','experiments/v758_state_feedback_audit','experiments/v759_state_feedback_execution','experiments/v760_state_feedback_execution_audit','experiments/v761_feedback_failure_diagnosis']:
 paths.extend(p for p in(repo/name).rglob('*')if p.is_file()and '__pycache__'not in str(p))
paths.extend(repo/n for n in ['runs/v757_launch.json','runs/v757_review_guard.before','runs/v757_probe.console','runs/v758_audit.console','runs/v759_launch.json','runs/v759_review_guard.before','runs/v759_probe.console','runs/v760_audit.console','runs/v761_diagnosis.console','runs/v761_tail_observation.console','RPCCR_STATE_FEEDBACK_AUTHORIZATION_20261103.json','RPCCR_STATE_FEEDBACK_EXECUTION_AUTHORIZATION_20261103.json','RPCCR_STATE_FEEDBACK_CLOSED_20261103.json','docs/RPCCR_STATE_FEEDBACK_V759_REPORT.md'])
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
(root/'README.md').write_text('# V757–V761完整原始证据\n\n三原受阻状态固定15动作存在合格替代，但V759状态反馈仍未完成96主动步资格；完整旧尾安全停稳，V758/V760独立保存证据通过。V761归因与尾部几何参考零积分。1768旧重放/84952私有/712新实际/89新包，全部来源逐字节回读，原失败/截止不改、原始runs保留。详见docs/RPCCR_STATE_FEEDBACK_V759_REPORT.md。\n')
manifest=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(root.rglob('*'))if p.is_file()]
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha((root/row['path']).read_bytes())==row['sha256']
result=dict(raw_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),manifest_entries=len(manifest),all_decompressed_and_source_readback_verified=True,archive=str(root.relative_to(repo)),raw_evidence_retained=True,new_integrations=0)
(repo/'runs/v761_archive_readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
