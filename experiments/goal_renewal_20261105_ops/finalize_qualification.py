"""Read-only physical evidence closure and lossless archive; no model imports."""
import gzip,hashlib,importlib.abc,json,os,subprocess,sys
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('FINALIZATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v825_goal_renewal_native_entry';root=repo/'runs/v825_goal_renewal_native_entry';day=repo/'runs/goal_renewal_20261105'
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
assert not(root/'FINALIZED.json').exists(),'EXISTING_FINALIZED_READ_ONLY'
assert read(root/'ROUND_WINDOW.json')['round_closed'] and read(day/'V825_DRIVER_COMPLETION.json')['guard_restored']
assert (repo/'REVIEW_PENDING').read_bytes()==(day/'V825_REVIEW_PENDING.before').read_bytes()
completion=read(root/'COMPLETION.json');result=read(root/'RESULT.json');audit=read(root/'FINAL_INDEPENDENT_AUDIT.json')
assert completion['status']=='GOAL_REFERENCE_COMPONENTS_EVALUATED'and audit['status']=='SAVED_REFERENCE_COMPONENT_EVIDENCE_PASS'
assert completion['counts']==result['counts']==audit['counts']
freeze=read(own/'INPUT_FREEZE.json')['files'];assert all(sha(repo/p)==h for p,h in freeze.items())
assert read(day/'V824_ZERO_MODEL_ERROR_DIAGNOSIS.json')['status']=='OUTER_STEP_ONLY_ZERO_MODEL_MISMATCH_PROVEN'
passed=bool(audit['primary282_native_qualified']);status='GOAL_REFERENCE_NATIVE_QUALIFICATION_PASSED'if passed else'PRIMARY282_FUNCTIONAL_QUALIFICATION_NOT_PASSED'
report=repo/'docs/RPCCR_GOAL_RENEWAL_QUALIFICATION_V825_REPORT.md'
lines=['# V824/V825：目标参考更新的固定原生资格实际报告','',
 f'实际结论：{status}。两检查点为同一已观察南北任务的保存状态，不是两独立导航任务，也不是新24动态验收。',
 '',f'实际分账：{json.dumps(audit["counts"],ensure_ascii=False)}。模型内部构造数未单独计数，不填0；V824原失败经独立零模型定位确认模型/积分0，原private=null保留、另记解析为0。',
 f'最低原生实际净空{audit["minimum_actual_clearance_m"]:.12f}m，坏接触0，完整预测/实际/重复最大状态控制误差{audit["maximum_native_state_ctrl_error"]}；原始501测距包及两原因果状态精确，329/657与声明norm覆盖{audit["actual_and_repeat_329_657_coverage_samples"]}样本。','',
 '| 检查点 | 联合控制资格 | 首8原生目标进展m | 完整328目标进展m | 完整重复误差 |','|---|---|---:|---:|---:|']
for row in result['records']:
 lines.append(f'| {row["step"]} | {row["qualified"]} | {row.get("prefix8_target_progress_m")} | {row.get("complete328_target_progress_m")} | {row.get("full_integration_repeat_error")} |')
lines += ['', '两状态原旧参考各25名义240预测重新计算与保存姿态误差0，命令/评分吻合；新完整参考仍经过原名义选择、原排序联合准入及原BRAKE_ONLY完整328安全尾。正首8进展和完整尾小进展不是持续跟踪或全局到达证明。',
 '', '准备及接口异常永久保留：冻结前helper误用构造max_wheel_speed24而Phase14实际48，0模型接口核对失败日志/源保留后按冻结运行时源码规范；V824原冻结入口误比较日志外层step，在首模型前停止，旧源码/ERROR/COMPLETION不改。V825是一次明确登记的元数据入口例外，只分离外层step，501包/两内部状态全精确，完全同V824原started/deadline和物理额度，不重计1200秒。再次异常不再入口修补。',
 '', '原run_static.pose使用float64物理根姿态，V823 renewal_probe原查询对应实际规划接口；public_pose_check是float32传感位置的附加精度对照。V823两种精度下均能生成完整几何参考，此处采用原实际根姿态路径，不把传感精度对照称原调用。',
 '', '所有旧V821失败、V822未执行和各原截止保持。只覆盖公开欧氏速.08课程，发现前静态反应式条件仍较弱；不宣称原每轴.12类、任意遮挡、多actor、实时或RAS优势。训练/SAC/Stage/实机0，current/runtime/模型/冻结网络未改。',
 '', '下一步在本GOAL_RENEWAL根截止内，另立单一观测触发的完整目标参考更新候选，原南北一t0/一主+成功条件完整重复；必须先冻结其新代码及全部审核。本资格不授权新24、三路线表、其他地图或新训练。']
report.write_text('\n'.join(lines)+'\n')
archive=repo/'evidence/rpccr_goal_renewal_native_qualification_20261105';assert not archive.exists();archive.mkdir();(archive/'blobs').mkdir()
old_archive=repo/'evidence/rpccr_v821_norm_route_development_20261105'
old_inventory=read(old_archive/'MANIFEST.json')
old_blobs={x['path']:x for x in old_inventory if x['path'].startswith('blobs/')}
files={repo/p for p in freeze};files.add(own/'INPUT_FREEZE.json');files.add(report)
for directory in [root,repo/'runs/v824_goal_renewal_qualification',day,Path(__file__).parent]:
 files.update(p for p in directory.rglob('*')if p.is_file()and p.suffix not in['.lock','.pyc']and '__pycache__'not in p.parts and p.name not in['v825_finalize.console','LEDGER.json','HANDOFF.md'])
inventory=[]
for p in sorted(files):
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();encoding='identity'if p.suffix=='.gz'else'gzip';relative='blobs/'+h+('.raw'if encoding=='identity'else'.gz');blob=archive/relative
 if not blob.exists():
  if relative in old_blobs:os.link(old_archive/relative,blob)
  else:blob.write_bytes(raw if encoding=='identity'else gzip.compress(raw,mtime=0))
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=relative,encoding=encoding))
(archive/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0));verified={}
for item in inventory:
 if item['blob']not in verified:
  raw=(archive/item['blob']).read_bytes();raw=raw if item['encoding']=='identity'else gzip.decompress(raw);verified[item['blob']]=(len(raw),hashlib.sha256(raw).hexdigest())
 assert verified[item['blob']]==(item['bytes'],item['sha256'])and sha(repo/item['path'])==item['sha256']
