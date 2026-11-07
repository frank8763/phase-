"""Saved-log diagnosis and immutable closure archive. No models or integrations."""
import datetime
import fcntl
import gzip
import hashlib
import json
import math
import shutil
import signal
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
root = repo/'runs/dynamic_acceptance_20261105'
batch = repo/'runs/v821_norm_route_development'
pair = batch/'main_slot02/paired'
cell = pair/'geometry_memory'
read = lambda p: json.loads(p.read_text())


def sha(p):
    digest = hashlib.sha256()
    with p.open('rb') as stream:
        for part in iter(lambda: stream.read(4*1024**2), b''):
            digest.update(part)
    return digest.hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


assert not (root/'ZERO_MODEL_CLOSURE.json').exists(), 'CLOSURE_ALREADY_RECORDED'
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('600S_ZERO_MODEL_CLOSURE')))
signal.alarm(600)
assert read(root/'ROUND_WINDOW.json')['round_closed']
assert not Path('/proc/178970').exists() and not Path('/proc/178978').exists()
assert (repo/'REVIEW_PENDING').read_bytes() == (root/'REVIEW_PENDING.before').read_bytes()
with (repo/'runs/v648_static_unknown/execution.lock').open('rb') as probe:
    fcntl.flock(probe,fcntl.LOCK_EX | fcntl.LOCK_NB)
    fcntl.flock(probe,fcntl.LOCK_UN)
assert read(batch/'FINALIZED.json')['source_and_decompressed_sha_verified']
assert read(batch/'FINALIZED.json')['status']=='NOT_PASSED'
assert not (repo/'runs/v822_norm_dynamic_confirmation/ROUND_WINDOW.json').exists()
for name in ['v821_norm_route_development','v822_norm_dynamic_confirmation']:
    freeze = read(repo/'experiments'/name/'CANDIDATE_FREEZE.json')
    assert all(sha(repo/n)==h for n,h in freeze['files'].items())
audit = read(batch/'FINAL_INDEPENDENT_AUDIT.json')
assert len(audit['records'])==1 and audit['records'][0]['physical_passed'] and not audit['records'][0]['functional_passed']
chain = read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')
assert [k for k,v in chain['checks'].items() if not v]==['strict_arrival']
result = read(cell/'result.json')
states = [json.loads(s) for s in (cell/'motion_estimate.jsonl').read_text().splitlines()]
observations = [x for x in states if x['observed_this_frame']]
execution = [json.loads(s) for s in (cell/'v648_execution.jsonl').read_text().splitlines()]
plans = []
for p in sorted(cell.glob('planning_*.json')):
    data = read(p); path = data['path']; stats = data['stats']
    plans.append(dict(path=str(p.relative_to(repo)),sha256=sha(p),step=data['step'],pose=data['pose'],
        status=stats['status'],expanded=stats.get('expanded'),wall_s=stats.get('wall_s'),
        nodes=None if path is None else len(path),endpoint=None if path is None else path[-1],
        endpoint_goal_distance_m=None if path is None else math.dist(path[-1][:2],data['causal_input']['goal']),
        fallback_stats={k:stats.get(k) for k in ['heuristic_start_m','heuristic_best_m','spatial_soft_reference','preferred_search']}))
diagnosis = dict(status='SAVED_LOG_DIAGNOSIS_VERIFIED_NO_NEW_ACTIONS',
    main_outcome=result['outcome'],goal_distance_m=result['goal_distance_m'],
    discovered_and_stopped_and_replanned_and_continued=True,chain=chain['details'],plans=plans,
    last_observed={k:observations[-1].get(k) for k in ['step','time','age_s','current_outer_rectangle']},
    final_belief={k:states[-1].get(k) for k in ['step','time','age_s','current_outer_rectangle','observed_this_frame']},
    final_xy=execution[-1]['qpos_full'][:2],final_speed_m_s=math.hypot(*execution[-1]['qvel_full'][:2]),
    walk_m=sum(math.dist(x['qpos_full'][:2],y['qpos_full'][:2]) for x,y in zip(execution,execution[1:])),
    navigation_wall_s=result['elapsed_s'],simulation_time_s=result['physics_steps']*.01,
    new_models=0,new_integrations=0,not_proof_of_global_continuous_infeasibility=True)
