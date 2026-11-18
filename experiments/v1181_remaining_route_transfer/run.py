from pathlib import Path
import sys,os,time,json,hashlib,signal,fcntl,importlib.abc,traceback
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1181_remaining_route_transfer'
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','physical','torch','rclpy'}:raise AssertionError('NO_PHYSICAL_MODEL '+name)
sys.meta_path.insert(0,NoModels());sys.path.insert(0,str(R/'experiments/v1179_frozen_recovery_native'))
import recovery_tools as old
q=old.q;np=q.np;dump=q.dump;sha=q.sha;read=old.read;GUARD=q.GUARD
sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'));import chain as bridge
def source_ok():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def main():
    assert not(O/'ROUND_WINDOW.json').exists()and not(O/'COMPLETION.json').exists();assert source_ok();start=time.monotonic();wall=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();dump(O/'ROUND_WINDOW.json',dict(software_only=True,models_authorized=False,started_unix=wall,absolute_deadline_unix=wall+900,hard_stop_monotonic=start+900,boot_id=boot))
    def remaining():
        assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot;return min(wall+900-time.time(),start+900-time.monotonic())
    def halt(*_):raise TimeoutError('TRANSFER_SOFTWARE_900S')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.alarm(900)
    rows=[];errors=None;engine=None;pycount=0;inside=False;stage='dependency_wait';lock=None
    try:
        parent=R/'runs/v1180_fresh_recovery_chain';until=time.monotonic()+min(300,remaining()-120)
        while not(parent/'FINALIZED.json').exists():
            assert time.monotonic()<until,'PARENT_NOT_FINALIZED_WITHIN_BOUND'
            if(parent/'COMPLETION.json').exists():assert read(parent/'COMPLETION.json')['passed'],'PARENT_FAILED_NO_TRANSFER'
            time.sleep(2)
        assert read(parent/'FINALIZED.json')['fresh_known_course_main_repeat_passed'],'PARENT_PAIR_NOT_PASSED';assert sha(R/'REVIEW_PENDING')==GUARD
        lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_run']is None;current.update(active_zero_model_diagnostic=str(O.relative_to(R)));dump(R/'CURRENT_EXPERIMENT.json',current)
        for task in read(C/'TASKS.json'):
            assert remaining()>90;stage=task['id'];engine=None;x=read(R/task['input']);origin=dict(q.initial(x['packet']),steering_load_episode=False);source_tick=x['source']['source_native_tick'];assert source_tick<=x['packet']['native_tick']and 0<=x['source']['source_age_s']<=.051
            table,lp=bridge.joint_table(x['source']);np.savez_compressed(O/(stage+'_TABLE.npz'),**table);g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);inside=True;ss,uu,mm=engine.simulate(origin,task['rows']);inside=False
            p=q.model.Predictor(x['setup'],origin);ps=[p.state.copy()];pu=[];pm=[np.r_[p.adapter.last,p.adapter.integral]]
            for turn,speed,n,mode in task['rows']:
                p.adapter.parked_target=float(turn)if mode else None
                for _ in range(int(n)):
                    assert remaining()>15;inside=True;s,u=p.step(float(speed),0. if mode or speed==0. else float(speed)*np.tan(turn)/.6,False);inside=False;pycount+=1;ps.append(s);pu.append(u);pm.append(np.r_[p.adapter.last,p.adapter.integral])
            ps=np.array(ps);pu=np.array(pu);pm=np.array(pm);error=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()),float(abs(pm-mm).max()));assert error<=1e-8,'COMPLETE_CURRENT_MODEL_CPP_PYTHON_MISMATCH'
            proof,req=g.final(x,ss,uu,task['rows']);target=np.array(x['safe_terminal_pose']);position=float(np.linalg.norm(ss[-1,:2]-target[:2]));heading=float(abs(np.arctan2(np.sin(ss[-1,2]-target[2]),np.cos(ss[-1,2]-target[2]))))
            proof['checks'].update(fixed_terminal_position=position<=.025,fixed_terminal_heading=heading<=.1,signed_request_scope=bool((req[:,0]>=-.03).all()and(req[:,0]<=.12).all()),model_state_control_memory_exact=error<=1e-8);proof.update(passed=bool(all(proof['checks'].values())),failed_checks=[k for k,v in proof['checks'].items()if not v],fixed_terminal_position_error=position,fixed_terminal_heading_error=heading,maximum_cpp_python_memory_error=error)
            row=dict(id=stage,nominal_source_passed=proof['passed'],proof=proof,analytical_cpp_native=engine.native,analytical_python_native=len(pu),LP_calls=lp,source_native_tick=source_tick,decision_native_tick=x['packet']['native_tick'],new_physical_models=0,new_mujoco_native=0,not_actual_route_success=True,complete_actual_lateral_state_available=False,physical_promotion_authorized=False);rows.append(row)
            np.savez_compressed(O/(stage+'_SOURCE.npz'),states=ss,controls=uu,memory=mm,requests=req);dump(O/(stage+'_RESULT.json'),row);dump(O/'PROGRESS.json',dict(stage=stage,completed=len(rows),passed=sum(r['nominal_source_passed']for r in rows),models=0,new_mujoco_native=0))
    except BaseException as exc:errors=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',errors)
    finally:
        signal.alarm(0);summary=dict(closed=True,completed=len(rows),all_two_nominal_sources_passed=len(rows)==2 and all(r['nominal_source_passed']for r in rows),rows=rows,error=errors,stop_stage=stage,analytical_cpp_native=None if inside else sum(r['analytical_cpp_native']for r in rows)+(engine.native if engine and(len(rows)==0 or rows[-1]['id']!=stage)else 0),analytical_python_native=pycount,partial_work_unknown=inside,models=0,new_mujoco_native=0,training_updates=0,source_unchanged=source_ok(),guard_original=sha(R/'REVIEW_PENDING')==GUARD,wall_s=time.monotonic()-start,actual_three_route_passed=False,new24=False,formal_retained_commit=False)
        dump(O/'COMPLETION.json',summary);finalize(summary)
        if lock:fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if errors is None else 1
