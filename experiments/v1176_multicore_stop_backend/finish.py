from pathlib import Path
import json,hashlib,fcntl,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1176_multicore_stop_backend'
def read(p):return json.loads(p.read_text())if p.exists()else None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    assert not(O/'FINALIZED.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');r=read(O/'RESULT.json');a=read(O/'FINAL_INDEPENDENT_AUDIT.json');f=read(C/'SOURCE_FREEZE.json');source=bool(f and all(sha(R/n)==h for n,h in f['files'].items()));assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    passed=bool(r and r['passed']and a and a['passed']and source)
    config=dict(user_authorized_multicore_cpu=True,user_gpu_permission=True,validated_max_analytical_workers=4 if passed else 0,validated_cpu_ids=[2,3,4,5]if passed else[],scheduler='SCHED_IDLE',nice=19,threads_per_worker=1,physical_controller_instances=1,physical_execution_lock_required=True,parallel_analytical_jobs_under_one_parent_lock=True,
        analytical_backend_module='experiments/v1176_multicore_stop_backend/backend.py',requires_per_process_library=True,selected_for_benchmarked_workload=r['selected_backend_for_this_workload']if passed else'unverified',gpu_computation_enabled=False,gpu_reason='Optional permission; no qualified CUDA implementation of current scalar stateful C++ kernel, no new GPU/engine port or training task.',other_process_access=False,exclusive_core_or_gpu_ownership_claimed=False)
    dump(C/'NEXT_ROUND_RESOURCE_CONFIG.json',config)
    report=R/'docs/RPCCR_MULTICORE_STOP_BACKEND_V1176_REPORT.md';lines=['# V1176 多核CPU停车预测后端','',f'2026-11-15用户授权多核CPU及可选GPU。多核一致性及保存审核通过：{passed}。',
        '', '本轮只使用原V1175三个固定软件输入包的独立保存边界，不加科学候选，不启动实际模型、导航或训练。',
        '物理执行仍保持一个车辆/控制所有者；每条状态链按原顺序推进。',
        '独立完整2200步停车预测和离线审核可使用进程并行，各进程有独立C++全局计数器。',
        '没有将该内核直接改为同库多线程，避免计数串扰。旧冻结源与run_phase隔离入口不改。']
    if passed:
        s=r['serial_timing'];p=r['parallel_timing'];lines.extend(['','| 指标 | 实测 |','|---|---:|',
            f'| 固定原生边界任务数 | {r["source_job_count"]} |',f'| 每后端新解析步 | {r["work_per_backend"]} |',
            f'| 串行初始化 s | {s["setup_s"]:.6f} |',f'| 串行计算 s | {s["execution_s"]:.6f} |',f'| 四进程含启动/退出总耗时 s | {p["end_to_end_including_startup_shutdown_s"]:.6f} |',
            f'| 含启动净加速倍数 | {r["measured_net_speedup_including_startup"]:.4f} |',
            f'| 原停止门通过/拒绝 | {r["original_stop_proof_passed"]}/{r["original_stop_proof_rejected"]} |',
            f'| 实际使用物理核心 | {p["cores"]} |',
            '',f'按本次实测，建议后端：`{r["selected_backend_for_this_workload"]}`。没有以四核数量冒充四倍加速。',
            '所有任务按原ID输出；完整float64状态、控制、五记忆数组的SHA256，以及原净空/控制/速率/停车/计数逐项完全一致。',
            '原任务预测拒绝如有发生，不计为实际碰撞，也不通过并行换排序或缩尾来消除拒绝。'])
    elif d:lines.extend(['','原ERROR/COMPLETION保留：'+str(d.get('error'))+'；未完成工作未知，不重启冻结基准。'])
    lines.extend(['','## 资源边界','',
        '新资源配置明确最多4个独立物理核心2/3/4/5，每进程单线程、nice19/SCHED_IDLE/IOidle。',
        '不查询Stage或其他作业进程，不改变它们的资源。低优先级是让路机制，不能保证硬件绝对零争用或宣称独占核心。',
        '未启动GPU计算或创建GPU运行上下文；目前内核为小型有状态C++递推，另开GPU迁移不能直接解决实际入口未接完的问题。',
        '用户GPU许可已记录；后续有大批量可匹配计算时再按相同正确性门评估，不自动换仿真引擎、训练或改物理协议。',
        '', '## 当前真正阻塞与下一步','',
        '近几轮完整软件准备核心多为1～3秒，用户等待还包括助手编写入口和修复错误；',
        '算力扩容不能替代完成输入包的真实执行worker、实际记录审核与隔离资格。',
        '下一轮直接接这三个固定输入：物理顺序执行，独立预测/审核启用已验证的多核后端；不再搜索输入。',
        '新的物理硬截止尚未打开，本轮性能通过不是响应、整路、三路线或24项验收，也不证明实时/泛化。',
        '原数据/异常/归档保留，remote未核验不删；新状态/训练/实机0。'])
    report.write_text('\n'.join(lines)+'\n');summary=dict(closed=True,multicore_backend_qualified=passed,resource_config=str((C/'NEXT_ROUND_RESOURCE_CONFIG.json').relative_to(R)),measured_net_speedup=r['measured_net_speedup_including_startup']if passed else None,selected_backend=r['selected_backend_for_this_workload']if passed else None,analytical_serial_native=d.get('serial_analytical_native')if d else None,analytical_parallel_native=d.get('parallel_analytical_native')if d else None,physical_native=0,models=0,training_updates=0,physical_window_open=False,actual_entry_still_pending=True,report=str(report.relative_to(R)));dump(O/'LEDGER.json',summary)
    p=R/'CURRENT_EXPERIMENT.json';j=read(p);assert j['active_run']in [None,'runs/v1176_multicore_stop_backend'];j.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=summary['report'],latest_v1176=summary,resource_policy=config,next_scope='User explicitly allows multicore CPU/optional GPU. Independent full-stop predictions validated with up to4 low-priority processes; use measured faster mode. Physical controller remains one owner. Next finish actual entry/audit/isolation for the exact V1175 three-input bundle; no more stimulus search. No new physical window or GPU port/training.');dump(p,j)
    with(R/'RESEARCH_STATUS.md').open('a')as h:h.write(f'\n- V1176用户多核CPU/可选GPU授权已落实新后端：validated={passed}，核心2/3/4/5低优先级进程各独立C++全局计数/1线程、完整数组SHA与原门/顺序/计数一致；含启动实测净倍数{summary["measured_net_speedup"]}，选择{summary["selected_backend"]}。原源不改/不看其他线进程/不保证独占；物理仍唯一所有者。GPU未启计算、不另开迁移支线，0新物理/训练，下一直接补固定三组件实际入口。{summary["report"]}。\n')
    snap=O/'metadata_at_close';snap.mkdir(exist_ok=True)
    for n in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']:(snap/n).write_bytes((R/n).read_bytes())
    (O/'HANDOFF.md').write_text('# LATEST OVERRIDE — V1176 multicore backend closed\n\nRead report/RESULT/FINAL_INDEPENDENT_AUDIT/NEXT_ROUND_RESOURCE_CONFIG. New CPU multiprocessing authority applies only new code; source/process isolation and physical single ownership remain. No Stage inspection. No GPU computation or physical window. Next finish actual input-bundle execution/audit/isolation rather than more stimulus searches.\n')
    paths={p for p in O.rglob('*')if p.is_file()and p.name not in ['LOCAL_MANIFEST.json','FINALIZED.json','relay.console']};paths.update(p for p in C.glob('*')if p.is_file());paths.add(report);files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};size=sum(v['bytes']for v in files.values());assert size<2*1024**3;dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']for n,v in files.items());dump(O/'FINALIZED.json',dict(closed=True,multicore_backend_qualified=passed,source_unchanged=source,manifest_readback=True,files=len(files),bytes=size,models=0,physical_native=0,closed_unix=time.time()));print(json.dumps(summary));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
