"""Close reviewable software preparation, without opening physical authority."""
import ast,fcntl,hashlib,json,time
from pathlib import Path
C=Path(__file__).parent;R=C.resolve().parents[1];O=R/'runs/v982_precise_recovery_gate';REC=R/'records/nav2_v982_20261110'
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=sha(R/'REVIEW_PENDING');assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    names=['ZERO_MODEL_ENTRY_QUALIFICATION.json','BINDING_QUALIFICATION.json','PEER_ISOLATION_QUALIFICATION.json','COMPONENT_CONTRACT_QUALIFICATION.json','SOFTWARE_QUALIFICATION.json']
    for name in names:assert read(O/name)['passed']
    tasks=read(C/'TASKS.json');old=read(R/'experiments/v979_state_recovery_physical/TASKS.json')[:2]
    compare=['case_id','seed','phase','dynamic','goal_xy','goal_yaw','wall_limit_s','brake_s','stage','slot','fixed_state_index','origin_native_tick','origin_sim_time']
    assert len(tasks)==2 and all(all(a[k]==b[k]for k in compare)for a,b in zip(tasks,old))
    scientific=['state_reference.py','command_tube.py','cycle_backup.py','steering_continuity.py','navigation_policy.py','shaping_audit.py','A_forward.yaml']
    for name in scientific:assert sha(C/name)==sha(R/'experiments/v979_state_recovery_physical'/name)
    for name in ['tracking.py','transaction.py','independent_tracking.py','closure.py','native_loop.py']:assert sha(C/name)==sha(R/'experiments/v981_tracking_evidence_closure'/name)
    for path in C.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
    assert 'v979_physical_gate=done'not in(C/'campaign.py').read_text()
    assert not(O/'AUTHORIZATION.json').exists()and not(O/'USER_APPROVAL.json').exists()and not(O/'ROUND_WINDOW.json').exists()
    frozen=read(C/'SOURCE_FREEZE.json')
    for name,digest in frozen['files'].items():assert sha(R/name)==digest
    software=read(O/'SOFTWARE_QUALIFICATION.json')
    cases=[x['report']for x in software['results']]
    final=dict(status='PREPARED_AWAITING_NEW_BOUNDED_PHYSICAL_APPROVAL',source_qualification_passed=True,
               fixed_components=2,installed_RPP_software_cases=2,software_attempt_selected=software['attempt'],
               old_failed_preparation_attempts_retained=True,physical_ready=False,models_authorized=False,
               models=0,actual_native=0,private_native=0,replay_native=0,new_navigation_samples=0,
               new24=0,training=0,hardware=0,source_freeze_sha256=sha(C/'SOURCE_FREEZE.json'),frozen_files=len(frozen['files']),
               inherited_scientific_algorithm='V977',checking_and_closure='V981_exact',
               proposed_root_seconds=5400,proposed_task_seconds=40,finite_stop_seconds=2,
               source_integrity_verified=True,review_pending_sha256=guard,execution_lock_idle=True,
               report='docs/RPCCR_PRECISE_RECOVERY_V982_REPORT.md',no_model_window_opened=True)
    REC.mkdir(exist_ok=True)
    for name in ['BASELINE_BINDING_RED.json','PREPARATION_FAILURES.json',*names]:(REC/name).write_bytes((O/name).read_bytes())
    dump(REC/'PREPARATION_AUDIT.json',final)
    lines=['# V982：两固定恢复状态的执行链准备','',
           '**源码与零模型准备完成；物理窗口未开启。动态整路尚未通过。**',
           '',
           '两个原固定状态：原西向东10010001/.6573753567727383，native6083和7814。仅提出新的独立最多90分钟验证，逐项40秒+原2秒停稳，第一失败停止。此批不含整路、重复、三路线或24项。V979及旧窗口保持封账。',
           '',
           '原V977参考构造、控制、RPP参数、模型/传感/actor、安全门不改；V981同一参考的.5mm在线守卫、独立密采样终审和有界收尾已实际绑定到新物理入口。补核全半秒停稳/编码器与原actor元数据，原.04m/.035rad/.15实际/.155预测/1e-8重放门不降。',
           '',
           '| 保存状态 | 真实安装RPP的软件动作 | 终点误差m | 独立航向上界rad | 虚拟后端最大消息间隔s |',
           '|---|---:|---:|---:|---:|']
    for i,row in enumerate(cases):lines.append(f"| {i} | {row['passed']} | {row['endpoint_distance_m']:.9f} | {row['independent_dense_tracking']['maximum_heading_upper_rad']:.9f} | {row['separate_process_peer']['maximum_send_gap_s']:.6f} |")
    lines+=['','这里使用真实Nav2/RPP和新生产Bridge，后端是明确的独立非物理自行车夹具、synthetic scan；不是MuJoCo物理通过，也不是实际转向滞后已解决。实际车辆完整轨迹/接触/控制/自身重放仍须下一物理关验证。','',
            '准备失败全部保留：入口演练的legacy authority导入顺序错误；第一次软件启动2秒DDS服务发现超时和空轨迹报告次生错误；第二次第一状态通过、第二状态在.202808s触发原.2s观测门。受控GIL对照复现同解释器生产线程.253s停顿、独立解释器约.0051s；仅将测试后端分进程后两状态通过，原.2s门未放宽。该对照不能唯一归因原次生时序故障。','',
            '资格包括实际worker/guard/audit绑定、两因果历史及准确ARM起点正负例、模型授权拒绝、实际半秒尾/伪造编码器/actor负例、两个真实安装RPP软件动作和干净退出。旧1562冻结文件未修改。13个历史物理输入已按远端inventory SHA锁定，共6,626,859字节，等待批准后才按需恢复；本轮没有下载全历史。','',
            f"源码冻结{len(frozen['files'])}文件；REVIEW_PENDING原字节、锁空闲、模型/物理积分/私有/重放/训练实机均0。新批必须收到明确独立90分钟组件批准才可首次初始化；没有后台导航。准备及后续物理闭批共享一次最终Git推送，尚未消耗；旧V981同步不重试。"]
    (R/final['report']).write_text('\n'.join(lines)+'\n')
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(status='REVIEW_PENDING',source_revision='V982_PREPARED_AWAITING_PHYSICAL_APPROVAL',
        decision_freeze='experiments/v982_precise_recovery_gate/SOURCE_FREEZE.json',protocol='experiments/v982_precise_recovery_gate/PROTOCOL.md',
        report=final['report'],active_entrypoint=None,active_run=None,active_window=None,next_physical_authorized=False,execution_window_closed=True,v982_preparation=final)
    dump(R/'CURRENT_EXPERIMENT.json',state)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V982执行链准备完成：V977算法控制不改、V981在线/独立密采样和有界收尾实际绑定；两真实安装RPP独立非物理peer全过，endpoint.016269/.018121m，半秒停稳/编码器/actor负例全过。导入顺序、2sDDS发现/空轨迹次生报告、.202808s旧thread peer时序失败全保留，生产.2s门不降；测试后端单独解释器资格完成，不冒称车辆物理通过。原两固定native6083/7814、提出新90分钟仅两组件/首失败停，无自动整路24。源码已冻/模型0/无新root窗/guard锁保持，待明确新有界物理批准；旧失败保持，见docs/RPCCR_PRECISE_RECOVERY_V982_REPORT.md。\n')
    print(json.dumps(final))
if __name__=='__main__':main()
