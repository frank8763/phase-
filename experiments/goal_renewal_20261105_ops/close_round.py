"""Close the stopped V826 round from saved evidence, without changing originals."""
import fcntl,gzip,hashlib,importlib.abc,json,zipfile
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('CLOSURE_FORBIDS_MODELS')
import sys
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2];day=repo/'runs/goal_renewal_20261105';root=repo/'runs/v826_goal_reference_renewal';supp=day/'closed_audit_supplement'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
assert not(day/'ZERO_MODEL_CLOSURE.json').exists(),'CLOSURE_ALREADY_EXISTS_NO_REPEAT'
original=read(root/'FINALIZED.json');assert original['status']=='GOAL_RENEWAL_DEVELOPMENT_NOT_PASSED'and not original['development_passed']
assert read(root/'ROUND_WINDOW.json')['round_closed']
assert(repo/'REVIEW_PENDING').read_bytes()==(root/'REVIEW_PENDING.before').read_bytes()
with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
freeze=read(repo/'experiments/v826_goal_reference_renewal/CANDIDATE_FREEZE.json')['files'];assert all(sha(repo/p)==h for p,h in freeze.items())
checks=read(supp/'INPUT_FREEZE.json')['files'];assert all(sha(repo/p)==h for p,h in checks.items())
renewal=read(supp/'evidence_view/GOAL_REFERENCE_RENEWAL_AUDIT.json');chain=read(supp/'discovery_chain/DISCOVERY_CHAIN_AUDIT_V699.json')
assert renewal['status']=='GOAL_REFERENCE_RENEWAL_INDEPENDENT_PASS'and chain['status']=='PASS'
completion=read(root/'development01/COMPLETION.json');assert len(completion['records'])==1
row=completion['records'][0];result=row['result'];assert result['outcome']=='GOAL'and result['strict_safe_arrival']
assert sum(code==0 for code in row['audits'].values())==12 and row['audits']['audit_goal_renewal.py']==1
native=read(repo/row['run']/'NATIVE_REPLAY_AUDIT.json');assert native['maximum_full_native_state_ctrl_error']==0 and native['replay_integration_steps']==4984
assert not(root/'repeat_slot02').exists(),'UNEXPECTED_REPEAT_DIRECTORY'
archive=repo/original['archive']['archive'];manifest=read(archive/'MANIFEST.json');assert all(sha(archive/x['path'])==x['sha256']for x in manifest)
transport=repo/original['archive']['transport'];assert transport.exists()
counts=dict(main_public=623,navigation_native=4984,navigation_private_native=4012696,navigation_replay_native=4984,
    qualification_old_replay_native=4000,qualification_private_native=24656,qualification_actual_native=656,qualification_repeat_native=656,
    new_main_executed=1,saved_main_complete_chain_passed=1,complete_navigation_repeats_executed=0,complete_navigation_repeats_unexecuted=1,new_confirmation=0)
closed=dict(status='CLOSED_MAIN_GOAL_SAVED_CHAIN_VERIFIED_ORIGINAL_BATCH_NOT_PASSED',original_batch_status=original['status'],original_audit_import_error_preserved=True,
    saved_supplement_status='UNCHANGED_FROZEN_AUDITS_PASS_WITH_READ_ONLY_DEPENDENCY_PATH',counts=counts,minimum_actual_clearance_m=result['minimum_dynamic_native_clearance_m'],
    obstacle_penetration_unknown_contacts=0,native_replay_max_state_ctrl_error=0.,first_renewal_step=282,pre_renewal_native2256_max_error=renewal['pre_trigger_native_max_error'],
    strict_goal_distance_m=result['goal_distance_m'],post_stop_displacement_m=chain['details']['post_stop_actual_displacement_m'],
    original_source_input_hashes_unchanged=True,primary_archive_compressed_manifest_reverified=True,review_guard_bytes_restored=True,
    new_models_closure=0,new_integrations_closure=0,no_more_physics=True,formal_development_passed=False,new24_confirmation_passed=False)
