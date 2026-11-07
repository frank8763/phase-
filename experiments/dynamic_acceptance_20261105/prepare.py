"""Prepare a fresh bounded validation campaign; this script constructs no models."""
import datetime
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo
from evidence_rules import dump, sha

repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
root = repo/'runs/dynamic_acceptance_20261105'
auth_path = repo/'RPCCR_DYNAMIC_ACCEPTANCE_AUTHORIZATION_20261105.json'
assert not auth_path.exists(), 'CAMPAIGN_AUTHORIZATION_ALREADY_EXISTS'
root.mkdir(exist_ok=True)
pattern = r'1006000[1-9]|1006001[0-9]|1006002[0-4]'
probe = subprocess.run(['rg','-n',pattern,'runs','-g','*.json','-g','*.jsonl','--max-count','1'],cwd=repo,capture_output=True,text=True)
assert probe.returncode==1 and not probe.stdout, 'RESERVED_NEW_NOISE_POOL_ALREADY_REFERENCED_IN_PRIOR_RUNS'
dump(root/'POOL_UNUSED_BEFORE_PREPARATION.json',dict(checked_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    command='rg -n registered10060001-24 runs -g *.json -g *.jsonl',exit_code=probe.returncode,
    navigation_and_run_record_matches=0,models_constructed=0,integrations=0))
started = time.time()
deadline = started+43200
auth = dict(user_instruction='2026-11-05 用户：好，现在将动态的验收吧',authorized_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    started_unix=started,absolute_deadline_unix=deadline,hard_stop_beijing=datetime.datetime.fromtimestamp(deadline,ZoneInfo('Asia/Shanghai')).isoformat(),
    total_wall_cap_s=43200,source_algorithm='V820_DECLARED_NORM_REFINED_COMPLETE_CAUSAL_PREFIX_TAIL',scientific_revisions=0,
    max_development_extension_batches=1,max_fresh_confirmation_batches=1,post_freeze_repairs=0,
    extension_main_tasks=2,extension_complete_repeats=2,existing_v820_main_and_repeat_not_rerun=True,
    confirmation_tasks=24,confirmation_complete_repeats=[1,9,17],new_noise_pool=[10060001,10060024],
    extension_cap_s=8100,confirmation_cap_s=36000,finalization_only_cap_s=1800,
    nav_public_cap=1200,nav_soft_s=1200,nav_hard_s=1500,nav_outer_s=1505,t0_internal_s=120,t0_outer_s=125,
    declared_norm_speed_m_s=.08,broader_axis_class_not_claimed=True,old_windows_and_failures_immutable=True,
    all_models_only_run_phase=True,single_cpu_sequential=True,training_updates=0,stage_access=0,real_robot=0,
    no_subagents_new_chats_external_messages=True,physics_stops_at_absolute_deadline=True)
dump(auth_path,auth)
dump(repo/'RPCCR_DYNAMIC_ACCEPTANCE_LEDGER_20261105.json',dict(status='PREPARING',started_unix=started,absolute_deadline_unix=deadline,
    development_extensions_started=0,confirmation_batches_started=0,scientific_revisions=0,post_freeze_repairs=0,
    current_stage=None,active_simulation=False,closed=False,new_confirmation_attempted=0,raw_deleted=False,
    no_old_sync_retry=True))
old = repo/'experiments/v820_tracked_norm_global'
cases = json.loads((old/'SCENE_CASES.json').read_text())
original = json.loads((repo/'experiments/v812_soft_global_reference/DEVELOPMENT_TASKS.json').read_text())
development = original[1:]
confirmation = []
for route_index,case in enumerate(cases):
    for j in range(8):
        slot = route_index*8+j+1
        seed = 10060000+slot
        u = int.from_bytes(hashlib.sha256(f'RPCCR_NORM_CONFIRMATION_20261105|{seed}'.encode()).digest()[:8],'big') / 2**64
        phase = ((math.pi*u-math.pi/2)+(math.pi if j%2 else 0))%(2*math.pi)
        confirmation.append(dict(slot=slot,seed=seed,phase=phase,case_id=case['id'],
            initial_axis_motion_direction='NEGATIVE_AXIS' if j%2 else 'POSITIVE_AXIS',
            course_distance_m=case['euclidean_distance_m'],role='FRESH_CONFIRMATION',
            phase_rule='SHA256 RPCCR_NORM_CONFIRMATION_20261105|seed; uniform conditional cos-sign, four each direction per route'))
