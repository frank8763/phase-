from campaign_context import *
from gates import main_gate,final_gate
import fcntl
def main():
    assert not(O/'FINALIZED.json').exists();f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
    auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
    unchanged=source_ok();rows=d.get('stages',[]);gate=main_gate(rows);passed=bool(d.get('passed')and unchanged and final_gate(rows,d.get('complete_repeats',{})))
    report=R/'docs/RPCCR_FIXED24_CONFIRMATION_V1228_REPORT.md'
    lines=['# V1228 南北当前状态恢复与条件固定24复验','',f'固定24确认通过={passed}；停止原因={d["stop_reason"]}。',
        'NS唯一科学修订：不再把旧成功的固定控制时序应用于新停车状态；从当前实测全状态、控制记忆、绝对时钟和本次原因果雷达域，使用已有有限控制空间搜索生成全目标来源。原控制器、3000扩展上限、21等待相位、完整2200停车尾、反馈和连续影子及全部安全门不降；新增名义余量门REQUIRED+0.022，末端按原25mm合同完成，不追额外12mm，实际当前全状态与连续影子必须完整预检捕获+停车。WE/EW模块保持V1222同字节科学，继承原独立开发资格，不当新样本。EW保持已登记起点北移0.10米课程。',
        '固定顺序先暴露槽9主与完整重复、原NS主与完整重复，四项全门及两重复误差<=1e-8通过后，才条件进入24真实t0、原顺序24主和固定1/9/17重复；旧V1222的8成功不混本确认分母。',
        f'统一原硬截止2026-11-16 20:30+08，不延期。已开始确认主任务={gate["executed"]}，成功={gate["successes"]}，完整24分母={gate["full24_executed"]}；全分母率={gate["full_denominator_success_rate"]}。',
        '这是已暴露固定课程复验，非新未见样本或泛化证明。首次开发功能、安全证据或操作异常立即停止；确认第二合格功能拒绝停止，任何安全证据异常首次停止。运行中不改源码/任务/门。',
        '完整门：`'+json.dumps(gate)+'`。','', '|任务|功能|安全证据独审|实际原生|重放|拒绝或错误|','|---|---|---|---:|---:|---|']
    for row in rows:
        r=row.get('result')or{};reason=(r.get('functional_failure')or{}).get('reason')or str(r.get('error'))
        lines.append(f'|{row["stage"]}|{row.get("functional_passed",False)}|{row.get("safety_evidence_passed",False)}|{r.get("new_actual_native")}|{r.get("own_replay_native")}|{reason}|')
    lines+=['','未执行任务：'+str(d.get('unexecuted',[]))+'。','固定重复比较：`'+json.dumps(d.get('complete_repeats',{}))+'`。','准确或未知账目：`'+json.dumps(d.get('physical_counts',dict(unknown=True)))+'`。普通预测总数未全部插桩，unknown不填0。',
        '原库时钟/原因果域激活拒绝或完整执行当前获证停车，可在已实际停稳且完整原生安全/控制/自身重放/独立审核通过后计功能失败；第二功能失败停止。所有其他异常立即停止，不冻结后改算法/门/种子/任务/重跑。',
        '原V1185失败、V1209暴露两槽开发与V1217三路线成功分别保留；0训练实机，单CPU2空闲调度/CPU软件渲染/Stage无访问。',
        'formal retained、通用未来误差W/全后继未证；不能从有限通过推出任意遮挡/多actor/地图泛化/实时/实机/RAS优势。',
        '本地必要原始证据/来源清单逐文件SHA回读，远端未核验不删；临时上限2GiB。']
    report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,physical_counts=d.get('physical_counts'),source_unchanged=unchanged,stop_reason=d['stop_reason'],report=str(report.relative_to(R)),old_pool_exposed=True)
    dump(O/'CLOSED_LEDGER.json',closed)
    j=read(R/'CURRENT_EXPERIMENT.json');assert j.get('active_run')in[None,str(O.relative_to(R))];j.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1228=closed);dump(R/'CURRENT_EXPERIMENT.json',j)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1228固定24当前版本复验闭批：passed={passed}、main={gate["executed"]}/24开始/{gate["successes"]}成功，stop={d["stop_reason"]}；原暴露池非新未见样本，未执行不算失败分母，无自动修补/新池/训练。{report.relative_to(R)}。\n')
    excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'};paths={p for root in[C,O,R/'runs/v858_nav2_verified/v1228']if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report);size=sum(p.stat().st_size for p in paths);assert size<2*1024**3
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,manifest_readback=True,files=len(files),bytes=size,remote_verified=False,guard_original=True,closed_unix=time.time()));print(json.dumps(closed))
if __name__=='__main__':main()