dump(supp/'SAVED_MAIN_EVIDENCE_SUMMARY.json',closed)
report=repo/'docs/RPCCR_GOAL_RENEWAL_20261105_CLOSURE_REPORT.md'
report.write_text('''# RP-CCR 目标参考更新：实际闭批报告

本次原南北主导航实际到达目标：623公开/4984原生，末距目标0.439949754m，原阈值0.45m以内。原12项物理/因果/控制审核和4984原生完整状态控制重放全部通过，最低实际净空0.243761598m，障碍接触/穿透/未知0，重放误差0。

原批次正式状态仍为GOAL_RENEWAL_DEVELOPMENT_NOT_PASSED。原因是新增audit_goal_renewal.py在加载footprint依赖时缺p0b68搜索路径，ModuleNotFoundError发生在其检查逻辑执行前。原源码、ERROR、COMPLETION、FINALIZED及原归档全部保持；驱动依照冻结协议停止，成功条件完整重复0/计划1未执行，新确认0。这不是车辆未到达，也不是本轮正式验收通过。

## 仅保存证据的零模型补核

闭批后在新只读symlink证据视图中，封死MuJoCo导入，只补原已冻结模块搜索路径，调用完全不修改的原新增审核。39条触发判定全部原因果重建通过，真正新增规划触发为282、436、455、467；282和467获得GLOBAL_GOAL_PATH，436/455仍为分段参考并如实保留。首触发282之前282公开/2256原生qpos/qvel/ctrl/mocap与原V821精确相同，误差0。

再对同一保存主轨迹执行未运行的原发现链审核，全部通过：224步/17.92s真实首次测距发现，发现前速度0.202279759m/s，已实际前进3.192466208m；原完整328原生/41公开刹停至1.4045e-5m/s，265新原因果参考，停车后真实位移3.392596908m，最后严格到达。所有623个原始传感包/原因果状态重建和329未来覆盖通过。补核不进行任何模型初始化、导航、私有预测或重放，不将旧批追认为通过，不补做物理重复。

## 实际分母与计算

- 原已观察南北任务新增主导航执行1次、保存完整链到达1次；它是开发中的一条已观察任务，不是独立新24成功率。
- 完整导航重复未执行1次；其余路线和新24未启动，不能报0/24或把V820西东旧成功混成新三路线。
- 本次完整导航4984/私有4012696/完整重放4984原生，全部准确。导航墙钟794.574s、仿真49.84s、10次规划/规划墙钟224.722s，不是实时。
- 资格另记4000旧重放/24656私有/656实际分支/656完整重复，模型内部构造数未单独计数。原V824模型前外层step错误和V825同原截止唯一元数据入口例外保留；V824原private=null不改，独立控制流证据另证明实际0。

改动只在RP-CCR全局参考续接触发。A*、控制库、评分、冻结BC网络和完整328安全尾保持。原run_static结果中的source_revision字符串继承V820标签，实际V826算法以CANDIDATE_FREEZE及90份源快照SHA为准；不把这个遗留标签当未改算法证明。相对于旧V821未到达，这条新主轨迹支持触发修订的可行性，尚无完整重复、跨路线泛化或公平对比结论。

## 科学范围与停止原因

原19静态体/单直径.20幅.25欧氏速.08actor/3m有噪声测距与5%漏检保持。发现前静态反应式合同仍较弱、公开3m起步排除先验；原更宽每轴.12类未通过，不外推任意遮挡、多actor、任意地图、实时或RAS全面优势。训练/SAC/Stage/实机0，current/runtime/模型/冻结网络不改。

本轮因原冻结新增审核入口异常停止，尽管保存主轨迹补核通过，也不恢复物理运行。REVIEW_PENDING原字节恢复、执行锁空闲；后续需独立注册完整重复及其他路线验证，不能复用本批失败状态宣称已验收。

原主归档17907来源/1783232220原始字节、所有来源/解压SHA和32MiB无损传输均由原finalizer回读，闭批再次核验原压缩文件清单SHA。补充证据单独归档，不覆盖原件，不删除runs或超90MiB本地大blob。最后同步仅本轮一次30秒push+5秒远端只读核验，结果见runs/goal_renewal_20261105/GIT_SYNC_RESULT.json；不重试旧同步。
''')
ledgerpath=day/'LEDGER.json';ledger=read(ledgerpath);ledger.update(status=closed['status'],closed=True,active_simulation=False,navigation_master_pid=None,new_navigation=1,private_native=4012696,full_replay_native=4984,
    navigation_native=4984,navigation_private_native=4012696,navigation_replay_native=4984,saved_main_arrivals=1,saved_discovery_chain_passed=True,original_development_passed=False,
    complete_repeat_unexecuted=1,new_confirmation=0,no_more_physics=True,stop_reason='Original frozen new audit import failure stopped batch; saved main goal and zero-model supplement passed; complete repeat unexecuted',report=str(report.relative_to(repo)))
dump(ledgerpath,ledger)
currentpath=repo/'CURRENT_EXPERIMENT.json';current=read(currentpath);current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_run=None,execution_window_closed=True,
    current_experiment='V826_CLOSED_MAIN_GOAL_VERIFIED_REPEAT_UNEXECUTED',report=str(report.relative_to(repo)),finite_full_field_dynamic_acceptance_passed=False)
