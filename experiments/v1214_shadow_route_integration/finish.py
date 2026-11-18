"""Bounded zero-model completion report and immutable evidence readback."""
from worker_context import *
import fcntl

def main():
    assert not(O/'FINALIZED.json').exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    source=all(sha(R/n)==h for m in ['WORKER_FREEZE.json','CAMPAIGN_FREEZE.json']for n,h in read(C/m)['files'].items())
    passed=bool(d['passed']and source and len(d['stages'])==6 and len(d['repeats'])==3 and all(s.get('audit',{}).get('physical_audit_complete')for s in d['stages'])and all(x['passed']for x in d['repeats'].values()))
    a=read(O/'USER_AUTHORIZATION.json');a.update(authorized=False,closed=True);dump(O/'USER_AUTHORIZATION.json',a)
    rows=[]
    for s in d['stages']:
        q=s.get('result',{});p=q.get('physical',{});rows.append(dict(task=s['task_id'],passed=q.get('passed'),audit=s.get('audit',{}).get('passed',False),actual=q.get('new_actual_native'),replay=q.get('own_replay_native'),goal=p.get('goal_distance_m'),clearance=p.get('minimum_actual_clearance_m'),error=q.get('error')))
    report=R/'docs/RPCCR_THREE_ROUTE_COMPATIBILITY_V1214_REPORT.md'
    lines=['# V1214 同版本三路线兼容性回归','',f'六次全门通过={passed}；停止原因={d["stop_reason"]}。','',
        'WE新增V1213固定工作量双分支搜索及完整反馈/连续影子准入，目标交接不重置影子状态或记忆，原终审保持；NS/EW保持原V1184策略。原控制、场景、感知与安全门不变，EW保持(4,-1.9)声明课程。','',
        '|任务|功能|独审|实际|重放|目标距m|最低实际净空m|','|---|---|---|---:|---:|---:|---:|']
    for x in rows:lines.append('|{task}|{passed}|{audit}|{actual}|{replay}|{goal}|{clearance}|'.format(**x))
    lines+=['','未执行：'+str(d['unexecuted'])+'。','完整重复：`'+json.dumps(d['repeats'])+'`。',
        '准确物理计数：`'+json.dumps({k:d.get(k)for k in ['models','new_actual_native','own_replay_native']})+'`；普通解析总数unknown，内部工厂次数unknown；已记录组件计算仅在原result单列，不当全部分析计数。',
        '本批先WE主重复，再NS主重复和EW主重复。每任务从规范t0、真实测距发现、完整停车、原因果恢复、续行与最终到达/停稳；独立原生/控制/净空/自体/完整重放审核及主重复误差<=1e-8必须。','',
        '所有旧失败/截止保持；本批不自动24、不新池、不训练实机，不声称未见泛化、任意时刻刹停、formal retained/W/全后继、实时或RAS优势。原始证据远端待核验，不提前删除。']
    report.write_text('\n'.join(lines)+'\n')
    closed=dict(closed=True,same_version_three_routes_passed=passed,source_unchanged=source,stop_reason=d['stop_reason'],rows=rows,repeats=d['repeats'],models=d['models'],new_actual_native=d['new_actual_native'],own_replay_native=d['own_replay_native'],new24=False,report=str(report.relative_to(R)),remote_verified=False)
    dump(O/'CLOSED_LEDGER.json',closed)
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,automatic_additional_simulation=False,latest_v1214=closed,latest_report=closed['report']);dump(R/'CURRENT_EXPERIMENT.json',current)
    with (R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1214三路线兼容性回归闭批：passed='+str(passed)+'、reason='+d['stop_reason']+'；旧V1209两暴露失败槽开发4/4保持，新24未启动。'+closed['report']+'。\n')
    snapshots=O/'CLOSURE_METADATA_SNAPSHOT';snapshots.mkdir()
    for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']:(snapshots/name).write_bytes((R/name).read_bytes())
    excluded={'FINALIZED.json','LOCAL_MANIFEST.json','LOCAL_READBACK.json','finalize.console'}
    paths={p for root in[C,O,RAW]if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded}
    paths.add(report)
    files={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p))for p in sorted(paths)}
    assert sum(v['bytes']for v in files.values())<LIMIT
    dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True))
    assert all((R/n).stat().st_size==v['bytes']and sha(R/n)==v['sha256']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,same_version_three_routes_passed=passed,source_unchanged=source,manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),new24=False,remote_verified=False,closed_unix=time.time()))
    print(json.dumps(closed))

if __name__=='__main__':main()