dump(root/'SAVED_LOG_DIAGNOSIS.json',diagnosis)
console = (root/'campaign.console').read_text()
assert "NameError: name 'json' is not defined" in console
error = dict(type='NameError',source='experiments/dynamic_acceptance_20261105/campaign.py',
    operation='Final stdout summary after finally wrote closed records and report',
    frozen_source_unchanged=True,source_not_repaired=True,original_console='runs/dynamic_acceptance_20261105/campaign.console',
    closed_records_and_stage_finalized_precede_error=True,scientific_nonarrival_preserved=True)
dump(root/'POST_COMPLETION_STDOUT_ERROR.json',error)
stamp = datetime.datetime.now().astimezone().isoformat()
summary = dict(status='CLOSED_DYNAMIC_ACCEPTANCE_NOT_PASSED',closed_at=stamp,
    additional_main_executed=1,additional_main_successes=0,planned_additional_main=2,additional_main_unexecuted=1,
    complete_repeats_executed=0,complete_repeats_unexecuted=2,
    fresh_confirmation_started=False,fresh_confirmation_main_executed=0,fresh_confirmation_tasks_unexecuted=24,
    confirmation_complete_repeats_executed=0,confirmation_complete_repeats_unexecuted=3,
    navigation_native=audit['navigation_native'],private_native=audit['private_native'],replay_native=audit['replay_native'],
    old_v820_navigation_native=13552,old_v820_private_native=10284544,old_v820_replay_native=13552,
    exact_integral_accounts=True,internal_model_initializations=None,
    all12_physical_evidence_audits_passed=True,full_state_ctrl_replay_max_error=0.,
    minimum_native_actual_clearance_m=result['minimum_dynamic_native_clearance_m'],
    bad_obstacle_contact_penetration_unknown=0,all_complete_chain_except_arrival_passed=True,
    review_guard_exact=True,execution_lock_free=True,scientific_sources_unchanged=True,
    automation_id='phase-dynamic-acceptance-20261105',automation_deleted=True,
    no_more_models_or_integrations=True,new_models_this_closure=0,new_integrations_this_closure=0,
    independent_stage_archive='evidence/rpccr_v821_norm_route_development_20261105',
    post_completion_stdout_error=error,report='docs/RPCCR_DYNAMIC_ACCEPTANCE_20261105_REPORT.md')
dump(root/'ZERO_MODEL_CLOSURE.json',summary)