dump(root/'LOCKED_NEW_CONFIRMATION_TASKS.json',confirmation)
plan = f'''# RP-CCR 完整场地动态新验收批 · 2026-11-05

用户在审阅V820结果后明确要求动态验收。本轮只验证冻结V820方法，不新改算法、模型、网络或安全门。
这是新独立窗口，硬截止{auth['hard_stop_beijing']}（Unix {deadline}），自准备起最多12小时；所有旧批次/截止不变，绝不重置或延长。

V821先复核V820原WEST_EAST主及完整重复全门和归档，再仅原NORTH_SOUTH/10010002、EAST_WEST/10010003及原连续相位，两t0全预检、两主、全过条件两完整重复；上限8100秒。固定失败不换路线、不修补克隆。已有V820一主一重复不重跑，不计新样本；合起来是原三路线各主+重复的开发验证，不是新确认。

仅V821全物理/功能/因果/全状态重放/完整重复、独立终审和所有来源/解压SHA回读全部通过，才启动V822。
V822预先冻结10060001–10060024、三路线各8、正反各12、连续初相位，24真实t0全预检后按slot1–24顺序主导航。
至少23/24完整链、每路线至少7/8、方向各至少11/12，第二功能未成功或首次安全/源码/模型/真值/状态/控制/覆盖/证据异常停止。固定slot1/9/17完整重复均须完整链成功及全状态qpos/qvel/ctrl/mocap误差<=1e-8、模型/规范初态/真实接触/发现一致；若固定重复基线未成功则不替换，确认不通过。
未完成全24不报全分母成功率；开发、旧空白24和重复均不混入新确认分母。只有全部终审及归档回读后称有限完整场地确认通过。

确认上限36000秒且不得越总截止，足额余时不足不启动；不另开第二池。所有子进程绝对墙钟有限，nav1200公开/1200soft1500hard1505outer、t0120internal125outer。首功能失败停止开发，确认最多容许一个严格安全且证据完整的功能失败。
原19静态实体、单直径.20m/幅.25m/欧氏速.08actor、3m原测距和5%漏检、原路线/初态/噪声机制、模型及网络不改；actor未来真值只物理/传感及离线评价，不能进在线控制。发现前已知静态合同是更弱反应式条件，公开3m起步先验；发现后完整328尾/.155预测/.15原生实际/329执行657规划包含、自体合法ctrl速率、静态体固定、无积分外根写、全部状态控制重放和所有尾门保持。
真实正常行驶首次测距发现—实际328刹停—新原因果路线—实际续行>=1m—目标<=.45为完整链。公开.08norm课程不冒称原更宽每轴.12类、任意遮挡/多actor/任意地图/实时性/递归安全/RAS优势。

全部模型构造/导航/私有/重放只run_phase.sh Stage隔离入口，单CPU顺序单实例及执行锁；训练/SAC/实机0，current/runtime/冻结网络不改。新科学源冻结后不修改或修补，初始化/入口失败也登记停止。全部原失败和原始证据保留，超100MB压缩blob32MiB无损分块重组核验，原件不删。
最终独立终审/全分母/未执行/准确或未知导航私有重放分账，归档回读、报告、审阅提交。本轮最后仅一次30秒push+5秒远端HEAD核验，失败不循环；旧V820同步不重试。
完成、失败或截止后停止模型和积分、恢复REVIEW_PENDING、删除本监控。不自动算法对比、训练、距离/地图/机制扩展，不创建新聊天或子代理或外部消息。
'''
(repo/'docs/RPCCR_DYNAMIC_ACCEPTANCE_20261105_PLAN.md').write_text(plan)
(root/'HANDOFF.md').write_text('# Phase dynamic acceptance\n\n## LATEST OVERRIDE\n\n准备新V821→条件V822，同冻结V820科学方法，旧V820已闭批不重开。绝对截止见新AUTH，不得延长；正在准备时不并发另起工作。只有ZERO_MODEL_QUALIFICATION和两份冻结清单齐全才启动campaign.py一次；已启动只监控，禁止重复实例和冻结后修补。\n')
identity = []
for name,tasks,confirm in [('v821_norm_route_development',development,False),('v822_norm_dynamic_confirmation',confirmation,True)]:
    directory = repo/'experiments'/name
    directory.mkdir(exist_ok=False)
    for p in old.iterdir():
        if p.is_file() and p.suffix in ['.py','.json'] and p.name not in ['CANDIDATE_FREEZE.json','DEVELOPMENT_TASKS.json','execute_development.py','finalize_development.py']:
            shutil.copyfile(p,directory/p.name)
    source = (old/'run_static.py').read_text()
    assert source.count("/'v820_tracked_norm_global'/")==1
    (directory/'run_static.py').write_text(source.replace("/'v820_tracked_norm_global'/",f"/'{name}'/"))
    source = (old/'audit_field_preflight.py').read_text()
    assert source.count('len(details)==len(tasks)==1')==1
    source = source.replace('len(details)==len(tasks)==1',f'len(details)==len(tasks)=={len(tasks)}')
    source = source.replace('One preregistered original WEST_EAST development route before navigation; no task rejection/replacement by navigation result',
                            'Preregistered fixed task list before navigation; no rejection or replacement by navigation result')
    (directory/'audit_field_preflight.py').write_text(source)
    dump(directory/'TASK_LIST.json',tasks)
    dump(directory/'DEVELOPMENT_TASKS.json',tasks)
    (directory/'PROTOCOL.md').write_text(plan+'\n本命名空间：'+name+'；任务数'+str(len(tasks))+'。\n')
    dependency = 'runs/v821_norm_route_development' if confirm else 'runs/v820_tracked_norm_global'
    dump(directory/'BATCH.json',dict(label='V822_NEW24_CONFIRMATION' if confirm else 'V821_REMAINING_TWO_ROUTES',
        confirmation=confirm,output='runs/'+name,window='confirmation01' if confirm else 'development01',
        dependency=dependency,absolute_deadline_unix=deadline,batch_cap_s=36000 if confirm else 8100,
        minimum_start_budget_s=36000 if confirm else 7200,repeat_slots=[1,9,17] if confirm else [2,3],
        archive='evidence/rpccr_'+name+'_20261105',report='docs/RPCCR_'+('NORM_CONFIRMATION_V822' if confirm else 'NORM_ROUTES_V821')+'_REPORT.md'))
    for script,module,function in [('execute.py','runner','run'),('finalize.py','finalizer','finalize')]:
        (directory/script).write_text('from pathlib import Path\nimport sys\nown=Path(__file__).resolve().parent\nsys.path.insert(0,str(own.parent/"dynamic_acceptance_20261105"))\nfrom '+module+' import '+function+'\n'+function+'(own)\n')
    equal=[]
    for p in directory.glob('*.py'):
        if p.name in ['execute.py','finalize.py','run_static.py','audit_field_preflight.py']:continue
        assert p.read_bytes()==(old/p.name).read_bytes(),p.name
        equal.append(dict(file=p.name,sha256=sha(p)))
    assert (directory/'run_static.py').read_text().replace(f"/'{name}'/","/'v820_tracked_norm_global'/")== (old/'run_static.py').read_text()
    identity.append(dict(namespace=name,algorithm_modules_byte_identical=equal,runner_only_output_namespace_changed=True,
                         preflight_only_registered_task_count_and_scope_adapted=True,scientific_changes=0))
    (repo/'runs'/name).mkdir(exist_ok=False)
dump(root/'ALGORITHM_IDENTITY.json',identity)
current = json.loads((repo/'CURRENT_EXPERIMENT.json').read_text())
current.update(status='PREPARING_DYNAMIC_ACCEPTANCE',state='PREPARING_DYNAMIC_ACCEPTANCE',requires_user_review_before_next_experiment=False)
current['dynamic_acceptance_20261105'] = dict(authorization=str(auth_path.relative_to(repo)),absolute_deadline_unix=deadline,
    algorithm='V820_UNCHANGED',development_remaining_routes=2,fresh_confirmation_tasks=24,models_started=False)
dump(repo/'CURRENT_EXPERIMENT.json',current)
print(json.dumps(dict(status='PREPARED_NOT_FROZEN_OR_STARTED',absolute_deadline_unix=deadline,hard_stop_beijing=auth['hard_stop_beijing'],new_models=0,new_integrations=0)))
