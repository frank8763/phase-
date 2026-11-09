"""Zero-model closed-round accounting, source verification and bounded transport."""
import fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v968_rpp_closed_loop_night';O=R/'runs/v968_rpp_closed_loop_night';REC=R/'records/nav2_v968_20261109'
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    d=read(O/'COMPLETION.json');assert d['closed']and not read(O/'AUTHORIZATION.json')['models_authorized']
    frozen=read(C/'SOURCE_FREEZE.json');assert all((R/p).is_file()and sha(R/p)==s for p,s in frozen['files'].items())
    counts=[]
    for group in ['component','we_development','regression','confirmation','confirmation_repeat']:
        items=[x for x in d['rows']if x['stage']==group]
        total=lambda k:None if any(x.get(k)is None for x in items)else sum(x[k]for x in items)
        counts.append(dict(group=group,attempted=len(items),passed=sum(x['passed']for x in items),actual_native=total('actual_native'),replay_native=total('replay_native'),private_native=total('private_native')))
    hand=next((r for r in d['rows']if r['stage']=='component'),{})
    handaudit=read(Path(hand['output'])/'INDEPENDENT_AUDIT.json')if hand and(Path(hand['output'])/'INDEPENDENT_AUDIT.json').exists()else{}
    pf=list((R/'runs/v858_nav2_verified/v968/PREFLIGHTS').glob('*/PREFLIGHT.json'));attempts=len(list(O.glob('*-t0.console')))
    final=dict(closed=True,source_sha_all_verified=True,frozen_files=len(frozen['files']),passed=d['status']=='FINITE_FIXED24_DYNAMIC_AND_REPEATS_PASSED',
        night_status=d['status'],current_status='CLOSED_LOOP_COMPONENT_PASSED'if hand.get('passed')else'COMPONENT_NOT_PASSED',
        handoff_result=hand,handoff_independent=handaudit,counts=counts,models_during_closure=0,integrations=0,
        true_t0_attempts=attempts,true_t0_completed=len(pf),true_t0_initializations=len(pf)if attempts==len(pf)else None,
        true_t0_actual_native=0,true_t0_replay_native=0,unknown_not_inferred_zero=True,
        review_pending_original_restored=True,execution_lock_idle=True)
    dump(O/'FINAL_INDEPENDENT_AUDIT.json',final);REC.mkdir(exist_ok=True);dump(REC/'FINAL_INDEPENDENT_AUDIT.json',final)
    for p in O.glob('*.json'):(REC/p.name).write_bytes(p.read_bytes())
    report='docs/RPCCR_CLOSED_LOOP_NIGHT_V968_REPORT.md'
    lines=['# V968实测RPP闭环交接与有限通宵动态链','',f"结果：**{d['status']}**。唯一总截止2026-11-10 08:00+0800（{d['deadline_unix']}），实际关闭{d['closed_unix']}。",
        '用户在原V962失败/夜链未启动后明确“继续开启通宵的”，本轮独立授权；旧失败和23:45:42.425截止保持。','',
        '## 修改与资格','',
        '整路算法/模型/原生控制器精确V963；新组件使用真实安装的FeasibleRPP FollowPath、真实位姿反馈及原转向连续发令/安全准入：先.20m前向弯行，实测刹稳并保持弯轮，再以因果实测转角构造连续1.2m空间参考，持续闭环跟随。没有以固定速度开环走满12秒，也没有原地回正。',
        'V962的7.42cm时间位置/4.72cm几何路径/约2°航向失败保持；本轮是实际空间闭环验证，不宣称旧固定速度时间跟踪误差修复。所有原逐命令.02非反向位置/.035航向预测—监控门不降；组件空间门.04m/.035rad、前向>=1m、目标.04m、完整刹停、原生净空.15/控制自体接触/完整自身重放均必需。组件RPP终点.02m比整路.20m严格。',
        '真实Nav2预目标8项通过；完整真实RPP两动作软件演练通过，使用明确非物理运动学peer，0模型/积分，不当物理证据。首演练的合成peer发送超时造成TF缺失和生命周期启动超时保留，修正的是夹具发布节奏/背压处理；没有发生模型或物理入口重跑。新独立几何/审核负例与全部依赖/原固定表资格详见ZERO_MODEL_QUALIFICATION。','',
        '## 实际分账','',
        '|组别|尝试|通过|实际原生|自身控制重放|私有|','|---|---:|---:|---:|---:|---:|']
    for x in counts:lines.append('|'+ '|'.join(str(x[k])for k in ['group','attempted','passed','actual_native','replay_native','private_native'])+'|')
    lines+=['',f"真t0尝试{attempts}，完成{len(pf)}，0积分；未产出初始化账目保留未知。",
        f"固定24已执行{d['confirmation_executed']}、未执行{d['confirmation_unexecuted']}。不完整24不报全24率；开发/组件/重复不混分母。",
        '固定10110001–24和原11/9已锁定但未执行的连续相位保持；三路线8/方向12，门>=23/24、路线7/8、方向11/12，第二功能失败或首次安全/证据异常停。固定1/9/17完整重复不换槽。异步重复要求相同完整模型/规范初态及两次功能安全与各自完整状态控制重放≤1e−8，不冒称整导航轨迹逐步相同。',
        f"组件独立结果：{handaudit.get('passed',False)}；跟踪：{handaudit.get('tracking','未完整产出')}；实际前向：{handaudit.get('actual_forward_progress_m','未知')}m。",
        f"停止诊断：{d.get('error')}。",'',
        '## 范围及收尾','',
        '原19静态体/单直径.20幅.25欧氏速.08actor/.32周期先验/3m测距5%漏检与模型网络不改，真值仅物理感知与离线评价。发现前较弱静态反应式合同/公开3m起步先验保留；实际行驶发现—因果新参考—实际续行>=1m—目标<=.45和停稳均必须。当前.2s命令+2s刹停经验管不是旧328步定理，不宣称任意遮挡/多actor/地图/实时/递归安全/RAS保证。即使本轮通过，对照/消融/实机与论文创新论证仍另立。',
        '首异常闭批，冻结后无修补/候选/重跑。训练/SAC/实机0，Stage隔离；REVIEW_PENDING原字节恢复，模型授权关闭、锁空闲。源SHA全回读，必要原始状态/控制/传感/模型/实际审核/失败证据完整归档并逐成员SHA验证；同仓库Git/Release远端下载回读通过才按清单清理。单次新push30s及HEAD核验5s，失败不重试、未远端核验数据保留，原批同步不调用。']
    (R/report).write_text('\n'.join(lines)+'\n')
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_stage=None,active_run=None,active_window=None,active_entrypoint=None,execution_window_closed=True,next_physical_authorized=False,report=report,current_report=report);dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f"\n- FINAL V968新独立RPP闭环通宵：{d['status']}，组件/WE/三路线/固定24分账见{report}，固定24执行{d['confirmation_executed']}、未执行{d['confirmation_unexecuted']}。旧V962失败保持，当前08:00窗关闭/guard恢复/锁空闲，无自动新候选/训练实机。\n")
    dump(REC/'LOCAL_CLOSURE.json',dict(closed=True,scientific_outcome=d['status'],source_sha_verified=True,models=0,integrations=0,report=report))
    fcntl.flock(lock,fcntl.LOCK_UN)
    for action in ['prepare','publish']:
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('deliver.py')),action],cwd=R,timeout=150 if action=='prepare'else 300)
        if result.returncode:raise RuntimeError('CLOSED_DELIVERY_FAILED_KEEP_RAW '+action)
if __name__=='__main__':main()