current['goal_renewal_20261105'].update(closed=True,no_more_physics=True,original_development_passed=False,saved_main_goal_verified=True,complete_repeat_unexecuted=True,report=str(report.relative_to(repo)));dump(currentpath,current)
p=repo/'RESEARCH_STATUS.md';p.write_text(p.read_text()+'\n- FINAL V826主实际623公开/4984原生GOAL、余.439949754m，原12审核和完整重放全过/误差0、最低实际.243761598/障碍穿透未知0；私有4012696/重放4984准确。新增审核在加载footprint依赖时缺p0b68路径ModuleNotFoundError，原STOPPED_EXCEPTION/FINALIZED NOT_PASSED/归档保持，完整重复0/1未执行，不恢复物理。闭批新只读视图封死模型、仅补既有模块路径调用未修改原审核，39触发记录全部重建/首282升级完整目标路径，其前282公开2256原生与V821误差0；原未执行发现链保存补核亦全PASS：224发现/328停稳/265新路线/停车后位移3.392596908m/严格到达。原批未追认通过，不报新24验收。17907来源1.783GB原始归档/无损块回读保持，新增零模型证据另归档；根截止不重开、REVIEW_PENDING恢复/锁空闲/训练Stage实机0。报告docs/RPCCR_GOAL_RENEWAL_20261105_CLOSURE_REPORT.md。\n')
hand=day/'HANDOFF.md';hand.write_text(hand.read_text()+'\n## LATEST OVERRIDE · CLOSED, no more models or physics\n\nV826 raw main reached GOAL623public/4984native, remaining.439949754/minactual.243761598/contact0/statectrlreplay0. Original12 audits passed; original added audit failed before checking due missing hybrid_planner search path, so frozen driver/FINALIZED remain NOT_PASSED and complete repeat not executed. No physical continuation. Unchanged original added audit and original discovery-chain audit now passed in separate read-only saved-evidence view with NoModels blocker and explicit dependency search path. First trigger282, prior2256native errors0, full saved discovery/stop/replan/continue/arrival chain passed. See closed_audit_supplement and closure report. Counts:nav4984/private4012696/replay4984; qualification separate4000/24656/656/656. Finish supplemental archive, exactly one bounded new-round sync, delete phase-v826; no model retry/new pool/algorithm/training.\n')
# Snapshot mutable operation metadata before making a separate immutable supplement.
snap=supp/'OPERATIONAL_SNAPSHOT';snap.mkdir()
for p in[currentpath,ledgerpath,hand,repo/'RESEARCH_STATUS.md']:(snap/p.name).write_bytes(p.read_bytes())
files=[p for p in supp.rglob('*')if p.is_file()and not p.is_symlink()]
for p in day.rglob('*'):
    if not p.is_file()or p.is_symlink()or p.suffix=='.lock'or p.name in['LEDGER.json','HANDOFF.md','closure.console']:continue
    if supp in p.parents:continue
    files.append(p)
files += [p for p in Path(__file__).parent.glob('*')if p.is_file()]+[report,repo/'RPCCR_GOAL_RENEWAL_AUTHORIZATION_20261105.json',repo/'RPCCR_GOAL_RENEWAL_ENTRY_EXCEPTION_20261105.json',root/'FINALIZED.json',root/'FINAL_INDEPENDENT_AUDIT.json',repo/'runs/v826_finalize.console',root/'transport.console']
files=sorted(set(files));dest=repo/'evidence/rpccr_goal_renewal_20261105_closure';assert not dest.exists();dest.mkdir()
entries=[dict(path=str(p.relative_to(repo)),bytes=p.stat().st_size,sha256=sha(p))for p in files]
manifest_bytes=(json.dumps(entries,indent=2,ensure_ascii=False)+'\n').encode();(dest/'SOURCE_MANIFEST.json').write_bytes(manifest_bytes)
archive=dest/'closure.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
    z.writestr('SOURCE_MANIFEST.json',manifest_bytes)
    for p in files:z.writestr(str(p.relative_to(repo)),p.read_bytes())
with zipfile.ZipFile(archive)as z:
    assert z.read('SOURCE_MANIFEST.json')==manifest_bytes
    for entry in entries:
        data=z.read(entry['path']);assert len(data)==entry['bytes']and hashlib.sha256(data).hexdigest()==entry['sha256']and sha(repo/entry['path'])==entry['sha256']
assert archive.stat().st_size<90*1024**2
verified=dict(status='ALL_SUPPLEMENT_SOURCE_AND_DECOMPRESSED_SHA_VERIFIED',files=len(entries),raw_bytes=sum(x['bytes']for x in entries),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),models=0,integrations=0)
dump(dest/'ARCHIVE_VERIFIED.json',verified);closed.update(supplement_archive=str(dest.relative_to(repo)),supplement_source_sha_verified=True,report=str(report.relative_to(repo)));dump(day/'ZERO_MODEL_CLOSURE.json',closed)
print(json.dumps(closed),flush=True)