def finalize(s):
    report=R/'docs/RPCCR_REMAINING_ROUTE_TRANSFER_V1181_REPORT.md';lines=['# V1181 另外两路线的当前模型参考转接','',f'软件轮已关闭；两份名义来源全门通过={s["all_two_nominal_sources_passed"]}，完成{s["completed"]}/2。','',
        '只用原NS15290与EW21520开发保存输入。NS明示从旧.125参考改为.12并按比例延长活动段，旧等待及2200停保持；EW原通用几何种子解行序不改，仅换当前已验证响应模型重新传播。',
        '原小输入未记录侧速、旧raw已按存储规则归档移出本地；本轮明确沿原名义模型lateral=0约定，仅作模型转接诊断，不能当完整实际状态/实测准入。',
        '这是固定候选的软件资格，不把保存优化向量直接冒称在线规划输出，不合并旧路线成功或声称新实测。','', '| 路线 | 当前模型名义源 | raw下界m | 目标上界m | 原固定终端误差m | 主要拒绝 |','|---|---|---:|---:|---:|---|']
    for row in s['rows']:
        p=row['proof'];lines.append(f'| {row["id"]} | {row["nominal_source_passed"]} | {p["minimum_raw_m"]} | {p["goal_upper_m"]} | {p["fixed_terminal_position_error"]} | {p["failed_checks"]} |')
    lines+=['','新物理模型/积分/导航/训练均0。Cpp解析步='+str(s['analytical_cpp_native'])+'，Python解析步='+str(s['analytical_python_native'])+'，异常时未知账目不填0。', '错误：`'+json.dumps(s['error'],ensure_ascii=False)+'`。',
        '仍缺完整实际反馈、重新生成在线源/同版本全路线及完整重复；本轮不能成为三路线、24项、未来W/全后继或实机保证。',
        'V1180主重复完成依赖、原guard及源SHA均核验；原所有旧窗口/失败保留。第一模型或证据异常停，无固定任务外追加候选。']
    report.write_text('\n'.join(lines)+'\n');current=read(R/'CURRENT_EXPERIMENT.json');current.update(active_zero_model_diagnostic=None,latest_report=str(report.relative_to(R)),latest_v1181=dict(closed=True,all_two_nominal_sources_passed=s['all_two_nominal_sources_passed'],completed=s['completed'],models=0,new_mujoco_native=0,error=s['error'],report=str(report.relative_to(R))));dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1181两剩余路线当前模型名义转接闭批：two_sources={s["all_two_nominal_sources_passed"]}、completed={s["completed"]}、Cpp/Python={s["analytical_cpp_native"]}/{s["analytical_python_native"]}，新模型物理0；旧NS.125→明示新.12延时，EW原行序/当前模型；不计实际三路线24，旧失败和formal缺口保持。{report.relative_to(R)}。\n')
    paths=[p for root in [C,O]for p in root.rglob('*')if p.is_file()and not p.is_symlink()and p.name not in ['console.log','LOCAL_MANIFEST.json','FINALIZED.json']and '__pycache__'not in p.parts];paths.append(report);size=sum(p.stat().st_size for p in paths);assert size<2*1024**3
    manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p))for p in paths};dump(O/'LOCAL_MANIFEST.json',dict(files=manifest,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']for n,v in manifest.items());dump(O/'FINALIZED.json',dict(closed=True,all_two_nominal_sources_passed=s['all_two_nominal_sources_passed'],source_unchanged=s['source_unchanged'],manifest_readback=True,files=len(manifest),bytes=size,models=0,new_mujoco_native=0,closed_unix=time.time()))
    print(json.dumps({k:v for k,v in s.items()if k!='rows'}))
if __name__=='__main__':sys.exit(main())
