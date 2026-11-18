from chain_tools import *
import fcntl
def main():
    assert not(O/'FINALIZED.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD;source=source_ok();stages=d.get('stages',[]);passed=bool(d.get('passed')and source and len(stages)==2 and all((s.get('audit')or{}).get('passed')for s in stages));rows=[]
    for s in stages:
        p=s.get('result');rows.append(dict(stage=s['stage'],passed=bool(p and p['passed']),audit_passed=bool((s.get('audit')or{}).get('passed')),new_navigation_native=p.get('new_actual_native')if p else None,historical_controls_used=p.get('historical_controls_used')if p else None,goal_distance_m=p.get('physical',{}).get('goal_distance_m')if p else None,final_stop_executed=p.get('final_stop_executed',False)if p else False,error=p.get('error')if p else'NO_RESULT_UNKNOWN_COUNTS'))
    report=R/'docs/RPCCR_FRESH_CAUSAL_RECOVERY_CHAIN_V1180_REPORT.md';lines=['# V1180 从零态完整因果恢复链','',f'同一已知开发课程原西向东主任务与完整重复通过={passed}；停止原因={d["stop_reason"]}。','',
        '新独立最多90分钟；从规范t0正常反馈导航→本轮实际测距发现→完整发现停车→观测接近→冻结观测库→现场因果证书刷新8+2200→现场联合支持与完整恢复→到达停车。',
        '导航进程禁止读取外部旧实际轨迹、控制和传感；旧预计算库仅在当前原因果观测域/时钟资格通过后激活。恢复参考由当前完整状态、记忆与本轮观测重新传播，不传送旧保存状态。',
        '已知课程开发库来自原任务旧开发；从头实际行驶仍不是新独立种子/泛化确认。',
        '', '| 任务 | 新导航步 | 旧控制使用 | 目标距离m | 完整停 | 功能门 | 独立审核 |','|---|---:|---:|---:|---|---|---|']
    for a in rows:lines.append(f'| {a["stage"]} | {a["new_navigation_native"]} | {a["historical_controls_used"]} | {a["goal_distance_m"]} | {a["final_stop_executed"]} | {a["passed"]} | {a["audit_passed"]} |')
    lines+=['','准确或未知分账：`'+json.dumps(d.get('physical_counts',dict(unknown=True)))+'`。原静态预测核未全部插桩，分析总步数如实unknown；已记录恢复C++/Python/LP另列。独立审核C++步='+str(d.get('independent_audit_analytical_cpp_native','未知'))+'。','未执行：'+str(d.get('unexecuted',[]))+'。']
    for s in stages:
        p=s.get('result')
        if p:lines+=[f'\n{s["stage"]}：实际摘要`{json.dumps(p.get("physical",{}),ensure_ascii=False)}`；恢复分析账`{json.dumps(p.get("known_recovery_counts",{}))}`；原错误`{json.dumps(p.get("error"),ensure_ascii=False)}`。']
    lines+=['','完整重复：`'+json.dumps(d.get('complete_repeat'))+'`。','',
        '本轮仍是明确限定的离线仿真开发；原全部真实安全、控制、重放和停车门保持，首次失败停止。',
        'V1178原169/737即时停车拒绝保持，formal_retained_commit与通用未来W/全后继保证仍false。',
        '不因有限整路通过追认任意扰动/随时停车安全、实机准入、实时性或任意场景；三路线与固定24项未执行。',
        '软件数据替身资格、其重新预测和原准备错误保留；入口替身缺actuator IDs只修替身，实际物理安全门未改。',
        '物理run_phase隔离/单CPU2空闲调度/CPU渲染/GPU隐藏/唯一控制所有者，Stage不访问。训练和实机0。',
        '源、本地清单逐文件SHA回读；远端未核验不清原始证据。']
    report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,fresh_known_course_main_repeat_passed=passed,rows=rows,physical_counts=d.get('physical_counts'),stop_reason=d['stop_reason'],source_unchanged=source,new24=False,three_routes_passed=False,formal_retained_commit=False,report=str(report.relative_to(R)));dump(O/'CLOSED_LEDGER.json',closed)
    current=read(R/'CURRENT_EXPERIMENT.json');assert current.get('active_run')in [None,str(O.relative_to(R))];current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1180=closed,next_scope='Review fresh t0 known-WE causal chain main/repeat; no old controls replayed in navigation. Known-course library development is not independent confirmation; formal retention remains unverified. No automatic three-route24.');dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1180原WE从t0完整因果恢复链闭批：main_repeat={passed}、reason={d["stop_reason"]}、counts={json.dumps(d.get("physical_counts"))}；导航禁读旧实际轨迹控制传感/规范零态/当前源刷新，已知课程开发非独立泛化；formal retained未证，0新三路线24。{closed["report"]}。\n')
    snap=O/'metadata_at_close';snap.mkdir(exist_ok=True)
    for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']:(snap/name).write_bytes((R/name).read_bytes())
    (O/'HANDOFF.md').write_text('# LATEST OVERRIDE — V1180 closed\n\nRead actual report and first refusal or full main/repeat. No restart/source repair/window reset. Known-course fromt0 development only, no three-route24/formal guarantee.\n')
    excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'};paths={p for root in [C,O,R/'runs/v858_nav2_verified/v1180']if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report);size=sum(p.stat().st_size for p in paths);assert size<2*1024**3
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,fresh_known_course_main_repeat_passed=passed,source_unchanged=source,manifest_readback=True,files=len(files),bytes=size,guard_original=True,remote_verified=False,closed_unix=time.time()));print(json.dumps(closed))
if __name__=='__main__':main()
