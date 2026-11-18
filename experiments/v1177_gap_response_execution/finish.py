"""Zero-model immutable close; no scientific retry or sync side effects."""
from gap_tools import *
import fcntl,gzip
def main():
    assert not(O/'FINALIZED.json').exists(),'DO_NOT_OVERWRITE_ARCHIVE'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
    tasks=read(C/'TASKS.json');source=source_ok();stages=d.get('stages',[]);rows=[]
    for s in stages:
        result=s.get('result');audit=s.get('audit');rows.append(dict(stage=s['stage'],functional_passed=bool(result and result['passed']),evidence_audit_passed=bool(audit and audit['passed']),observed_feature_covered=result.get('measured_feature_covered')if result else None,actual_native=result.get('new_actual_native')if result else None,replay_native=result.get('own_replay_native')if result else None,error=result.get('error')if result else'NO_RESULT_COUNTS_UNKNOWN',functional_failure=result.get('functional_failure')if result else None))
    fully=bool(d.get('passed')and len(rows)==6 and all(r['functional_passed']and r['evidence_audit_passed']for r in rows)and source)
    report=R/'docs/RPCCR_GAP_RESPONSE_EXECUTION_V1177_REPORT.md';lines=['# V1177 固定三组件实际响应与完整重复','',f'本轮已闭批：六任务全部主门和审核/重复通过={fully}；停止原因：{d["stop_reason"]}。',
        '', '新独立90分钟窗口在第一车辆初始化前锁定，旧全部截止和失败保持。',
        '仅rate/lateral/low三个固定静态NS组件，各自规范初态、主任务成功才完整重复；没有新输入搜索。',
        '横向.13请求是明示新静态激励，原实际.13身体速度门不降低；原整路.12参考未改。',
        '', '| 任务 | 实际步 | 自己控制重放步 | 功能门 | 独立证据审核 | 观测峰值达到模型见证 |',
        '|---|---:|---:|---|---|---|']
    for r in rows:lines.append(f'| {r["stage"]} | {r["actual_native"]} | {r["replay_native"]} | {r["functional_passed"]} | {r["evidence_audit_passed"]} | {r["observed_feature_covered"]} |')
    lines.extend(['','准确/未知分账：`'+json.dumps(d.get('physical_counts',dict(unknown=True)))+'`；独立审核新Cpp解析步：'+str(d.get('independent_audit_analytical_cpp_native','未知'))+'。',
        '未执行：'+str(d.get('unexecuted',[]))+'。'])
    for s in stages:
        r=s.get('result')
        if r:
            p=r.get('physical',{});lines.extend(['',f'任务{s["stage"]}：实际最低净空{p.get("minimum_actual_clearance_m")}米/坏接触{p.get("bad_contacts")}；最大响应误差{r.get("maximum_response_error")}；实际速率/侧速峰值{r.get("observed_rate_lateral")}。'])
            if r.get('functional_failure')or r.get('error'):lines.append('原拒绝或异常：`'+json.dumps(r.get('functional_failure')or r.get('error'),ensure_ascii=False)+'`。')
    lines.extend(['','## 原门与资源','',
        '原完整自体、每原生.15、静态固定、无root外写、合法ctrl/slew、body(.13,.03,.16)、',
        '名义响应(.04,.035,.015)、完整2200停及全状态自己控制重放<=1e-8均保留。',
        '每8实际测量边界完整停车证书；离线独立停证审核使用四核独立进程、同源数组/计数。',
        '物理初始化、实际与重放只run_phase隔离/CPU2/执行锁单所有者；不访问Stage进程或资料。',
        '数据替身资格、元数据隔离探针与真实物理成功分别记账；冷四核入口资格另消耗140800解析步、0物理。',
        '错误输入拒绝列表以QUALIFICATION.json为准；两次新入口导入失败和worker派生断言均为0模型、原日志保留。',
        '', '## 科学边界','',
        '“模型预测峰值复现”与“实际响应在原误差界内”不同。二者冻结前已明确分开，',
        '实际峰值未达到某个模型数值时如实标记observed_feature_covered=false，不把此数值强加为新物理安全门；',
        '即使全部组件通过，也不声称实际未来误差支持已在整个状态空间被证明。',
        '组件未到原动态目标，独立静态初态不能拼成一条到达轨迹，重复不是独立泛化样本。',
        '全参考行驶误差管/首停入集/真实模型误差合同仍需后续接通，不能称动态整路、三路线或24验收。',
        '首失败后不补输入、改增益、开替代任务或延长截止；原记录及必要源/证据待远端核验前保留。'])
    report.write_text('\n'.join(lines)+'\n');summary=dict(closed=True,all_three_response_pairs_passed=fully,rows=rows,source_unchanged=source,physical_counts=d.get('physical_counts'),stop_reason=d['stop_reason'],original_dynamic_goal_passed=False,three_routes_passed=False,new24_executed=False,future_error_support_verified=False,report=str(report.relative_to(R)));dump(O/'CLOSED_LEDGER.json',summary)
    current=read(R/'CURRENT_EXPERIMENT.json');assert current.get('active_run')in [None,str(O.relative_to(R))]
    current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=summary['report'],latest_v1177=summary,next_scope='V1177 actual static response components closed; read exact first refusal or full pairs. No stimulus search or old deadline restart. Distinguish actual response qualification from observed feature hull/future support, then update model error/complete-reference proof. No automatic dynamic three-route24.');dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1177固定三个静态响应及条件重复物理轮闭批：all_three_pairs={fully}、reason={d["stop_reason"]}，counts={json.dumps(d.get("physical_counts"))}；真实/元数据/替身/四核审核分账、旧窗保留、原门不降。实际峰值覆盖模型值单列、非事后放宽门；0新动态目标/三路线24。{summary["report"]}。\n')
    snap=O/'metadata_at_close';snap.mkdir(exist_ok=True)
    for n in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']:(snap/n).write_bytes((R/n).read_bytes())
    (O/'HANDOFF.md').write_text('# LATEST OVERRIDE — V1177 closed\n\nRead actual report/COMPLETION/CLOSED_LEDGER and each actual audit. No restart/frozen repair/new window. Original guard restored, no worker should remain. Static response only, not dynamic goal/three routes/24 or universal W.\n')
    roots=[C,O,R/'runs/v858_nav2_verified/v1177'];paths={p for root in roots if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in ['LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console']};paths.add(report)
    size=sum(p.stat().st_size for p in paths);assert size<2*1024**3
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True,active_driver_outputs_excluded=True));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,all_three_response_pairs_passed=fully,source_unchanged=source,manifest_readback=True,files=len(files),bytes=size,guard_original=True,remote_verified=False,closed_unix=time.time()));print(json.dumps({k:v for k,v in summary.items()if k!='rows'}));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