analysis = '''# V821：南北路线失败的保存日志诊断

本次新增开发执行0/1成功；另一主任务和两次开发重复未执行。V822新24项以及三次确认重复全部未启动，不报0/24。V820西东原任务和重复通过的结论保留，不能据此声称三路线都通过。

问题出现在发现和重新规划之后的全局续接，而不是没有检测到障碍或车辆完全不跟随路径：第224步首次真实测距发现，完整328原生刹停后，第265步生成新因果参考；停车后实际位移3.875720m。这些链条审核均通过，只有最终到达门失败。最低原生实际净空0.245942m，障碍/穿透/未知接触0，完整4832原生状态控制重放误差0；安全证据通过不代表到达成功。

原始初始规划GLOBAL_GOAL_PATH有181节点，末距目标0.194861m；发现后第265步的规划是SAFE_PROGRESS_PREFIX，仅109节点，末距原目标仍1.929047m，不是另一条已连通目标的全局路径。车辆随后到达右下侧约[0.659,-2.680]，目标在[-1.278,-2.959]，二者隔着原竖直静态隔墙的下段。原完整场地/目标不变，不把这条分段路线称作完整绕障到达路线。

第564和604步重规划均返回NO_MEANINGFUL_GLOBAL_PROGRESS_WITHIN_BUDGET，保存的主回退搜索各用满16000扩展，上层还含4000优先/前向尝试，实际展开和墙钟分别记录在SAVED_LOG_DIAGNOSIS.json；不能把16000当所有搜索总量，不能由有限搜索拒绝证明所有连续控制无解。

最后一次新测距命中在第500步/40.00s，末第604步/48.32s已连续8.32s未新增命中。当前占据外框半宽从约[.2146,.2104]m扩大到[1.1915,1.2048]m。日志支持“分段参考终点缺少通往目标的后续续接，同时丢失新观测使当前占据变宽”的诊断。更具体的遮挡/量程成因、是否存在可执行返回通路及哪种修订有效尚未验证。本轮没有构造新动作、重新搜索或物理试探。

下一步研究应先针对原265/500/564/604保存状态，分离验证回到原目标的完整参考/允许必要回退的搜索进展判据与保持/恢复观测的条件，再单独注册有证据支持的算法修订。仅增加墙钟或把单条安全前缀当完整全局路径，不能据此解决验收。此段是未执行的下一步设计，不是已证明有效的新算法。

另有独立的收尾操作错误：主控campaign.py最后一行打印JSON摘要漏导入json。它发生在finally已写闭批/报告、V821独立终审和全归档完成之后，原NameError/源码/console全部保留，不修改冻结代码、不重跑；它不是南北主任务未到达的原因。
'''
analysis_path = repo/'docs/RPCCR_DYNAMIC_ACCEPTANCE_V821_ANALYSIS_20261105.md'
analysis_path.write_text(analysis)
overall = repo/'docs/RPCCR_DYNAMIC_ACCEPTANCE_20261105_REPORT.md'
overall.write_text(overall.read_text()+'''\n## 已核对的实际结果\n\n本轮新增开发0/1成功：NORTH_SOUTH/10010002共604公开/4832原生，未到达、余1.956521m。EAST_WEST主、两开发重复、V822新24及三确认重复均未执行；不得报告0/24。原全部12安全/命令/因果/覆盖/完整尾审核与完整状态控制重放通过，最低实际0.245942m、坏接触0、重放误差0。准确导航/私有/重放4832/3363872/4832，旧V820单任务成功及重复另记。\n\n已真实发现、刹停、重规划并续行3.875720m；发现后参考仅SAFE_PROGRESS_PREFIX，末端还差1.929047m，后续有限搜索未找到有意义进展，末8.32s无新增命中使当前占据框扩张。详见RPCCR_DYNAMIC_ACCEPTANCE_V821_ANALYSIS_20261105.md及runs/dynamic_acceptance_20261105/SAVED_LOG_DIAGNOSIS.json。不能把局部安全或一次西东路线成功当三路线/新24验收通过。\n\n主控最后打印摘要另有NameError（漏导入json），发生在闭批写盘和阶段终审归档之后；原源码和错误均保留，不追改原COMPLETION或修补重跑。REVIEW_PENDING原字节恢复、执行锁空闲、无后台物理，监控已因开发前置失败删除。本轮只零模型收尾，无追加实验。\n''')
ledger_path = repo/'RPCCR_DYNAMIC_ACCEPTANCE_LEDGER_20261105.json'
ledger = read(ledger_path)
ledger.update(status='CLOSED_DYNAMIC_ACCEPTANCE_NOT_PASSED',closure=summary,active_simulation=False,
    current_stage=None,closed=True,closed_at=stamp,automation_deleted=True,
    needs_review_commit_and_single_bounded_sync=True,no_more_models_or_integrations=True)
dump(ledger_path,ledger)
current_path = repo/'CURRENT_EXPERIMENT.json'
current = read(current_path)
current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',current_experiment='V821_CLOSED_FUNCTIONAL_NOT_PASSED',
    active_automation=None,active_entrypoint=None,active_run=None,active_pid=None,active_window=None,
    report=summary['report'],evidence=summary['independent_stage_archive'],requires_user_review_before_next_experiment=True,
    finite_full_field_dynamic_acceptance_passed=False)
current.setdefault('dynamic_acceptance_20261105',{}).update(closed=True,status=summary['status'],active_stage=None,
    campaign_pid=None,monitor_id=None,automation_deleted=True,closure='runs/dynamic_acceptance_20261105/ZERO_MODEL_CLOSURE.json',
    fresh_confirmation_started=False,report=summary['report'],new_main_successes=0,new_main_executed=1)
dump(current_path,current)
with (repo/'RESEARCH_STATUS.md').open('a') as f:
    f.write('\n- FINAL '+stamp+' V821原南北主604公开/4832导航原生、3363872私有/4832重放，NO_SAFE_PROGRESS_PATH_WITHOUT_RETAINED_RECOVERY/余1.956521m，新增开发执行0/1成功；另1主/2开发重复/V822新24和3确认重复全部未执行，不报0/24。12原安全证据审核、完整状态重放PASS/error0/最低.245942294m/坏接触0；真实224发现/328刹停/265新因果参考/实际续行3.875720m，仅到达失败。265参考SAFE_PROGRESS_PREFIX末余1.929047m，564/604有限搜索无有意义进展，最后500后8.32s无命中、当前占据框膨胀。阶段原始16252来源/1.546GB归档和24无损传输块回读通过；源保持冻结。主控末JSON打印漏import json的NameError在finally闭批和归档后发生，原错误保留、不修改冻结源或重跑。V822前置未过停止，全批REVIEW_PENDING/锁空闲/监控已删除，无新物理；只有零模型保存日志分析及补充归档/一次有界同步。详见docs/RPCCR_DYNAMIC_ACCEPTANCE_20261105_REPORT.md及V821_ANALYSIS。\n')
