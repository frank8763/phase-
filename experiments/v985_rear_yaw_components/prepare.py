"""Freeze reviewable two-state entry qualification, without physical authority."""
import ast,fcntl,hashlib,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v985_rear_yaw_components';REC=R/'records/nav2_v985_20261110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=sha(R/'REVIEW_PENDING');assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    names=['ZERO_MODEL_ENTRY_QUALIFICATION.json','BINDING_QUALIFICATION.json','COMPONENT_CONTRACT_QUALIFICATION.json','SOFTWARE_QUALIFICATION.json']
    assert all(read(O/n)['passed']for n in names)
    assert not any((O/n).exists()for n in ['USER_APPROVAL.json','ROUND_WINDOW.json','AUTHORIZATION.json','CAMPAIGN_CLAIM.json'])
    old=read(R/'experiments/v982_precise_recovery_gate/SOURCE_FREEZE.json');files={}
    for name,h in old['files'].items():assert sha(R/name)==h;files[name]=h
    servo=read(R/'experiments/v984_decoupled_yaw_servo/SOURCE_FREEZE.json')
    for name,h in servo['files'].items():assert sha(R/name)==h;files[name]=h
    for p in [R/'experiments/v982_precise_recovery_gate/SOURCE_FREEZE.json',R/'experiments/v984_decoupled_yaw_servo/SOURCE_FREEZE.json']:
        files[str(p.relative_to(R))]=sha(p)
    original=read(R/'experiments/v982_precise_recovery_gate/TASKS.json');tasks=read(C/'TASKS.json')
    same=['case_id','seed','phase','dynamic','goal_xy','goal_yaw','wall_limit_s','brake_s','stage','slot','fixed_state_index','origin_native_tick','origin_sim_time']
    assert len(tasks)==2 and all(all(a[k]==b[k]for k in same)for a,b in zip(tasks,original))
    for name in ['state_reference.py','command_tube.py','cycle_backup.py','steering_continuity.py','navigation_policy.py','shaping_audit.py','A_forward.yaml','tracking.py','transaction.py','independent_tracking.py','closure.py','native_loop.py']:
        assert sha(C/name)==sha(R/'experiments/v982_precise_recovery_gate'/name),'UNINTENDED_SCIENTIFIC_OR_TIMING_CHANGE '+name
    for p in C.iterdir():
        assert not p.is_symlink()
        if p.is_file()and p.name!='SOURCE_FREEZE.json':
            if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
            files[str(p.relative_to(R))]=sha(p)
    for name in [*names,'SEED_HISTORY_0.json','SEED_HISTORY_1.json']:
        p=O/name;files[str(p.relative_to(R))]=sha(p)
    frozen=dict(final=True,awaiting_explicit_physical_approval=True,models_before_freeze=0,integrations_before_freeze=0,
        scientific_servo_source='experiments/v984_decoupled_yaw_servo/vehicle_control.py',files=files)
    path=C/'SOURCE_FREEZE.json'
    if path.exists():assert read(path)==frozen,'ALREADY_FROZEN_SOURCE_CHANGED'
    else:dump(path,frozen)
    REC.mkdir(exist_ok=True)
    for name in names:(REC/name).write_bytes((O/name).read_bytes())
    binding=read(O/'BINDING_QUALIFICATION.json');entry=read(O/'ZERO_MODEL_ENTRY_QUALIFICATION.json');contract=read(O/'COMPONENT_CONTRACT_QUALIFICATION.json')
    final=dict(status='PREPARED_AWAITING_NEW_BOUNDED_PHYSICAL_APPROVAL',source_qualification_passed=True,
        models=0,actual_native=0,private_native=0,replay_native=0,new_navigation_samples=0,new24=0,training=0,hardware=0,
        models_authorized=False,physical_ready=False,no_model_window_opened=True,fixed_components=2,
        proposed_root_s=5400,component_wall_s=40,component_stop_s=2,
        frozen_files=len(files),source_freeze_sha256=sha(path),old_v982_frozen_files_unchanged=len(old['files']),
        old_v982_status='NOT_PASSED',servo_exact_V984=True,actual_worker_switch_and_audit_bound=True,
        entry_checks=len(entry['checks']),binding_checks=len(binding['checks']),binding_negative_cases=len(binding['negative_cases']),
        complete_stop_contract_checks=len(contract['checks']),installed_RPP_software_cases=2,
        metadata_proxy_is_not_model_audit=True,physical_response_qualified=False,
        review_pending_sha256=guard,execution_lock_idle=True,report='docs/RPCCR_REAR_YAW_COMPONENTS_V985_REPORT.md')
    dump(REC/'PREPARATION_AUDIT.json',final)
    dump(REC/'PREPARATION_AUTHORIZATION.json',dict(user_instruction='下一步开始',scope='concrete next-gate preparation',models_authorized=False,
        old_batch='V982_CLOSED_NOT_PASSED',new_physical_window_requires_explicit_answer=True))
    cases=read(O/'SOFTWARE_QUALIFICATION.json')['results']
    lines=['# V985：新后轮偏航反馈的两状态验证准备','',
        '**执行入口、审核和零模型准备完成；新的物理窗口尚未开启。**','',
        '原两个保存起点固定为V974西向东10010001/相位.6573753567727383的native6083与7814，逐项40秒行驶＋原2秒有限停车，首项所有功能与安全审核通过后才第二项。拟采用新独立最多90分钟，首失败或截止即停；没有整路、重复、三路线、24项或通宵任务。V982失败与旧截止保持。','',
        '先以原V958映射从真实t0逐原生恢复完整历史，在原起点比对全状态/控制后才构造冻结V984控制器。只复制原控制记忆；模型、车体状态、时钟和积分计数保持。SETUP同时记录历史与活动控制版本，原真实t0绑定证据仍如实指向V958，不伪装成V984在历史前缀中已通过。','',
        '新增控制切换证据和所有新步的实际控制/反馈记录。独立审核将历史五类完整状态与原轨迹重新比对，再使用实际前原生状态重建反馈输入和混合旧/新电机控制到1e-8。即使完整FollowPath未完成，新增控制审核仍独立保存失败或通过，不替代原完整功能判定。','',
        f"源码入口{len(entry['checks'])}项、控制绑定{len(binding['checks'])}项、{len(binding['negative_cases'])}个独立记录篡改负例和完整停车/编码器/actor合同{len(contract['checks'])}项均通过。元数据/数组夹具重建6083旧控制+24新控制误差6.94e-17；不是模型或车辆物理验证。",'',
        '| 原保存状态 | 实际安装RPP软件动作 | 终点误差m | 航向上界rad |','|---|---:|---:|---:|']
    for row in cases:
        q=row['report'];lines.append(f"| {row['index']} | {q['passed']} | {q['endpoint_distance_m']:.9f} | {q['independent_dense_tracking']['maximum_heading_upper_rad']:.9f} |")
    lines+=['','两个动作均使用明确的独立非物理peer/synthetic scan，没有测试新控制器的实际力学响应。真实Nav2/RPP入口软件通过不能作为物理跟踪通过。原V977参考、RPP参数、精细在线守卫和独立审核、.04m/.035rad/.155预测/.15实际、完整控制尾/停车/全状态重放门保持。','',
        f"冻结{len(files)}个来源，其中原V982的{len(old['files'])}文件和V984候选字节核验不变。仅13个原始输入SHA预锁定，批准后按需恢复约6.6MB；未下载全历史。模型/积分/导航/预测/重放/训练实机0，REVIEW_PENDING原字节、执行锁空闲。","",'本准备阶段必要源码/结果在同仓库Release核验，原始资格缓存随后按清单清理；仅本地提交，V985唯一Git推送留给最终物理闭批。需要新的明确有界物理答复后才能首次初始化；原V982按首失败封账，不能沿用其90分钟窗口。']
    (R/final['report']).write_text('\n'.join(lines)+'\n')
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(status='REVIEW_PENDING',source_revision='V985_PREPARED_AWAITING_PHYSICAL_APPROVAL',
        decision_freeze='experiments/v985_rear_yaw_components/SOURCE_FREEZE.json',protocol='experiments/v985_rear_yaw_components/PROTOCOL.md',
        report=final['report'],active_entrypoint=None,active_run=None,active_window=None,next_physical_authorized=False,execution_window_closed=True,v985_preparation=final)
    dump(R/'CURRENT_EXPERIMENT.json',state)
    line='\n- V985准备完成：原V958完整历史恢复后在原6083/7814起点切换冻结V984，仅控制记忆移交/物理状态时钟不变；新增逐步反馈与实际电机证据、独立原历史五类状态和混合控制重建。13入口/18绑定/5记录负例/10停车合同检查通过，两个实际安装RPP非物理peer软件动作通过，端点.017207/.018151m；不冒称新映射物理响应通过。原V9821637文件与V984全部冻源保持；新模型/积分/导航/预测/重放/训练实机0，guard/锁保持，无新窗。提出新的90分钟仅两组件/40s+2s/首失败停，不自动整路24；待明确答复。见docs/RPCCR_REAR_YAW_COMPONENTS_V985_REPORT.md。\n'
    if 'V985准备完成：'not in(R/'RESEARCH_STATUS.md').read_text():
        with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(line)
    print(json.dumps(final))
if __name__=='__main__':main()
