"""Prepare physical use of the one qualified time-reference revision."""
import ast,json,pathlib,shutil
repo=pathlib.Path(__file__).resolve().parents[2];old=repo/'experiments/v807_reactive_single_task_continuation';qual=repo/'experiments/v808_timed_reference_qualification';own=repo/'experiments/v809_time_reference_global';assert not own.exists();own.mkdir()
for p in old.iterdir():
 if p.suffix in ['.py','.md','.json']and p.name!='CANDIDATE_FREEZE.json':(own/p.name).write_text(p.read_text().replace('v807_reactive_single_task_continuation','v809_time_reference_global'))
for n in ['planner.py','timed_reference.py']:shutil.copy2(qual/n,own/n)
(own/'future_guide.py').write_text('"""Time-labelled current-occupancy reference; execution safety separate."""\nfrom timed_reference import route_world,HORIZON\n')
p=own/'run_static.py';s=p.read_text();anchor="                    route_field.guard=.15;route_field.base_heuristic=F.base._heuristic_grid";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"\n                    from timed_reference import attach\n                    attach(route_field,motion_state)");p.write_text(s)
p=own/'route_commitment.py';s=p.read_text();s=s.replace("    minimum=float(np.min(field.pose_values(path[index:end,:3])))",'''    if getattr(field,'temporal_state',None)is None:
        minimum=float(np.min(field.pose_values(path[index:end,:3])))
        extra={}
    else:
        from timed_reference import current_route_samples
        queries,times=current_route_samples(path,index,current)
        minimum=float(np.min(field.reference_values(queries,times)))
        extra={'time_reference_query_poses':queries.tolist(),'time_reference_query_times_s':times.tolist(),'temporal_validation_is_reference_only':True}''');s=s.replace("return {'current_route_minimum_m'","return {**extra,'current_route_minimum_m'");p.write_text(s)
