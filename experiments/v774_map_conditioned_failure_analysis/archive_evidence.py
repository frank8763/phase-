"""Archive closed raw evidence once, then decompress and hash every byte."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
root=repo/'evidence/rpccr_map_conditioned_v769_v777_20261103';root.mkdir(exist_ok=False);(root/'blobs').mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
paths=[]
for name in ['runs/v769_geometry_reachability_qualification', 'runs/v771_geometry_audit_environment_recovery', 'runs/v772_prelaunch', 'runs/v772_domain_prelaunch', 'runs/v772_map_conditioned_progress', 'runs/v773_map_conditioned_progress_audit', 'runs/v774_map_conditioned_failure_analysis', 'runs/v774_tail_interface_recovery', 'runs/v775_map_history_envelope_check', 'experiments/v769_geometry_reachability_qualification', 'experiments/v770_geometry_reachability_audit', 'experiments/v771_geometry_audit_environment_recovery', 'experiments/v772_map_conditioned_progress', 'experiments/v773_map_conditioned_progress_audit', 'experiments/v774_map_conditioned_failure_analysis', 'experiments/v775_map_history_envelope_check', 'experiments/v776_retained_tail_reentry_qualification', 'experiments/v777_retained_tail_reentry_audit', 'runs/v776_retained_tail_reentry_qualification', 'runs/v777_retained_tail_reentry_audit']:
 paths.extend(p for p in(repo/name).rglob('*')if p.is_file()and '__pycache__'not in str(p))
paths.extend(repo/n for n in ['RPCCR_GEOMETRY_REACHABILITY_AUTHORIZATION_20261103.json', 'RPCCR_MAP_CONDITIONED_PROGRESS_AUTHORIZATION_20261103.json', 'RPCCR_MAP_CONDITIONED_CLOSED_20261103.json', 'docs/RPCCR_MAP_CONDITIONED_V769_V777_REPORT.md', 'runs/v770_import_failure.json', 'runs/v774_tail_interface_failure.json', 'runs/v772_launch.json', 'runs/v772_review_guard.before', 'runs/v772_probe.console', 'runs/v769_qualification.console', 'runs/v770_audit.console', 'runs/v771_audit.console', 'runs/v772_domain_prelaunch.console', 'runs/v773_audit.console', 'runs/v774_analysis.console', 'runs/v774_tail.console', 'runs/v774_tail_repaired.console', 'runs/v775_history.console', 'RPCCR_TAIL_REENTRY_QUALIFICATION_AUTHORIZATION_20261103.json', 'runs/v776_launch.json', 'runs/v776_review_guard.before', 'runs/v776_probe.console', 'runs/v777_audit.console', 'runs/v771_audit_dependencies/INSTALL.console', 'runs/v771_audit_dependencies/INSTALL_RESULT.json', 'runs/v771_audit_dependencies/PIP_REPORT.json', 'runs/v771_audit_dependencies/INSTALLED_FILES.json', 'runs/v771_audit_dependencies/SCIPY_INSTALLED.zip'])
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
(root/'README.md').write_text('# V769–V777地图条件可达集合与实际未通过全证据\n\n固定状态几何资格与独立集合审核通过；V770缺依赖导入失败及V774尾部接口失败保留。V771仅runs私有SciPy恢复独立审计，共享环境未改；SCIPY_INSTALLED.zip及INSTALLED_FILES可恢复所有私有依赖字节。V772固定两版本均持续推进FAIL，重复未执行，V773完整实际保存审计通过；584旧重放/275848私有/2320新原生/290新包。V774原射线/末次/尾部、V775持久历史均零积分；V776原尾固定3状态资格有重新可证动作，但未实际新接管，V777独立审核。明确不穿透已知静态体是额外条件运动类；完整场地动态仍未通过。所有RAW_INVENTORY来源逐字节解压哈希回读，原始runs不删。报告docs/RPCCR_MAP_CONDITIONED_V769_V777_REPORT.md。\n')
manifest=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(root.rglob('*'))if p.is_file()]
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha((root/row['path']).read_bytes())==row['sha256']
result=dict(raw_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),manifest_entries=len(manifest),all_decompressed_and_source_readback_verified=True,archive=str(root.relative_to(repo)),raw_evidence_retained=True,new_integrations=0)
(repo/'runs/v775_archive_readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
