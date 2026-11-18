from route_tools import *
import fcntl
def main():
    assert not(O/'FINALIZED.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
    unchanged=source_ok();stages=d.get('stages',[]);passed=bool(d.get('passed')and unchanged and len(stages)==6 and all((s.get('audit')or{}).get('passed')for s in stages))
    rows=[]
    for s in stages:
        r=s.get('result')or{};rows.append(dict(stage=s['stage'],passed=r.get('passed',False),audit_passed=(s.get('audit')or{}).get('passed',False),native=r.get('new_actual_native'),replay_native=r.get('own_replay_native'),goal_distance_m=r.get('physical',{}).get('goal_distance_m'),error=r.get('error')))
    report=R/'docs/RPCCR_THREE_ROUTE_ENTRY_V1184_REPORT.md'
    lines=['# V1184 同版本三路线反馈开发', '',f'同版本三路线主任务及完整重复通过={passed}；停止原因={d["stop_reason"]}。','',
        '固定顺序NS主重复、EW主重复、WE主重复；WE虽V1180通过，本轮仍在统一冻结版本重新验证，旧结果不填充本轮未执行。',
        '所有导航从规范t0，原正常行驶/真实测距发现/完整发现停车；NS/EW在当前实测完整状态、记忆及本轮传感支持重新传播固定开发参考；WE保持V1180链。EW起点为已登记北移.10米课程。',
        'NS姿态反馈；EW已资格有符号速度执行器反馈及完整时间姿态监测，不能泛称新倒行姿态控制器。课程库来自旧开发，不是独立泛化。','',
        '|任务|主功能|独立审核|实际原生|重放|距目标m|','|---|---|---|---:|---:|---:|']
    for r in rows:lines.append(f'|{r["stage"]}|{r["passed"]}|{r["audit_passed"]}|{r["native"]}|{r["replay_native"]}|{r["goal_distance_m"]}|')
    lines+=['','未执行：'+str(d.get('unexecuted',[]))+'。','准确或未知分账：`'+json.dumps(d.get('physical_counts',dict(unknown=True)))+'`。原普通预测未全部插桩，unknown不填0。','完整重复：`'+json.dumps(d.get('complete_repeats',{}))+'`。',
        '首次安全/功能/证据异常停，不运行冻结后修补；旧窗口与错误保持。formal retained/未来W/全后继仍未证，不声称实时或实机准入。新24未执行，0训练实机；单CPU2空闲调度/CPU渲染/Stage不访问。','',
        '本地必要原始证据及来源清单SHA逐文件回读；远端未核验不删除。']
    for r in rows:
        if r['error']:lines+=['','原错误：`'+json.dumps(r['error'],ensure_ascii=False)+'`。']
    report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,same_version_three_routes_passed=passed,rows=rows,physical_counts=d.get('physical_counts'),source_unchanged=unchanged,stop_reason=d['stop_reason'],new24=False,formal_retained_commit=False,report=str(report.relative_to(R)))
    dump(O/'CLOSED_LEDGER.json',closed)
    current=read(R/'CURRENT_EXPERIMENT.json');assert current.get('active_run')in[None,str(O.relative_to(R))];current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1184=closed);dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1184三路线统一反馈批闭：passed={passed}、reason={d["stop_reason"]}，全部来源与原始证据本地回读；旧成功不填本轮未执行，0新24/训练/实机。{report.relative_to(R)}。\n')
    excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'}
    paths={p for root in[C,O,R/'runs/v858_nav2_verified/v1184']if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report);size=sum(p.stat().st_size for p in paths);assert size<2*1024**3
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,same_version_three_routes_passed=passed,source_unchanged=unchanged,manifest_readback=True,files=len(files),bytes=size,remote_verified=False,guard_original=True,closed_unix=time.time()));print(json.dumps(closed))
if __name__=='__main__':main()
