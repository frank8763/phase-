"""Zero-model development closure, never report six tasks as fixed24."""
from campaign_context import *
import fcntl

def main():
 assert not(O/'FINALIZED.json').exists();f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
 unchanged=source_ok();rows=d.get('stages',[]);pairs=d.get('development_repeats',{});passed=bool(d.get('passed')and unchanged and len(rows)==6 and len(pairs)==3 and all(r['functional_passed']and r['safety_evidence_passed']for r in rows)and all(p['passed']and p['maximum_complete_state_ctrl_error']<=1e-8 for p in pairs.values()))
 auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
 report=R/'docs/RPCCR_NS_RETAINED_FALLBACK_V1235_REPORT.md'
 lines=['# V1235 南北保留原搜索及有限后备开发','',f'有限开发通过={passed}；停止原因={d["stop_reason"]}。',
 '仅原槽10、槽9和原NS10010002各主任务+成功完整重复。原3000平衡相位搜索保留优先，仅明确耗尽全部扩展无源才一次3000种子共享frontier后备；最坏总6000扩展/两次各120s，原动作相位及全部.022余量/控制/完整停车/反馈连续影子门不变。原成功选择保留，不宣称整体加速或完备/最优。',
 '本批未执行24确认/其他路线，六开发不混原24分母。旧V1230九成功及槽10失败保持原版历史，不追认为新科学24成功。独立90min双时钟，首功能安全证据操作异常即停，冻结后无修补/重跑。','', '|任务|功能|独审|实际原生|重放|错误|','|---|---|---|---:|---:|---|']
 for row in rows:
  r=row.get('result')or{};lines.append(f'|{row["stage"]}|{row.get("functional_passed",False)}|{row.get("safety_evidence_passed",False)}|{r.get("new_actual_native")}|{r.get("own_replay_native")}|{r.get("error")or r.get("functional_failure")}|')
 lines+=['','重复：`'+json.dumps(pairs)+'`。','未执行：'+str(d.get('unexecuted',[]))+'。','准确或未知计数：`'+json.dumps(d.get('physical_counts'))+'`。原普通预测未完整插桩，未知不填0。','CPU2idle/单实例执行锁/GPU隐藏/CPU OSMesa/2GiB/Stage0访问/训练实机0；REVIEW_PENDING恢复。必要原件远端未验证不删；有限开发不是完整动态24验收、任意遮挡/多actor/未知地图/实时/实机/RAS优势证明。']
 report.write_text('\n'.join(lines)+'\n');closed=dict(closed=True,NS_three_state_development_passed=passed,fixed24_executed=False,stop_reason=d['stop_reason'],source_unchanged=unchanged,physical_counts=d.get('physical_counts'),report=str(report.relative_to(R)))
 dump(O/'CLOSED_LEDGER.json',closed);j=read(R/'CURRENT_EXPERIMENT.json');assert j.get('active_run')in[None,str(O.relative_to(R))];j.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1235=closed);dump(R/'CURRENT_EXPERIMENT.json',j)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1235南北有限后备六开发闭批：passed={passed}，stop={d["stop_reason"]}，不自动24；{report.relative_to(R)}。\n')
 excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'};paths={p for root in[C,O,RAW]if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report)
 files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
 dump(O/'FINALIZED.json',dict(closed=True,NS_three_state_development_passed=passed,fixed24_executed=False,source_unchanged=unchanged,manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),guard_original=True,remote_verified=False));print(json.dumps(closed))
if __name__=='__main__':main()
