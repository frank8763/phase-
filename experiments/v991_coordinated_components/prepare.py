"""Freeze exact V990 entry after complete zero-model qualifications."""
import ast,fcntl,hashlib,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v991_coordinated_components';REC=R/'records/nav2_v991_20261110'
NAMES=['ZERO_MODEL_ENTRY_QUALIFICATION.json','BINDING_QUALIFICATION.json','COMPONENT_CONTRACT_QUALIFICATION.json',
       'SOFTWARE_QUALIFICATION.json','BUDGET_QUALIFICATION.json','RESTORE_CONTROL_FLOW_QUALIFICATION.json',
       'CLOSURE_QUALIFICATION.json','NATIVE_LOOP_QUALIFICATION.json','REPORTING_CLOCK_QUALIFICATION.json',
       'CAMPAIGN_QUALIFICATION.json','PEER_ISOLATION_QUALIFICATION.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')

def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=sha(R/'REVIEW_PENDING');assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert all(read(O/n)['passed']for n in NAMES)
    assert not any((O/n).exists()for n in ['USER_APPROVAL.json','ROUND_WINDOW.json','AUTHORIZATION.json','CAMPAIGN_CLAIM.json'])
    files={};old=read(R/'experiments/v987_bounded_startup_components/SOURCE_FREEZE.json')
    candidate=read(R/'experiments/v990_coordinated_actuation/SOURCE_FREEZE.json')
    for freeze in [old,candidate]:
        for name,h in freeze['files'].items():assert sha(R/name)==h,name;files[name]=h
    for version in ['v987_bounded_startup_components','v990_coordinated_actuation']:
        p=R/'experiments'/version/'SOURCE_FREEZE.json';files[str(p.relative_to(R))]=sha(p)
    original=read(R/'experiments/v987_bounded_startup_components/TASKS.json');tasks=read(C/'TASKS.json')
    same=['case_id','seed','phase','dynamic','goal_xy','goal_yaw','wall_limit_s','brake_s','stage','slot','fixed_state_index','origin_native_tick','origin_sim_time']
    assert len(tasks)==2 and all(all(a[k]==b[k]for k in same)for a,b in zip(tasks,original))
    unchanged=['state_reference.py','command_tube.py','cycle_backup.py','steering_continuity.py','navigation_policy.py',
        'shaping_audit.py','A_forward.yaml','tracking.py','transaction.py','independent_tracking.py','closure.py',
        'native_loop.py','startup_progress.py','budget.py']
    exact_byte_science=[]
    for name in unchanged:
        new=(C/name).read_text();prior=(R/'experiments/v987_bounded_startup_components'/name).read_text()
        # Only declared output/task namespace substitutions are permitted where
        # operation source contains its own path; scientific files are exact.
        normalized=prior.replace('v987_bounded_startup_components','v991_coordinated_components').replace('nav2_v987_20261110','nav2_v991_20261110').replace('V987','V991').replace('v987','v991')
        assert new==normalized,'UNINTENDED_REFERENCE_GATE_OR_CLOCK_CHANGE '+name
        if new==prior:exact_byte_science.append(name)
    REC.mkdir(exist_ok=True)
    for name in [*NAMES,'PREPARATION_FAILURES.json']:
        (REC/name).write_bytes((O/name).read_bytes())
        for p in [O/name,REC/name]:files[str(p.relative_to(R))]=sha(p)
    for name in ['SEED_HISTORY_0.json','SEED_HISTORY_1.json']:
        p=O/name;assert p.read_bytes()==(R/'runs/v987_bounded_startup_components'/name).read_bytes()
        files[str(p.relative_to(R))]=sha(p)
    for p in C.iterdir():
        assert not p.is_symlink()
        if p.is_file()and p.name!='SOURCE_FREEZE.json':
            if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
            files[str(p.relative_to(R))]=sha(p)
    frozen=dict(final=True,awaiting_explicit_physical_approval=True,models_before_freeze=0,integrations_before_freeze=0,
        scientific_control_source='experiments/v990_coordinated_actuation/vehicle_control.py',files=files)
    p=C/'SOURCE_FREEZE.json'
    if p.exists():assert read(p)==frozen,'FROZEN_SOURCE_CHANGED'
    else:dump(p,frozen)
    binding=read(O/'BINDING_QUALIFICATION.json');entry=read(O/'ZERO_MODEL_ENTRY_QUALIFICATION.json')
    final=dict(status='PREPARED_AWAITING_NEW_BOUNDED_PHYSICAL_APPROVAL',source_qualification_passed=True,
        models=0,actual_native=0,private_native=0,replay_native=0,new_navigation_samples=0,new24=0,training=0,hardware=0,
        models_authorized=False,physical_ready=False,no_model_window_opened=True,fixed_components=2,
        proposed_root_s=5400,component_wall_s=40,component_stop_s=2,
        frozen_files=len(files),old_v987_frozen_files_unchanged=len(old['files']),V990_source_exact=True,
        source_freeze_sha256=sha(p),actual_worker_switch_and_audit_bound=True,canonical_model_audit_performed=False,
        entry_checks=len(entry['checks']),binding_checks=len(binding['checks']),binding_negative_cases=len(binding['negative_cases']),
        complete_stop_contract_checks=len(read(O/'COMPONENT_CONTRACT_QUALIFICATION.json')['checks']),installed_RPP_software_cases=2,
        installed_RPP_software_attempt=read(O/'SOFTWARE_QUALIFICATION.json')['attempt'],
        qualification_groups=len(NAMES),restore_cap_s=180,task_hard_s=350,campaign_wait_s=360,root_launch_reserve_s=375,
        exact_byte_unchanged_modules=exact_byte_science,physical_response_qualified=False,
        initial_lifecycle_software_timeout_preserved=True,lifecycle_timeout_unique_cause_identified=False,
        review_pending_sha256=guard,execution_lock_idle=True,report='docs/RPCCR_COORDINATED_COMPONENTS_V991_REPORT.md')
    dump(REC/'PREPARATION_AUDIT.json',final)
    dump(REC/'PREPARATION_AUTHORIZATION.json',dict(user_instruction='距离动态验收完成还差什么？下一步开始',
        scope='Prepare exact frozen V990 two-state entry and full software qualification',models_authorized=False,
        new_physical_window_requires_explicit_answer=True,old_V987_status='NOT_PASSED'))
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(status='REVIEW_PENDING',source_revision='V991_PREPARED_AWAITING_PHYSICAL_APPROVAL',
        decision_freeze='experiments/v991_coordinated_components/SOURCE_FREEZE.json',protocol='experiments/v991_coordinated_components/PROTOCOL.md',
        report=final['report'],active_entrypoint=None,active_run=None,active_window=None,next_physical_authorized=False,
        execution_window_closed=True,v991_preparation=final)
    dump(R/'CURRENT_EXPERIMENT.json',state)
    with(R/'RESEARCH_STATUS.md').open('a')as f:
        f.write('\n- V991两状态验证入口准备完成：精确绑定冻结V990协调分配/逐步ALLOCATION与独立混合控制审核，原V958真实t0历史恢复和6083/7814状态顺序保持，原参考/RPP/跟踪/安全/350s时钟不改。11组资格全部过：13因果ARM/18构造绑定与10记录篡改负例、10完整停车、预算/恢复/父子停止/原生循环与未知账目、campaign三例顺序门及peer隔离；实际安装RPP两软件动作终点约.018223/.018127m。首次软件生命周期35s超时及两次campaign夹具错误0模型保留，通信唯一原因未知，未增限时/未改科学。无新物理窗口，旧V987失败和V990冻结保持；拟新90分钟仅原两组件40s+2s首失败停，不自动整路或24，待明确答复。模型积分预测重放训练实机0，REVIEW_PENDING原字节/锁保持。见docs/RPCCR_COORDINATED_COMPONENTS_V991_REPORT.md。\n')
    print(json.dumps(final))

if __name__=='__main__':main()
