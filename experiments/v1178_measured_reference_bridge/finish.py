from pathlib import Path
import json,hashlib,fcntl,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1178_measured_reference_bridge'
def read(p):return json.loads(p.read_text())if p.exists()else None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    assert not(O/'FINALIZED.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');a=read(O/'FINAL_INDEPENDENT_AUDIT.json');f=read(C/'SOURCE_FREEZE.json');source=bool(f and all(sha(R/n)==h for n,h in f['files'].items()));assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    regression=read(O/'MEASURED_REGRESSION.json');stop=read(O/'REFERENCE_STOP_AUDIT.json');bridge=read(O/'BRIDGE_CONCLUSION.json');passed=bool(a and a['passed']and source)
    report=R/'docs/RPCCR_MEASURED_REFERENCE_BRIDGE_V1178_REPORT.md';lines=['# V1178 新实测误差与整条恢复参考接续','',f'保存审查/回读通过={passed}。本轮软件分析；新物理、模型、训练0，不重跑V1177。',
        '', 'V1177已完成三组件主任务及完整重复。本轮只将三个主任务的17600实际单步记录作为新开发误差数据，',
        '三个重复的17600步单独用于确定性证据，不能再次充当独立数据扩充。模型系数、参考、目标与安全门不改。',
        '', '## 新实测响应回建','', '| 组件 | 原实际记录 | 原轨迹最大位置/航向/轮角误差 | 单步轮角速率残差最大 |','|---|---:|---|---:|']
    if regression:
        for r in regression['cases']:lines.append(f'| {r["component"]} | {r["actual_records"]} | {r["maximum_actual_trajectory_response"]} | {r["observed_residual_abs_max"][7]:.9g} |')
        lines.extend(['','逐真实前状态传播一次，应用控制与控制记忆、Python/C++完整状态核对；原状态残差与可逆运动学创新保存。',
            '“模型速率峰值.6043、实际.5847”是二者响应差异，不是要求实车达到模型峰值的物理可达性结论。',
            '新有限残差最大仍不是通用W；不能据新组件通过就把formal retention的缺失字段填True。'])
    if stop:
        lines.extend(['','## 整条原参考的停车储备扫描','',
            f'原V1163参考5885步，每8步及末边界共{stop["total"]}个完整状态/记忆，按原原因果动态外包络和绝对时钟各预测2200步停车。',
            f'通过{stop["passed"]}，拒绝{stop["rejected"]}；四核总耗时{stop["wall_s"]:.3f}秒，Cpp解析{stop["analytical_cpp_native"]}步。',
            '这些是旧名义参考的完整前缀后继测试，没有新增真实碰撞/导航样本。',
            f'最低停车raw={stop["worst"]["minimum_raw"]:.12f}米，原门.24353421020226934。'])
        if stop['first_refused']:
            r=stop['first_refused'];lines.extend(['',f'首个拒绝在参考相对native {r["offset"]}，停车尾第{r["worst_tail_native"]}步最差，原因{r["minimum_kind"]}，raw={r["minimum_raw"]:.12f}。',
                f'静态下界最小{r["static_min"]:.12f}，原因果动态下界最小{r["dynamic_min"]:.12f}；完整控制/身体/停车门分别见REFERENCE_STOP_AUDIT，不能称车跟踪失败。',
                '这表明“完整恢复参考能到目标”并不自动提供每一途中状态的即时2200刹停资格。',
                '不得因此再启动普通stop-anywhere入口，也不能降低raw/身体/末速门隐藏拒绝。'])
    if bridge:lines.extend(['','## 完整恢复与缺口','',
        f'完整名义恢复参考：{bridge["complete_nominal_recovery_passed"]}；raw最低{bridge["minimum_reference_raw"]:.12f}米，目标距离上界{bridge["goal_upper"]:.12f}米；全周期终端raw{bridge["terminal_full_cycle_raw"]:.12f}。',
        f'所有名义边界立即停车：{bridge["stop_anywhere_nominal_all_passed"]}。',
        '完整参考与停车两类证书的语义分别保存，不可相互替代。',
        '后续需要完整恢复后备的状态/记忆后继包含与模型误差合同，或者明确预注册有限经验开发范围、',
        '保留真实每原生安全/完整尾/重放门，并诚实区分有限实测与形式保证；不能暗改既有formal gate。'])
    if d and d['error']:lines.extend(['','异常：`'+str(d['error'])+'`；原证据保留，不重启。'])
    lines.extend(['','独立审核回建保存创新、控制记忆、时钟、最差与首拒绝的完整停车数组及原因果支持表达式；',
        '回算仍使用同一动力学模型，不冒称第二种独立物理系统或形式化完整可达性求解器。',
        'REVIEW_PENDING保持、源及本地SHA回读，当前指针关闭。没有打开物理窗/追加整路/三路线24，原件远端未核验不清理。'])
    report.write_text('\n'.join(lines)+'\n');summary=dict(closed=True,software_audit_passed=passed,new_actual_error_records=regression['main_records']if regression else None,nominal_stop_queries=stop['total']if stop else None,nominal_stop_refused=stop['rejected']if stop else None,complete_nominal_recovery_passed=bridge['complete_nominal_recovery_passed']if bridge else None,
        analytical_python_native=d.get('analytical_python_native')if d else None,analytical_cpp_native=d.get('analytical_cpp_native')if d else None,independent_audit_cpp_native=a['analytical_cpp_native']if a else None,physical_native=0,models=0,future_support_verified=False,physical_window_open=False,report=str(report.relative_to(R)));dump(O/'LEDGER.json',summary)
    p=R/'CURRENT_EXPERIMENT.json';j=read(p);assert j['active_run']in [None,'runs/v1178_measured_reference_bridge'];j.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=summary['report'],latest_v1178=summary,next_scope='V1178 measured error/reference bridge complete. Read nominal full recovery vs stop-at-every-boundary distinction and exact refused states. Do not repeat old components or launch ordinary stop-anywhere executor blindly; missing formal recovery/error contract remains explicit, no new physics window.');dump(p,j)
    with(R/'RESEARCH_STATUS.md').open('a')as h:h.write(f'\n- V1178新实测17600主记录（重复另计）固定模型单步/创新回建及原5885参考每8完整2200停车四核扫描闭批：audit={passed}、nominal_stop={summary["nominal_stop_queries"]}/refused={summary["nominal_stop_refused"]}，完整名义恢复={summary["complete_nominal_recovery_passed"]}；Python/Cpp={summary["analytical_python_native"]}/{summary["analytical_cpp_native"]}，审核Cpp={summary["independent_audit_cpp_native"]}、新物理0。全参考/即时停语义区分，缺失futureW/formal后继不填True，无新物理窗，不重复已过组件。{summary["report"]}。\n')
    snap=O/'metadata_at_close';snap.mkdir(exist_ok=True)
    for n in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']:(snap/n).write_bytes((R/n).read_bytes())
    (O/'HANDOFF.md').write_text('# LATEST OVERRIDE — V1178 closed\n\nRead report/BRIDGE_CONCLUSION/REFERENCE_STOP_AUDIT/MEASURED_REGRESSION/independent audit. New finite actual errors do not prove universal W. Distinguish complete recovery from arbitrary immediate braking; do not restart old components or a stop-anywhere controller if scan refused. No physical window opened.\n')
    paths={p for p in O.rglob('*')if p.is_file()and p.name not in ['LOCAL_MANIFEST.json','FINALIZED.json','relay.console']};paths.update(p for p in C.glob('*')if p.is_file());paths.add(report);files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};assert sum(v['bytes']for v in files.values())<2*1024**3;dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']for n,v in files.items());dump(O/'FINALIZED.json',dict(closed=True,software_audit_passed=passed,source_unchanged=source,manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),physical_native=0,models=0,closed_unix=time.time()));print(json.dumps(summary));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
