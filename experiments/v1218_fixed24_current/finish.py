from campaign_context import *
from gates import main_gate,final_gate
import fcntl
def main():
    assert not(O/'FINALIZED.json').exists();f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
    auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
    unchanged=source_ok();rows=d.get('stages',[]);gate=main_gate(rows);passed=bool(d.get('passed')and unchanged and final_gate(rows,d.get('complete_repeats',{})))
    report=R/'docs/RPCCR_FIXED24_CONFIRMATION_V1218_REPORT.md'
    lines=['# V1218 固定24项当前版本复验','',f'固定24确认通过={passed}；停止原因={d["stop_reason"]}。',
        '科学规划与控制保持V1217：WE当前状态双分支及反馈/连续影子准入，NS/EW保持原策略，三路线六开发成功不混本确认分母。原10060001–24相位/顺序不换；旧版已暴露前8项，故是当前方法固定基准复验，不称全新未见样本。EW保持已声明起点北移.10米课程。',
        f'已实际开始主导航={gate["executed"]}，全链成功={gate["successes"]}，失败={gate["failures"]}，完整24分母={gate["full24_executed"]}；全分母率={gate["full_denominator_success_rate"]}。',
        '完整门：`'+json.dumps(gate)+'`。','', '|任务|功能|安全证据独审|实际原生|重放|拒绝或错误|','|---|---|---|---:|---:|---|']
    for row in rows:
        r=row.get('result')or{};reason=(r.get('functional_failure')or{}).get('reason')or str(r.get('error'))
        lines.append(f'|{row["stage"]}|{row.get("functional_passed",False)}|{row.get("safety_evidence_passed",False)}|{r.get("new_actual_native")}|{r.get("own_replay_native")}|{reason}|')
    lines+=['','未执行任务：'+str(d.get('unexecuted',[]))+'。','固定重复比较：`'+json.dumps(d.get('complete_repeats',{}))+'`。','准确或未知账目：`'+json.dumps(d.get('physical_counts',dict(unknown=True)))+'`。普通预测总数未全部插桩，unknown不填0。',
        '仅两类原库时钟/原因果域激活拒绝，可在已实际停稳且完整原生安全/控制/自身重放/独立审核通过后计功能失败；第二功能失败停止。所有其他异常立即停止，不冻结后改算法/门/种子/任务/重跑。',
        '原V1185失败、V1209暴露两槽开发与V1217三路线成功分别保留；0训练实机，单CPU2空闲调度/CPU软件渲染/Stage无访问。',
        'formal retained、通用未来误差W/全后继未证；不能从有限通过推出任意遮挡/多actor/地图泛化/实时/实机/RAS优势。',
        '本地必要原始证据/来源清单逐文件SHA回读，远端未核验不删；临时上限2GiB。']
    report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,physical_counts=d.get('physical_counts'),source_unchanged=unchanged,stop_reason=d['stop_reason'],report=str(report.relative_to(R)),old_pool_exposed=True)
    dump(O/'CLOSED_LEDGER.json',closed)
    j=read(R/'CURRENT_EXPERIMENT.json');assert j.get('active_run')in[None,str(O.relative_to(R))];j.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1218=closed);dump(R/'CURRENT_EXPERIMENT.json',j)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1218固定24当前版本复验闭批：passed={passed}、main={gate["executed"]}/24开始/{gate["successes"]}成功，stop={d["stop_reason"]}；原暴露池非新未见样本，未执行不算失败分母，无自动修补/新池/训练。{report.relative_to(R)}。\n')
    excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'};paths={p for root in[C,O,R/'runs/v858_nav2_verified/v1218']if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report);size=sum(p.stat().st_size for p in paths);assert size<2*1024**3
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,manifest_readback=True,files=len(files),bytes=size,remote_verified=False,guard_original=True,closed_unix=time.time()));print(json.dumps(closed))
if __name__=='__main__':main()