manifest=[dict(path=str(p.relative_to(archive)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(archive.rglob('*'))if p.is_file()];dump(archive/'MANIFEST.json',manifest)
assert all(sha(archive/x['path'])==x['sha256']for x in manifest)
transport=None
if any(x['bytes']>90*1024**2 for x in manifest):
 transport=str(archive.relative_to(repo))+'_transport'
 process=subprocess.run([sys.executable,'-B',str(repo/'experiments/global_day_20261104_analysis/transport_archive.py'),str(archive),str(repo/transport)],cwd=repo,capture_output=True,text=True,timeout=605)
 (root/'transport.console').write_text(process.stdout+process.stderr);assert process.returncode==0,'LOSSLESS_TRANSPORT_FAILED'
final=dict(status=status,primary282_native_qualified=passed,source_and_decompressed_sha_verified=True,raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),archive=str(archive.relative_to(repo)),transport=transport,report=str(report.relative_to(repo)),counts=audit['counts'],new_models_finalizer=0,new_integrations_finalizer=0,new_navigation=0,full_dynamic_acceptance_passed=False)
dump(root/'FINALIZED.json',final);ledger=read(day/'LEDGER.json');ledger.update(status='V825_QUALIFICATION_FINALIZED',qualification_passed=passed,qualification_finalized=str((root/'FINALIZED.json').relative_to(repo)),qualification_counts=audit['counts'],active_simulation=False);dump(day/'LEDGER.json',ledger)
print(json.dumps(final),flush=True)