p=own/'reference_audit_geometry.py';s=p.read_text();start=s.index('  t=np.linspace');end=s.index('\n return SimpleNamespace',start);p.write_text(s[:start]+s[end:])
p=own/'audit_field_preflight.py';s=p.read_text().replace('len(details)==len(tasks)==1','len(details)==len(tasks)==3').replace('One preregistered original development route','Three preregistered original development routes');p.write_text(s)
shutil.copy2(repo/'experiments/v802_exact_rejection_global/DEVELOPMENT_TASKS.json',own/'DEVELOPMENT_TASKS.json')
p=own/'audit_reactive.py';s=p.read_text();s=s.replace("n=min(len(execution),len(static),first if first is not None else len(execution));errors=","same_prior_task=read(pair/'DYNAMIC_PROTOCOL.json')['case_id']=='WEST_EAST';n=min(len(execution),len(static),first if first is not None else len(execution))if same_prior_task else 0;errors=")
s=s.replace("predetection_vehicle_exact_static=all(v<=1e-8 for v in errors.values())and n==(first if first is not None else len(execution))","predetection_vehicle_exact_static_if_prior_exists=(not same_prior_task)or(all(v<=1e-8 for v in errors.values())and n==(first if first is not None else len(execution)))").replace("exact_static_prefix_public=n,","same_task_static_comparison_applicable=same_prior_task,exact_static_prefix_public=n,");p.write_text(s)
p=own/'audit_projection_learning.py';s=p.read_text();start=s.index('    lower,upper=future_cells');end=s.index('\nmodel=Proposer',start)
s=s[:start]+'''    times=np.linspace(0,6.56,657);lower,upper=future_cells(state['outer_state_cells'],times)
    pl=np.asarray(state['position_lower']);pu=np.asarray(state['position_upper']);vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper']);tt=times[:,None]
    lo=np.maximum(pl+tt*vl-.02*tt*tt,pl-.12*tt)-1e-5;hi=np.minimum(pu+tt*vu+.02*tt*tt,pu+.12*tt)+1e-5
    excess=float(max(np.max(lo[:,None,:]-lower),np.max(upper-hi[:,None,:])));assert excess<=1e-7
    assert metadata['status']=='TIME_LABELLED_CURRENT_OCCUPANCY_REFERENCE'and metadata['beyond_horizon_is_uncertified_guidance']and len(new['rectangles'])==len(read(root/'STATIC_PROTOCOL.json')['known_rectangles'])+1
    records.append({'step':x['step'],'maximum_containment_excess':excess,'source_hidden_world_geometry_used':state['hidden_world_geometry_used']})
''' +s[end:];p.write_text(s)
p=own/'execute_development.py';s=p.read_text();a=s.index("unchanged();assert");z=s.index("with(repo/",a);s=s[:a]+'''unchanged();assert(repo/'REVIEW_PENDING').exists();assert read(repo/'runs/v808_timed_reference_qualification/FINAL_INDEPENDENT_AUDIT.json')['status']=='TIME_REFERENCE_QUALIFICATION_PASS';assert read(repo/'runs/v808_timed_reference_qualification/FINALIZED.json')['source_decompressed_sha_verified'];assert not(root/'ROUND_WINDOW.json').exists()
'''+s[z:]
a=s.index("day=read(");z=s.index("tasks=read(own",a);s=s[:a]+'''day=read(repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json');assert day['development_revisions_used']==1 and day.get('physical_batches_started',0)==0
started=time.time();deadline=day['development_absolute_deadline_unix'];assert deadline-started>=5000,'INSUFFICIENT_ORIGINAL_DEVELOPMENT_BUDGET';'''+s[z:]
a=s.index(' # Reuse the unchanged');z=s.index(" for role in ['MAIN_DEVELOPMENT'",a)
original=(repo/'experiments/v802_exact_rejection_global/execute_development.py').read_text();pre=original[original.index(' for t in tasks:\n'):original.index(" for role in ['MAIN_DEVELOPMENT'")]
s=s[:a]+pre+s[z:];s=s.replace("('audit_route_commitment.py',60)","('audit_route_commitment.py',240)").replace("('audit_reactive.py',300)","('audit_reactive.py',300),('audit_time_reference.py',300)")
s=s.replace('ONE_REACTIVE_MAIN_AND_REPEAT_PASSED','THREE_TIME_REFERENCE_MAIN_AND_REPEAT_PASSED').replace('V806_OUTER_TERMINATED','V809_OUTER_TERMINATED');p.write_text(s)
p=own/'finalize_development.py';s=p.read_text().replace("'audit_reactive.py']","'audit_reactive.py','audit_time_reference.py']").replace('len(records)==2','len(records)==6').replace('ONE_REACTIVE_MAIN_AND_REPEAT_PASSED','THREE_TIME_REFERENCE_MAIN_AND_REPEAT_PASSED').replace('ONE_REACTIVE_DEVELOPMENT_VERIFIED','THREE_TIME_REFERENCE_DEVELOPMENT_VERIFIED').replace('planned_main=1,planned_repeat=1','planned_main=3,planned_repeat=3').replace('rpccr_reactive_continuation_v807_20261104','rpccr_time_reference_global_v809_20261104').replace('RPCCR_REACTIVE_CONTINUATION_V807_REPORT.md','RPCCR_TIME_REFERENCE_GLOBAL_V809_REPORT.md').replace('RP-CCR V807','RP-CCR V809').replace('/计划1','/计划3').replace("一个已观察任务的开发和重复","同原地图三路线已观察任务的开发和重复")
s=s.replace("text+=['',","text+=['', '唯一科学新变化是V808资格已核验的时间标记参考，原执行控制安全合同不变。原V807失败不改写，本次不是新池确认。',",1);p.write_text(s)
(own/'PROTOCOL.md').write_text('''# V809 夜间开发01物理阶段：时间标记参考
用户已授权2026-11-04后台无人监管通宵至11月5日08:00/1793836800，全夜最多2开发/1确认。V809和V808是同一科学版本，沿用V808已锁7200秒开发绝对截止，不在物理启动时重新计时。先有V808五保存输入资格独立全门与归档来源解压SHA回读，方可启动。旧V806/V807及全部旧失败保持。
唯一算法修订及边界见V808协议，planner.py/timed_reference.py原字节移植：原静态A*和当前actor外矩形作路线引导，近端6.56秒按候选时标(.20m/s/.40s换向)检查因果预测，超时域只有未证未来参考。不是实际速度/等待合同，不冒称全路径执行已证，原8+320每次完整动态风险控制准入独立保留。发现前静态反应条件不变、不声称任意未见安全。名义动作评分、后备、模型网络、传感器阈值不改。
原三路线WEST_EAST/NORTH_SOUTH/EAST_WEST、10010001–03/原相位、19静态体/单直径.20幅.25欧氏速.08actor/3m测距5%漏检。3t0全门后原序3主，全完整链通过才3完整重复；首功能或任何安全/源/模型/真值/状态/控制/覆盖/证据异常停。每nav1200公开/1200soft1500hard1505outer，t0120/125，全部子进程绝对墙钟且不越V808原截止/夜间08。无冻结后修补/新动作种子/确认。
完整链正常行驶首次测距发现、328实际停稳、新因果路线、实际续行1m、目标.45；原生净空.15/障碍穿透未知0/完整自体合法ctrl速率/无根改写/静态体固定/全状态控制重放1e-8/329执行657规划包含/原始测距因果/全部尾与再接入。新独立参考审核重构时间查询，参考不是控制证明。重复同结果长度qpos/qvel/ctrl/mocap1e-8，模型规范初态真实接触发现一致。WEST_EAST有旧无动态首段可对照，另外两路线明确无对应静态证据、不适用该项。
实际模型初始化/导航/私有预测/重放仅run_phase隔离单CPU单实例锁，finally原字节恢复REVIEW_PENDING。Stage/训练/SAC/实机0，current/runtime和冻结网络不改。闭批后零模型finalize_development.py独立终审/全来源解压SHA回读，不覆盖旧COMPLETION。剩余额度依夜间台账，不循环追加；有限反应式课程不宣称完备/实时/全面优势或RAS保证。
''')
for p in own.glob('*.py'):ast.parse(p.read_text())
assert (own/'planner.py').read_bytes()==(qual/'planner.py').read_bytes()and (own/'timed_reference.py').read_bytes()==(qual/'timed_reference.py').read_bytes()
print(json.dumps({'prepared_not_frozen':str(own),'scientific_versions':1,'models':0,'integrations':0}))

