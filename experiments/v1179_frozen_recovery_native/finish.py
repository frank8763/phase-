"""Zero-model immutable close and source/data SHA readback."""
from recovery_tools import *
import fcntl
def main():
    assert not(O/'FINALIZED.json').exists(),'DO_NOT_OVERWRITE_CLOSED_MANIFEST'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD;source=source_ok();rows=[]
    for s in d.get('stages',[]):
        r=s.get('result');a=s.get('audit');rows.append(dict(stage=s['stage'],passed=bool(r and r['passed']),audit_passed=bool(a and a['passed']),historical_native=r.get('historical_reconstruction_native')if r else None,new_suffix_native=r.get('new_actual_native')if r else None,replay_native=r.get('own_replay_native')if r else None,goal_distance_m=r.get('goal_distance_m')if r else None,final_stop_executed=r.get('final_stop_executed',False)if r else False,error=r.get('error')if r else'UNKNOWN_INFLIGHT_COUNTS'))
    passed=bool(d.get('passed')and source and len(rows)==2 and all(r['passed']and r['audit_passed']for r in rows)and d.get('complete_repeat',{}).get('passed'))
    report=R/'docs/RPCCR_FROZEN_RECOVERY_NATIVE_V1179_REPORT.md';lines=['# V1179 原保存任务完整恢复实测','',f'本轮闭批；原保存态恢复主任务及完整重复通过={passed}；停止原因={d["stop_reason"]}。','',
        '单一原西向东10010001/相位.6573753567727383，19静态体/原动态actor/模型网络控制不变。',
        '从规范零态逐原生重建原34723控制；历史与原全qpos/qvel/ctrl/mocap/传感核对，不传送保存状态。',
        '之后固定V1163参考5885步，必要时原前向捕获<=600步，始终追加完整2200实际停车。',
        '', '| 任务 | 旧控制重建 | 新恢复步 | 完整控制重放 | 目标距离m | 完整停 | 功能门 | 独立审核 |',
        '|---|---:|---:|---:|---:|---|---|---|']
    for r in rows:lines.append(f'| {r["stage"]} | {r["historical_native"]} | {r["new_suffix_native"]} | {r["replay_native"]} | {r["goal_distance_m"]} | {r["final_stop_executed"]} | {r["passed"]} | {r["audit_passed"]} |')
    lines+=['','准确或未知分账：`'+json.dumps(d.get('physical_counts',dict(unknown=True)))+'`。独立审核Cpp步='+str(d.get('independent_audit_analytical_cpp_native','未知'))+'；未执行='+str(d.get('unexecuted',[]))+'。']
    for s in d.get('stages',[]):
        r=s.get('result')
        if r:
            p=r.get('physical',{});lines+=[f'\n{s["stage"]}：最低实际净空{p.get("minimum_actual_clearance_m")}m；坏接触{p.get("bad_contacts")}；最大实际/影子模型响应误差{r.get("maximum_model_response_error")}；实际/时间参考位姿误差{r.get("maximum_reference_pose_error")}。']
            if r.get('error'):lines+=['原错误：`'+json.dumps(r['error'],ensure_ascii=False)+'`。']
    lines+=['','这是一项明确限定的离线物理仿真策略资格，不是已准入的实体控制器。',
        'V1178原737边界169个即时停车证书拒绝保持；完整恢复能到达与任意时刻可立即安全停车不同。',
        '原RETAINED_RECOVERY_V1门未修改；formal_retained_commit及universal_model_error_support_verified均为false。',
        '不能把有限到达追认为全后继保证，也不把预测拒绝称作实际碰撞。失败前缀若未完整停则明确false。',
        '原每原生.15/自体/静态固定/无root外写/ctrl与slew/身体.13,.03,.16/响应.04,.035,.015/参考位姿.04,.035/目标距离+.08<=.45/完整重放1e-8保留。',
        '从旧失败态复验不计作全新从头路线或独立泛化样本；没有三路线、新24确认、训练或实机。',
        '物理单CPU2单所有者/原隔离与锁/CPU软件渲染；不访问Stage。新90分钟壁钟+单调钟+boot截止不重置旧窗。',
        '源和本地证据SHA回读；远端未核验，原件保留。']
    report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,finite_saved_task_recovery_pair_passed=passed,rows=rows,physical_counts=d.get('physical_counts'),source_unchanged=source,stop_reason=d['stop_reason'],new24=False,three_routes_passed=False,formal_retained_commit=False,universal_model_error_support_verified=False,report=str(report.relative_to(R)));dump(O/'CLOSED_LEDGER.json',closed)
    current=read(R/'CURRENT_EXPERIMENT.json');assert current.get('active_run')in [None,str(O.relative_to(R))];current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1179=closed,next_scope='Review finite actual saved-source recovery and measured failure or complete repeat. No automatic fresh route/three-route24; formal successor admission remains unverified.');dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1179原保存34723状态完整恢复闭批：pair={passed}、reason={d["stop_reason"]}、counts={json.dumps(d.get("physical_counts"))}；原源/模型/安全门保持，有限离线策略实测不追认任意时刻停车或全后继证明，不计新三路线24。{closed["report"]}。\n')
    snap=O/'metadata_at_close';snap.mkdir(exist_ok=True)
    for n in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']:(snap/n).write_bytes((R/n).read_bytes())
    (O/'HANDOFF.md').write_text('# LATEST OVERRIDE — V1179 closed\n\nRead report/COMPLETION/CLOSED_LEDGER. No native restart, frozen repair or old deadline renewal. Finite saved-task test, not fresh route/three-route24 or formal successor guarantee.\n')
    excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'};roots=[C,O,R/'runs/v858_nav2_verified/v1179'];paths={p for root in roots if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report);size=sum(p.stat().st_size for p in paths);assert size<2*1024**3
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True,active_console_excluded=True));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,finite_saved_task_recovery_pair_passed=passed,source_unchanged=source,manifest_readback=True,files=len(files),bytes=size,guard_original=True,remote_verified=False,closed_unix=time.time()));print(json.dumps(closed));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