with (root/'HANDOFF.md').open('a') as f:
    f.write('\n## LATEST OVERRIDE\n\n'+stamp+' V821已FINALIZED NOT_PASSED，新增开发0/1功能成功；另1主/2重复和V822新24/3重复未执行。全部12物理证据审核/4832完整重放误差0/最低.245942294/坏接触0，4832导航/3363872私有/4832重放准确。完整发现刹停新参考续行均过、仅目标失败。主控最后stdout漏import json NameError原样保留，科学源冻结不改，不修补重跑。campaign已闭批，原guard恢复/锁空闲/父子master均退出；本监控已实际删除，停止原因开发前置失败。只补充零模型归档、审阅提交、本轮一次30s push+5s远端HEAD核验（先查GIT_SYNC_RESULT.json），旧V820同步绝不重试，原始证据不删，不再任何模型/导航/私有/重放/训练。\n')

# Verify the immutable original archive and transport again; never overwrite it.
archive = repo/summary['independent_stage_archive']
for item in read(archive/'MANIFEST.json'):
    assert (archive/item['path']).stat().st_size==item['bytes'] and sha(archive/item['path'])==item['sha256']
inventory = json.loads(gzip.decompress((archive/'RAW_INVENTORY.json.gz').read_bytes()))
cache = {}
for item in inventory:
    if item['blob'] not in cache:
        data = (archive/item['blob']).read_bytes()
        raw = data if item['encoding']=='identity' else gzip.decompress(data)
        cache[item['blob']] = (len(raw),hashlib.sha256(raw).hexdigest())
    assert cache[item['blob']] == (item['bytes'],item['sha256']) and sha(repo/item['path'])==item['sha256']
transport = read(repo/(summary['independent_stage_archive']+'_transport/TRANSPORT_MANIFEST.json'))
for item in transport['entries']:
    digest = hashlib.sha256();size=0
    for part in item['chunks']:
        data=(repo/part['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==part['sha256'];digest.update(data);size+=len(data)
    assert digest.hexdigest()==item['sha256'] and size==item['bytes'] and sha(repo/item['original_blob'])==item['sha256']

dest = repo/'evidence/rpccr_dynamic_acceptance_20261105_closure'
assert not dest.exists()
snapshot = root/'closure_snapshot';snapshot.mkdir(exist_ok=False)
for p in [current_path,ledger_path,repo/'RESEARCH_STATUS.md',overall]:shutil.copyfile(p,snapshot/p.name)
files = set(p for p in root.rglob('*') if p.is_file() and p.suffix not in ['.lock','.pyc'] and '__pycache__' not in p.parts)
files.update(p for p in Path(__file__).parent.glob('*.py'))
files.update(p for p in (repo/'experiments/v822_norm_dynamic_confirmation').iterdir() if p.is_file())
files.update([analysis_path,repo/'RPCCR_DYNAMIC_ACCEPTANCE_AUTHORIZATION_20261105.json',batch/'FINALIZED.json',
              batch/'FINAL_INDEPENDENT_AUDIT.json',batch/'finalize.console',batch/'transport.console',batch/'driver.console'])
dest.mkdir();(dest/'blobs').mkdir();extra=[]
for p in sorted(files):
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();blob=dest/'blobs'/(h+'.gz')
    if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
    extra.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(extra,indent=2).encode(),mtime=0))
for item in extra:
    raw=gzip.decompress((dest/item['blob']).read_bytes());assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'] and sha(repo/item['path'])==item['sha256']
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(dest.rglob('*')) if p.is_file()]
dump(dest/'MANIFEST.json',manifest)
assert all(sha(dest/x['path'])==x['sha256'] for x in manifest)
dump(root/'CLOSURE_ARCHIVE_VERIFIED.json',dict(status='ALL_SOURCE_DECOMPRESSED_AND_TRANSPORT_SHA_VERIFIED',
    original_archive=summary['independent_stage_archive'],original_sources=len(inventory),
    supplement_archive=str(dest.relative_to(repo)),supplement_sources=len(extra),supplement_raw_bytes=sum(x['bytes'] for x in extra),
    original_raw_deleted=False,new_models=0,new_integrations=0))
signal.alarm(0)
print(json.dumps(dict(status=summary['status'],navigation_native=summary['navigation_native'],private_native=summary['private_native'],
    replay_native=summary['replay_native'],confirmation_unexecuted=24,archive_verified=True,supplement_sources=len(extra))))
