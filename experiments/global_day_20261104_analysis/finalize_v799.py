"""Zero-model immutable fixed-state qualification closure and source readback."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v799_spatial_nominal_qualification';root=repo/'runs/v799_spatial_nominal_qualification'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert(repo/'REVIEW_PENDING').exists()and not(root/'FINALIZED.json').exists()
assert read(root/'ROUND_WINDOW.json')['round_closed']
freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
r=read(root/'RESULT.json');audit_path=repo/'runs/v799_spatial_nominal_saved_audit/RESULT.json'
audit=read(audit_path)if audit_path.exists()else None
passed=bool(r['qualification_passed']and audit and audit['status']=='ALL_FIXED_SPATIAL_PREFIX_EVIDENCE_VERIFIED'and audit['qualification_passed'])
result=dict(status='FIXED_SPATIAL_PREFIX_QUALIFICATION_VERIFIED'if passed else'FIXED_SPATIAL_PREFIX_NOT_PASSED',
    qualification_passed=passed,evidence_verified=bool(audit and audit['status']=='ALL_FIXED_SPATIAL_PREFIX_EVIDENCE_VERIFIED'),
    source_unchanged=True,original_replay_native=r['original_replay_steps'],private_native=r['private_integrations'],
    physical_validation_native=r['scene_validation_integrations'],physical_repeat_native=r['scene_repeat_integrations'],
    witnesses=r['physically_verified_positive_witnesses'],full_global_dynamic_passed=False,new_navigation_samples=0,new_confirmation_samples=0,
    finalizer_models=0,finalizer_integrations=0,raw_deleted=False)
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
report=repo/'docs/RPCCR_SPATIAL_PREFIX_V799_REPORT.md';assert not report.exists()
report.write_text('\n'.join(['# V799 名义提案与短前缀完整后备联合资格','',f'独立结论：**{result["status"]}**，不是全局导航成功。',
    '', '固定V793原404/541/617三个失败状态，各25原提案，全部75保留。原240预测因果净空/自体/末速度精确复现；额外资格采用同一当前因果域、实际8原生前缀加原320完整后备，无未来假测量。',
    '',f'旧重放{r["original_replay_steps"]}/私有{r["private_integrations"]}/实际分支{r["scene_validation_integrations"]}/完整重复{r["scene_repeat_integrations"]}原生。误差：旧重放{r["maximum_replay_error"]}、实际{r["maximum_validation_error"]}；最低实际净空{r["minimum_actual_native_clearance_m"]}m、坏接触{r["bad_contacts"]}。',
    '',f'正首前缀+完整后备+实际重复见证：{r["physically_verified_positive_witnesses"]}。首8原生仅约毫米进展，不能称整328尾都向前；其余状态没有合格正前缀见证。',
    '', '解释：名义240未来全轨迹的动态拒绝不等价于实际短前缀+原完整后备无解。支持分离“名义空间提案”和“实际前缀+完整因果安全尾”的单候选检验，但不证明可持续进展、中央通行、实际动态发现/到达、递归安全或RAS增量。',
    '', '只有本资格全部独立审核和归档来源/解压SHA回读通过后，才可依赖另立冻结V800原三路线全局开发；保留全部原安全门、地图、actor、传感、物理控制、冻结网络及原失败。训练/SAC/Stage/实机0。'])+'\n')
dest=repo/'evidence/rpccr_spatial_prefix_v799_20261104';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir()
files={p for d in [own,root,repo/'runs/v799_spatial_nominal_saved_audit',repo/'runs/v799_preparation',repo/'runs/v799_preparation_errors']for p in d.rglob('*')if p.is_file()and'__pycache__'not in p.parts}
for name in ['RPCCR_SPATIAL_NOMINAL_AUTHORIZATION_20261104.json','runs/v799_driver.console','runs/v799_probe.console','runs/v799_saved_audit.console','runs/v799_launch.json','runs/v799_driver_launch.json','runs/v799_review_guard.before','runs/v799_fixture_qualification.console','runs/v799_fixture_qualification_attempt02.console','runs/v799_fixture_qualification_attempt03.console']:
    files.add(repo/name)
files|={report,Path(__file__)};inventory=[]
for p in sorted(files):
    data=p.read_bytes();h=hashlib.sha256(data).hexdigest();blob=dest/'blobs'/(h+'.gz');packed=gzip.compress(data,mtime=0)
    if blob.exists():assert blob.read_bytes()==packed
    else:blob.write_bytes(packed)
    inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(data),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
    raw=gzip.decompress((dest/row['blob']).read_bytes());assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']==sha(repo/row['path'])
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');assert all(sha(dest/r['path'])==r['sha256']for r in manifest)
result['archive']=dict(path=str(dest.relative_to(repo)),source_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),all_source_and_decompressed_readback_verified=True,raw_deleted=False)
(root/'FINALIZED.json').write_text(json.dumps(result,indent=2)+'\n')
f=repo/'RPCCR_SPATIAL_NOMINAL_LEDGER_20261104.json';l=read(f);l.update(status='V799_QUALIFICATION_VERIFIED_READY_FOR_CONDITIONAL_GLOBAL'if passed else'V799_QUALIFICATION_FAILED_NO_GLOBAL_ALLOWED',v799_closure=result);f.write_text(json.dumps(l,indent=2)+'\n');print(json.dumps(result))
