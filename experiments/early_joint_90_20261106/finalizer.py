"""Independent persisted-evidence audit and lossless archive, zero models/integrations."""
import fcntl
import gzip
import json
import subprocess
import sys
from pathlib import Path
from evidence_rules import AUDITS, FUNCTIONAL_CHECKS, dump, main_gate, read, repeat_check, sha


def finalize(own):
    repo = own.parents[1]
    config = read(own/'BATCH.json')
    root = repo/config['output']
    lock = (root/'finalize.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root/'FINALIZED.json').exists():
        print(json.dumps(read(root/'FINALIZED.json')))
        return
    assert read(root/'ROUND_WINDOW.json')['round_closed']
    assert (repo/'REVIEW_PENDING').read_bytes() == (root/'REVIEW_PENDING.before').read_bytes()
    window = root/config['window']
    completion = read(window/'COMPLETION.json')
    tasks = read(own/'TASK_LIST.json')
    rows = completion['records']
    freeze = read(own/'CANDIDATE_FREEZE.json')
    source_ok = all(sha(repo/n)==h for n,h in freeze['files'].items())
    assert read(window/'LOCKED_TASK_LIST.json') == tasks, 'TASK_LIST_CHANGED'
    reference = repo/config['reference_view']
    assert read(repo/'runs/early_joint_90_20261106/ZERO_MODEL_QUALIFICATION.json')['passed']
    records = []
    actual = private = replay = 0
    nav_exact = private_exact = replay_exact = True
    sys.path.insert(0,str(own))
    from contact_fingerprint import compare_contacts
    for row in rows:
        pair = repo/row['run']
        result = read(pair/'geometry_memory/result.json') if (pair/'geometry_memory/result.json').exists() else None
        interrupted = read(pair/'geometry_memory/interrupted.json') if (pair/'geometry_memory/interrupted.json').exists() else None
        state = result or interrupted or {}
        nav_count, private_count = state.get('physics_steps'), state.get('prediction_steps')
        nav_exact &= result is not None and isinstance(nav_count,int)
        private_exact &= result is not None and isinstance(private_count,int)
        actual += nav_count if isinstance(nav_count,int) else 0
        private += private_count if isinstance(private_count,int) else 0
        rp = pair/'NATIVE_REPLAY_AUDIT.json'
        native = read(rp) if rp.exists() else None
        replay_exact &= native is not None
        replay += 0 if native is None else native.get('replay_integration_steps',0)
        audit_statuses = {}
        for script,filename,_ in AUDITS:
            p = pair/filename
            data = read(p) if p.exists() else {}
            expected = read(reference/filename)['status']
            audit_statuses[script] = bool(row['audits'].get(script)==0 and data.get('status')==expected
                                         and all(data.get('checks',{}).values()))
        chain_path = pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json'
        chain = read(chain_path) if chain_path.exists() else None
        failed = [] if chain is None else [k for k,v in chain['checks'].items() if not v]
        physical = bool(source_ok and result is not None and native is not None and
                        native['status']=='MATCHED_RECORDED_PUBLIC_STATES' and
                        native['maximum_full_native_state_ctrl_error'] <= 1e-8 and
                        native['replay_integration_steps']==result['physics_steps'] and
                        all(audit_statuses.values()) and chain is not None and not(set(failed)-FUNCTIONAL_CHECKS))
        functional = bool(physical and chain['status']=='PASS' and all(chain['checks'].values()) and
                          result['strict_safe_arrival'] and result['outcome']=='GOAL' and result['goal_distance_m']<=.45)
        independent = dict(name=row['name'],task=row['task'],role=row['role'],run=row['run'],
                           physical_passed=physical,functional_passed=functional,
                           audit_statuses=audit_statuses,result=result,failed_functional_checks=failed,
                           repeated=None)
        if row['role']=='REPEAT' and result is not None:
            base = next((x for x in records if x['role']=='MAIN' and x['task']['slot']==row['task']['slot']),None)
            if base is not None and base['result'] is not None:
                independent['repeated'] = repeat_check(repo/base['run'],pair,base['result'],result,compare_contacts)
                dump(pair/'FINAL_INDEPENDENT_REPEAT.json',independent['repeated'])
        records.append(independent)
    gate = main_gate(tasks,records,config['confirmation'])
    repeats = [x for x in records if x['role']=='REPEAT']
    repeated_ok = len(repeats)==len(config['repeat_slots']) and [x['task']['slot'] for x in repeats]==config['repeat_slots'] and all(
        x['physical_passed'] and x['functional_passed'] and x['repeated'] is not None and x['repeated']['passed'] for x in repeats)
    preflight_file = window/'PREFLIGHT_INDEPENDENT_AUDIT.json'
    preflight_ok = preflight_file.exists() and read(preflight_file)['status']=='PASS' and read(preflight_file)['tasks']==len(tasks)
    passed = bool(source_ok and gate['passed'] and repeated_ok and preflight_ok and
                  all(x['physical_passed'] for x in records) and completion['status']=='FROZEN_TASKS_AND_REPEATS_COMPLETED' and
                  nav_exact and private_exact and replay_exact)
    combined = bool(not config['confirmation'] and passed and read(repo/'runs/early_joint_90_20261106/ZERO_MODEL_QUALIFICATION.json')['passed'])
    status = ('FINITE_FULL_FIELD_DYNAMIC_CONFIRMATION_PASS' if config['confirmation'] else 'ONE_FIXED_SCENE_AND_COMPLETE_REPEAT_VERIFIED') if passed else 'NOT_PASSED'
    result = dict(status=status,development_passed=(passed if not config['confirmation'] else False),
                  confirmation_passed=(passed if config['confirmation'] else False),
                  single_fixed_scene_development_passed=combined, source_unchanged=source_ok,
                  preflight_passed=preflight_ok, main_gate=gate, complete_repeats=len(repeats),
                  repeats_passed=repeated_ok, records=records,
                  navigation_native=(actual if nav_exact else None), known_navigation_native=actual,
                  private_native=(private if private_exact else None),known_private_native=private,
                  replay_native=(replay if replay_exact else None), known_replay_native=replay,
                  navigation_account_exact=nav_exact,private_account_exact=private_exact,replay_account_exact=replay_exact,
                  new_confirmation_tasks=(len(tasks) if config['confirmation'] else 0),reused_saved_main_references=0,reused_reference_not_new_sample=True,algorithm='EARLY_JOINT_NOMINAL_AND_COMPLETE_TAIL_WITH_336_CONTINUATION',
                  new_models_finalizer=0,new_integrations_finalizer=0,training_updates=0,stage_access=0,real_robot=0)
    dump(root/'FINAL_INDEPENDENT_AUDIT.json',result)
    report = repo/config['report']
    lines = [f"# RP-CCR {config['label']} 实际报告",'',f"独立结论：**{status}**。",'',
             f"主任务尝试{gate['main_attempts']}/{gate['planned_main']}，完整链成功{gate['main_successes']}，未执行{gate['unexecuted_main']}。完整重复{len(repeats)}/{len(config['repeat_slots'])}，全部通过={repeated_ok}。",
             f"完整分母成功率：{gate['success_rate'] if gate['success_rate'] is not None else '未执行完整分母，不报全分母率'}。分路线{gate['route_successes']}，分方向{gate['direction_successes']}。",'',
             '|槽位|路线|噪声种子|主任务状态|公开步|目标距离m|最低实际净空m|', '|---|---|---|---|---|---|---|']
    by_slot = {x['task']['slot']:x for x in records if x['role']=='MAIN'}
    for task in tasks:
        row = by_slot.get(task['slot']); r = {} if row is None else row['result'] or {}
        state = '未执行' if row is None else '完整链成功' if row['functional_passed'] else '未成功/未验证'
        lines.append(f"|{task['slot']}|{task['case_id']}|{task['seed']}|{state}|{r.get('public_steps','—')}|{r.get('goal_distance_m','—')}|{r.get('minimum_dynamic_native_clearance_m','—')}|")
    lines += ['',f"本批实际导航/私有/重放={result['navigation_native']}/{result['private_native']}/{result['replay_native']}原生；null表示未知，不能填0。内部模型加载次数未知。",
              ('本批为事前锁定10070001–24新确认，各完整重复另计。'if config['confirmation']else'原10060002单个旧失败开发样本；成功才同版本完整重复，不混新确认。')+'所有旧失败保持。',
              '保持原19静态体、三固定路线、单直径.20m/幅.25m/最大欧氏速.08m/s actor、3m测距和5%漏检。在线仅原因果观测；真实相位/轨迹只用于场景和离线评价。',
              '发现前静态合同是已声明较弱反应式条件；发现后原.155预测/.15实际净空、完整328刹停、329执行/657规划包含、全部尾和合法控制及状态重放门保持。原更宽每轴.12运动类未通过，不宣称隐藏突入、多actor、任意地图、实时性、递归安全或RAS保证。',
              '新增为跟踪后在原完整328后再查8原生无未来观测接续；旧证书净空余量低于.155+.08×3.28=.4174时提前联合至多4个原名义首命令与原21及18沿参考完整尾，按完整328净空+.5目标进展选择，原.155/.002/.025/.02进展门保持。仅普通行驶提前联合；原返回保持不变。新增完整保存接续和独立控制重建审计，非递归可行保证。首次开发功能或安全证据失败停，确认第二功能或首次安全证据失败停，不修补/替补/新池。',
              'REVIEW_PENDING原字节恢复；本报告和原始证据归档回读后才写FINALIZED。']
    report.write_text('\n'.join(lines)+'\n')
    archive = repo/config['archive']
    assert not archive.exists(), 'ARCHIVE_MUST_NOT_BE_OVERWRITTEN'
    archive.mkdir(); (archive/'blobs').mkdir()
    files = {repo/n for n in freeze['files']}
    for directory in [root,own,Path(__file__).parent]:
        files.update(p for p in directory.rglob('*') if p.is_file() and p.suffix not in ['.pyc','.lock']
                     and '__pycache__' not in p.parts and p.name not in ['finalize.console','transport.console'])
    files.add(report)
    import os
    previous=repo/'evidence/rpccr_goal_reference_renewal_v826_20261105'
    inventory = []
    for p in sorted(files):
        raw = p.read_bytes(); h = __import__('hashlib').sha256(raw).hexdigest()
        encoding = 'identity' if p.suffix=='.gz' else 'gzip'
        blob = archive/'blobs'/(h+('.raw' if encoding=='identity' else '.gz'))
        if not blob.exists():
            old_blob=previous/'blobs'/blob.name
            if old_blob.exists():os.link(old_blob,blob)
            else:blob.write_bytes(raw if encoding=='identity' else gzip.compress(raw,mtime=0))
        inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(archive)),encoding=encoding))
    (archive/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
    verified = {}
    for item in inventory:
        if item['blob'] not in verified:
            data = (archive/item['blob']).read_bytes()
            raw = data if item['encoding']=='identity' else gzip.decompress(data)
            verified[item['blob']] = (len(raw),__import__('hashlib').sha256(raw).hexdigest())
        assert verified[item['blob']] == (item['bytes'],item['sha256']) and sha(repo/item['path'])==item['sha256']
    manifest = [dict(path=str(p.relative_to(archive)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(archive.rglob('*')) if p.is_file()]
    dump(archive/'MANIFEST.json',manifest)
    assert all(sha(archive/x['path'])==x['sha256'] for x in manifest)
    transport = None
    if any(x['bytes']>90*1024**2 for x in manifest):
        transport = config['archive']+'_transport'
        process = subprocess.run([sys.executable,'-B',str(repo/'experiments/global_day_20261104_analysis/transport_archive.py'),str(archive),str(repo/transport)],cwd=repo,capture_output=True,text=True,timeout=605)
        (root/'transport.console').write_text(process.stdout+process.stderr)
        assert process.returncode==0, 'TRANSPORT_REASSEMBLY_FAILED'
    dump(root/'FINALIZED.json',dict(status=status,development_passed=(passed and not config['confirmation']),
        confirmation_passed=(passed and config['confirmation']),single_fixed_scene_development_passed=combined,
        archive=config['archive'],transport=transport,source_and_decompressed_sha_verified=True,
        raw_files=len(inventory),raw_bytes=sum(x['bytes'] for x in inventory),raw_deleted=False,
        report=config['report'],new_models_finalizer=0,new_integrations_finalizer=0))
    print(json.dumps(read(root/'FINALIZED.json')))
