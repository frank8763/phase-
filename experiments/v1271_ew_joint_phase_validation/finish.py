"""Zero-model closure and source/member readback; originals retained."""
from campaign_context import *
import fcntl
def main():
    assert not(O/'FINALIZED.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
    unchanged=source_ok();rows=d.get('stages',[]);pairs=d.get('development_repeats',{})
    passed=bool(d.get('passed')and unchanged and len(rows)==4 and all(r['functional_passed']and r['safety_evidence_passed']for r in rows)and set(pairs)=={'slot18','slot19'}and all(a['passed']for a in pairs.values()))
    report=R/'docs/RPCCR_EW_ACTUAL_OBSERVATION_V1271_REPORT.md'
    lines=['# V1271 EW槽17实际观测交接开发','',f'主任务及完整重复全门通过={passed}；停止原因={d["stop_reason"]}。',
        '仅原18/19联合开发，科学修订为完整安全观察位置交接后，使用本轮实际雷达刷新原因果域再准入全程。原静态驾驶/发现/完整刹停、模型、课程与物理门不改；若新域仍拒绝，保持已证停车并完整重放/独审。',
        '新90分钟双时钟为助手按既有有界惯例选择；旧V1248失败和旧截止不延，前16旧成功不计本批新确认。18–24与固定确认重复均未在本批执行。','',
        '|任务|功能|独审|实际原生|自身重放|错误/拒绝|','|---|---|---|---:|---:|---|']
    for row in rows:
        r=row.get('result')or{};lines.append(f'|{row["stage"]}|{row.get("functional_passed",False)}|{row.get("safety_evidence_passed",False)}|{r.get("new_actual_native")}|{r.get("own_replay_native")}|{r.get("error")or r.get("functional_failure")}|')
    lines+=['','完整重复：`'+json.dumps(pairs)+'`。','未执行：'+str(d.get('unexecuted',[]))+'。','实际与未知计数：`'+json.dumps(d.get('physical_counts'))+'`。普通预测未完整插桩，未知不填0。',
        'CPU2idle/单实例/CPU OSMesa/GPU隐藏/2GiB，训练/Stage/实机0。REVIEW_PENDING恢复；原件远端未核验不删。有限已暴露课程开发不证明未见泛化、任意遮挡、多actor、实时或RAS优势。']
    report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,joint_phase_main_repeat_development_passed=passed,fixed24_executed=False,stop_reason=d['stop_reason'],source_unchanged=unchanged,physical_counts=d.get('physical_counts'),report=str(report.relative_to(R)))
    dump(O/'CLOSED_LEDGER.json',closed);current=read(R/'CURRENT_EXPERIMENT.json');assert current.get('active_run')in[None,str(O.relative_to(R))]
    current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1271=closed);dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1271原18/19联合开发实际观测交接主/条件完整重复闭批：passed={passed}，stop={d["stop_reason"]}，不自动24；{report.relative_to(R)}。\n')
    excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'}
    paths={p for root in[C,O,RAW]if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report)
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True))
    assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,joint_phase_main_repeat_development_passed=passed,fixed24_executed=False,source_unchanged=unchanged,manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),guard_original=True,remote_verified=False));print(json.dumps(closed))
if __name__=='__main__':main()
