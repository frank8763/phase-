"""Report and operation snapshots after two distinct closed component stages."""
import fcntl
import hashlib
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v960_hold_response_closure'
REC=ROOT/'records/nav2_v955_v960_20261109'
REPORT='docs/RPCCR_RESPONSE18_V955_V960_REPORT.md'


def read(p):return json.loads(p.read_text())
def dump(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def main():
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=hashlib.sha256((ROOT/'REVIEW_PENDING').read_bytes()).hexdigest()
    assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    old=read(ROOT/'runs/v956_damped_response18/COMPLETION.json');new=read(ROOT/'runs/v959_hold_response18/COMPLETION.json')
    previous=read(ROOT/'runs/v957_response18_closure/FINAL_INDEPENDENT_AUDIT.json');audit=read(OUT/'FINAL_INDEPENDENT_AUDIT.json')
    assert old['closed']and new['closed']and previous['evidence_integrity_verified']and audit['evidence_integrity_verified']
    for folder in ['v956_damped_response18','v959_hold_response18']:assert not read(ROOT/'runs'/folder/'AUTHORIZATION.json')['models_authorized']
    rows=audit['rows'];tasks=read(ROOT/'experiments/v959_hold_response18/TASKS.json')
    initial=[];model_sha=[]
    for row in rows:
        folder=ROOT/tasks[row['index']]['output']/'physics'
        model_sha.append(hashlib.sha256((folder/'scene_model.mjb').read_bytes()).hexdigest())
        with np.load(folder/'INITIAL_STATE.npz')as f:initial.append({key:f[key].copy()for key in f.files})
    same_initial=all(set(d)==set(initial[0])and all(np.array_equal(d[k],initial[0][k])for k in d)for d in initial)
    same_model=len(set(model_sha))==1
    dump(OUT/'CANONICAL_INITIAL_MODEL_CHECK.json',dict(passed=same_initial and same_model,initial_state_arrays_exactly_equal=same_initial,
        model_mjb_sha256_equal=same_model,model_hashes=model_sha,models=0,integrations=0))
    assert same_initial and same_model,'CANONICAL_MODEL_OR_INITIAL_STATE_MISMATCH'
    REC.mkdir(exist_ok=True)
    for name in ['v955_damped_stopped_alignment','v956_damped_response18','v957_response18_closure',
        'v958_hold_steering_contract','v959_hold_response18','v960_hold_response_closure']:
        folder=ROOT/'runs'/name
        for p in folder.glob('*.json'):
            if p.name in {'AUTHORIZATION.json','AUTHORIZATION.before_close.json','USER_INSTRUCTION.json','ZERO_MODEL_QUALIFICATION.json',
                'COMPLETION.json','FINAL_INDEPENDENT_AUDIT.json','CANONICAL_INITIAL_MODEL_CHECK.json'}:
                (REC/(name+'_'+p.name)).write_bytes(p.read_bytes())
    (REC/'OLD_SELECTIVE_RESTORE_RECEIPT.json').write_bytes((ROOT/'runs/v954_restore_cache/RESTORE_RECEIPT.json').read_bytes())
    status='PASSED_RESPONSE18_ONLY'if audit['passed']else'NOT_PASSED'
    minimum=min(r['minimum_actual_clearance_m']for r in rows)
    maximum_position=max(r['position_max_m']for r in rows if r['position_max_m']is not None)
    maximum_heading=max(r['heading_max_rad']for r in rows if r['heading_max_rad']is not None)
    start=datetime.fromtimestamp(new['started_unix'],timezone(timedelta(hours=8))).isoformat()
    deadline=datetime.fromtimestamp(new['deadline_unix'],timezone(timedelta(hours=8))).isoformat()
    lines=['# V955–V960：18项命令—刹停响应资格','',
        f"2026-11-09。V956 **NOT_PASSED**保留；新V959 **{status}**，完成{len(rows)}/18项，独立审核结论{audit['passed']}。",
        '**只涉及固定平台响应组件；新整路、动态验收、新24、实际转向连续性交接均未执行。**','',
        '## 先失败的V956，不追认或混算','',
        '用户要求继续18项后，新V955取消移动层额外yaw转向反馈，并尝试刹稳后连续回正及后轮零均值差动抑制偏航。22项控制/49项实际执行与记录软件检查通过，均0车辆模型；它们不是物理资格。',
        'V956独立窗21:15:59.109783–22:45:59.109783，首3项通过，第4项右弯停车的回正阶段实测yaw-rate达到−.03014721993rad/s，越过原.03停稳门；21:17:03.762首失败封账。差动补偿在本次参数下未维持原停稳门，不放宽小数阈值。',
        '4次模型初始化、1545实际原生步：前3项1260实际/1260完整自身控制重放；第4项285实际未做自身控制重放，14项未执行。最低实际.203608947m、坏接触0。不能称1545步全部通过重放。',
        '原campaign实际总数为null，原文件保留。独立审计以285保存状态/285命令/285根状态审核一致，精确复现下一次Adapter.compute异常；冻结Vehicle.step的compute语句序号1在native积分语句序号5之前。因此额外第286积分没有发生，零模型补核得1545准确总账，不把未知写0。','',
        '## 用户明确选择新的停车定义','',
        '用户随后明确选择“保持轮角刹停，转向交接另验（推荐）”。原V90918项资格针对运动后完整刹停；V950后来为直线交接增加了每项末轮角必须归零。新V958/V959前瞻性移除此附加中立完成门，编码器继续完整记录；V956原.03停稳失败并未因删轮角门被救回，V953/V956仍失败。',
        'V958移动用Ackermann运动学与原纵向PI；停车保持现有转角并将驱动目标刹至0，不执行原地回正或额外差动补偿。对应10项零模型检查、V95950项执行/记录检查通过；合成数据只演练实际420步worker和评估器，7560夹具循环不计物理积分。',
        '接口分工参考[ROS2 steering controller官方文档](https://control.ros.org/jazzy/doc/ros2_controllers/steering_controllers_library/doc/userdoc.html)：运动学映射与路径跟踪分开。这里仍为本仓库适配器，不冒称实际部署官方插件或获得文献保证。','',
        '## 新V959实际结果','',
        f'一次新窗口：{start}至{deadline}，唯一截止{new["deadline_unix"]}，旧V956时间不复用。',
        '原18任务/顺序/420步时间表/同原WE10010001相位保留；原19静态实体、actor直径/幅值/速度、原测距噪声/漏检及模型不改。反向输入是固定平台响应资格，不是普通导航倒行授权。',
        '门保持：位置误差非反向.02m/反向.04m，航向.035rad，全原生平速.13m/s/角速.16rad/s，半秒后平速及角速.03；净空.15、坏/未知/自体接触0、完整自体、控制界与速率、静态体固定/无积分外根写、全状态控制自身重放≤1e−8。末轮角如实记录，不能把非零轮角当可立即交接直线。','',
        '|索引|预热速度/角速|后续|位置残差m|航向残差rad|最低净空m|实测/重放|结果|',
        '|---|---|---|---|---|---|---|---|']
    for r in rows:
        t=tasks[r['index']];producer=new['rows'][r['index']]
        lines.append(f"|{r['index']}|{t['warm'][0]:+.1f}/{t['warm'][1]:+.6f}|{t['transition']}|{r['position_max_m']:.9f}|{r['heading_max_rad']:.9f}|{r['minimum_actual_clearance_m']:.9f}|{r['exact_actual_native']}/{r['own_replay_native']}|{'PASS'if r['component_passed']else'FAIL'}|")
    lines+=['',f"新V959：{new['models_initialized']}初始化，实际{audit['actual_native']}、完整自身控制重放{audit['replay_native']}、私有0、未执行{new['unexecuted_cases']}。最低实际净空{minimum:.9f}m；最大位置残差{maximum_position:.9f}m、最大航向残差{maximum_heading:.9f}rad，所有源/原因果控制重建及逐原生数据独立回读。",
        f"同批初态全部原生state数组精确相同、MJB SHA全部相同：{model_sha[0]}。同一课程/同一初态的18固定输入，不是18独立导航样本或场景泛化。",
        '完整自身控制重放属于执行证据，不是重新运行导航算法的独立完整重复。全18准入不证明任意中间速度/曲率、连续换向、任意负载实时性或更宽状态集合。','',
        '## 接下来的边界','',
        '下一关是实测轮角连续的前进交接：新参考起始曲率应匹配实际转向，沿前进路径逐渐调整；不能停车后强令转角归零，也不能直接换直线参考。V958的几何起始接口仅必要条件，不是完整可执行走廊/物理证书。实际前进≥1m和完整目标到达仍须独立验证，本轮不自动启动。',
        '旧18附加回正协议未通过；新18已明确改变停车定义，两者不混分母。新动态24、算法比较、消融、实机和论文结论均未由本批完成。训练/SAC/实机0，Stage隔离。','',
        '## 收尾与记录','',
        'REVIEW_PENDING原字节恢复，模型授权关闭、执行锁空闲。原窗口、失败、原null账目与补核证明都保留。必要源码、报告、元数据由Git保存，完整实际/失败证据由同仓库Release保留；records/nav2_v955_v960_20261109提供回执。只有远端资产和解压成员SHA全回读通过，才按清单清理临时缓存。']
    (ROOT/REPORT).write_text('\n'.join(lines)+'\n')
    current=read(ROOT/'CURRENT_EXPERIMENT.json')
    current.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True,
        report=REPORT,next_physical_authorized=False,requires_user_review_before_next_experiment=True,
        last_observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat())
    current['v959_response18'].update(closed=True,status=status,models=new['models_initialized'],actual_native=audit['actual_native'],
        replay_native=audit['replay_native'],private_native=0,passed_responses=sum(r['component_passed']for r in rows),unexecuted=new['unexecuted_cases'],
        independent_audit_passed=audit['passed'],steering_neutral_not_required=True,physical_handoff_qualified=False,report=REPORT)
    dump(ROOT/'CURRENT_EXPERIMENT.json',current)
    dump(REC/'LOCAL_CLOSURE.json',dict(closed=True,scientific_outcome=status,v956_failed_preserved=True,v956_actual_native=1545,
        v956_replay_native=1260,v956_unreplayed_native=285,v959_actual_native=audit['actual_native'],v959_replay_native=audit['replay_native'],
        review_pending_sha256=guard,execution_lock_idle=True,navigation=0,new24=0,handoff=0,new_models_during_close=0))
    print(json.dumps(dict(status=status,minimum_clearance=minimum,maximum_position=maximum_position,maximum_heading=maximum_heading,report=REPORT)))


if __name__=='__main__':main()
