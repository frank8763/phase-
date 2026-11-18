"""Full fixed24 closure, precise denominators and complete original evidence."""
from campaign_context import *
from gates import main_gate,final_gate
import fcntl
def main():
    assert not(O/'FINALIZED.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
    rows=d['stages'];gate=main_gate(rows);pairs=d.get('complete_repeats',{});unchanged=source_ok();passed=bool(d['passed']and unchanged and final_gate(rows,pairs))
    assert not any(a.get('parent_inherited')for a in rows)
    auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
    report=R/'docs/RPCCR_CAUSAL_TIME_WINDOW_FIXED24_V1275_REPORT.md'
    lines=['# V1275 因果安全时间窗固定24确认','',f'完整确认全门通过={passed}；停止原因={d["stop_reason"]}。',
        'WE/NS保留原已资格成功分支；EW统一保留原6源成功对象，只有正常完整6源无解后，对单个已暴露课程代表控制形状从当前实测状态/记忆/原因果域全原生重传播40个起步等待，按完整安全储备slack固定选择。无按slot/种子设置等待、无未来传感或动态真值入规划。',
        '代表轨迹只是已知课程提案；原池已暴露，不称未见泛化、通用规划、任意运动障碍或算法全面优势。V1271原18/19两个失败相位的真实主与精确完整重复及原17成功分支数组保持是开发资格，不导入本确认分母。',
        '新独立10800秒双时钟/当前boot，原24清单相位不变，全部24真实t0后原序24新主，主全门后固定1/9/17完整重复。0旧确认或开发导入。原所有失败/旧截止保持，不运行中修源、换池或替补。',
        '原主>=23/24/每路线>=7/8/方向>=11/12及所有安全证据门、三个精确完整重复必需。首次安全/源/模型/控制/真值/状态/覆盖/操作证据异常停；限定完整安全停车、完整自身重放与独审的功能失败容许一次，第二停。未执行不算失败或完整24成功率。',
        '原实际每原生净空.15/自体接触穿透未知0/完整合法ctrl及速率/固定静态体和无积分外根写/全qpos/qvel/ctrl/mocap重放1e-8门保持；名义额外22mm，停车入口及终点另保留60.235mm响应刚体储备。全等待与余程完整2200尾，实际测距发现、刹停、真实传感重建、新路线、续行1m及目标.45全链须。',
        '合同是已登记19静态体/单小actor/原3m测距与漏检/已知地图课程，发现前是较弱静态反应式合同。训练/实机0，不声称实时、递归或全扰动管证明。','',
        '主门：`'+json.dumps(gate)+'`。','', '|任务|功能|独审|实际原生|自身回放|目标剩余m|错误/拒绝|','|---|---|---|---:|---:|---:|---|']
    for row in rows:
        r=row.get('result')or{};p=r.get('physical')or{}
        lines.append(f'|{row["stage"]}|{row.get("functional_passed")}|{row.get("safety_evidence_passed")}|{r.get("new_actual_native")}|{r.get("own_replay_native")}|{p.get("goal_distance_m")}|{r.get("error")or r.get("functional_failure")}|')
    lines+=['','固定完整重复：`'+json.dumps(pairs)+'`。','未执行：`'+json.dumps(d.get('unexecuted',[]))+'`。',
        '本批准确或未知计数：`'+json.dumps(d.get('physical_counts'))+'`。全部普通预测未完整插桩保持unknown，不能填0。开发父计数另列：`'+json.dumps(d.get('parent_physical_counts'))+'`。',
        '持续固定24临时8GiB/256MiB储备，单CPU2物理/唯一Phase锁，数学四低优先级spawn CPU2–5/GPUhidden，Stage源模型结果进程完全隔离。必要原件远端SHA与下载回读前保留。当前指针REVIEW_PENDING、截止后仅零模型收尾。']
    report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,stop_reason=d['stop_reason'],physical_counts=d.get('physical_counts'),report=str(report.relative_to(R)),confirmation_rows_imported=0)
    dump(O/'CLOSED_LEDGER.json',closed);j=read(R/'CURRENT_EXPERIMENT.json');assert j.get('active_run')in[None,str(O.relative_to(R))]
    j.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1275=closed);dump(R/'CURRENT_EXPERIMENT.json',j)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1275因果时间窗固定24闭批：passed={passed}，主{gate["successes"]}/{gate["executed"]}已执行，完整分母={gate["full24_executed"]}，stop={d["stop_reason"]}；0旧确认开发导入，{report.relative_to(R)}。\n')
    excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'}
    paths={p for root in[C,O,RAW]for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report)
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True))
    assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),guard_original=True,remote_verified=False));print(json.dumps(closed))
if __name__=='__main__':main()
