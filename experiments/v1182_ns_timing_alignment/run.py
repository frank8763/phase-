from pathlib import Path
import sys,time,json,hashlib,math,fcntl,signal,traceback,importlib.abc
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1182_ns_timing_alignment'
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','physical','torch','rclpy'}:raise AssertionError('ZERO_PHYSICAL '+name)
sys.meta_path.insert(0,NoModels());sys.path.insert(0,str(R/'experiments/v1179_frozen_recovery_native'));import recovery_tools as old
q=old.q;np=q.np;dump=q.dump;read=old.read;sha=q.sha;GUARD=q.GUARD
def source_ok():return all(sha(R/n)==h for n,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def main():
    assert not(O/'ROUND_WINDOW.json').exists()and not(O/'COMPLETION.json').exists()and source_ok();assert sha(R/'REVIEW_PENDING')==GUARD
    assert read(R/'runs/v1180_fresh_recovery_chain/FINALIZED.json')['fresh_known_course_main_repeat_passed']and read(R/'runs/v1181_remaining_route_transfer/FINALIZED.json')['closed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);start=time.monotonic();wall=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();dump(O/'ROUND_WINDOW.json',dict(software_only=True,models_authorized=False,started_unix=wall,absolute_deadline_unix=wall+900,hard_stop_monotonic=start+900,boot_id=boot))
    def remaining():
        assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot;return min(wall+900-time.time(),start+900-time.monotonic())
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('TIMING_SOFTWARE_900S')));signal.alarm(900)
    engine=None;inside=False;py=0;error=None;answer=dict(nominal_timing_source_passed=False,models=0,new_mujoco_native=0,new_actual_observations=0,training_updates=0,actual_route_passed=False,new24=False,formal_retained_commit=False)
    try:
        j=read(C/'TASK.json');x=read(R/j['input']);base=j['rows'];assert base[0]==[0.,0.,1151,0];moving=base[1:];origin=dict(q.initial(x['packet']),steering_load_episode=False)
        with np.load(R/'runs/v1181_remaining_route_transfer/NORTH_SOUTH_SOURCE.npz')as z:poses=z['states'][1151:,:3].copy()
        with np.load(R/'runs/v1181_remaining_route_transfer/NORTH_SOUTH_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
        g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);inside=True;hs,hu,hm=engine.simulate(origin,[(0.,0.,1963,0)]);inside=False
        holdraw=np.minimum(*g.components(hs[:,:3],np.arange(len(hs))));holdprefix=np.minimum.accumulate(holdraw);static=g.static.clearances(poses)[0];yaw=poses[:,2,None]
        from geometry import NORMALS
        low=poses[:,:2]@NORMALS.T-.44*abs(np.cos(yaw)*NORMALS[:,0]+np.sin(yaw)*NORMALS[:,1])-.375*abs(-np.sin(yaw)*NORMALS[:,0]+np.cos(yaw)*NORMALS[:,1]);ticks=np.arange(len(poses));scores=[]
        for wait in range(1964):
            assert remaining()>60;dynamic=(low-g.upper(ticks+wait)-.1).max(1);minimum=float(min(static.min(),dynamic.min(),holdprefix[wait]));scores.append(dict(wait_native=wait,proposal_raw_lower=minimum,hold_prefix_raw=float(holdprefix[wait]),moving_static_raw=float(static.min()),moving_dynamic_raw=float(dynamic.min())))
        best=min(scores,key=lambda r:(-r['proposal_raw_lower'],r['wait_native']));dump(O/'PHASE_PROPOSALS.json',dict(proposal_only_no_state_propagation_at_other_waits=True,scores=scores,selected=best));wait=best['wait_native'];rows=([(0.,0.,wait,0)]if wait else[])+moving
        inside=True;ss,uu,mm=engine.simulate(origin,rows);inside=False;p=q.model.Predictor(x['setup'],origin);ps=[p.state.copy()];pu=[];pm=[np.r_[p.adapter.last,p.adapter.integral]]
        for target,speed,n,mode in rows:
            p.adapter.parked_target=float(target)if mode else None
            for _ in range(int(n)):
                assert remaining()>15;inside=True;s,u=p.step(float(speed),0. if mode or speed==0. else float(speed)*math.tan(target)/.6,False);inside=False;py+=1;ps.append(s);pu.append(u);pm.append(np.r_[p.adapter.last,p.adapter.integral])
        modelerror=max(float(abs(ss-np.array(ps)).max()),float(abs(uu-np.array(pu)).max()),float(abs(mm-np.array(pm)).max()));assert modelerror<=1e-8,'MODEL_MEMORY_MISMATCH'
        proof,rr=g.final(x,ss,uu,rows);target=np.array(x['safe_terminal_pose']);position=float(np.linalg.norm(ss[-1,:2]-target[:2]));heading=float(abs(np.arctan2(np.sin(ss[-1,2]-target[2]),np.cos(ss[-1,2]-target[2]))));proof['checks'].update(fixed_terminal_position=position<=.025,fixed_terminal_heading=heading<=.1,complete_cpp_python_memory=modelerror<=1e-8);proof['passed']=bool(all(proof['checks'].values()));proof.update(failed_checks=[k for k,v in proof['checks'].items()if not v],fixed_terminal_position_error=position,fixed_terminal_heading_error=heading)
        answer.update(nominal_timing_source_passed=proof['passed'],selected_wait_native=wait,old_wait_native=1151,proposal_score=best,proof=proof,maximum_cpp_python_memory_error=modelerror,selected_rows=rows,complete_actual_lateral_state_available=False,physical_promotion_authorized=False);np.savez_compressed(O/'SELECTED_SOURCE.npz',states=ss,controls=uu,memory=mm,requests=rr);dump(O/'SELECTED_PLAN.json',dict(input=x,rows=rows,proof=proof,source_is_nominal_development_only=True))
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        signal.alarm(0);answer.update(closed=True,error=error,analytical_cpp_native=None if inside else engine.native if engine else 0,analytical_python_native=py,partial_work_unknown=inside,source_unchanged=source_ok(),guard_original=sha(R/'REVIEW_PENDING')==GUARD,wall_s=time.monotonic()-start);dump(O/'COMPLETION.json',answer);finalize(answer);fcntl.flock(lock,fcntl.LOCK_UN)
def finalize(a):
    p=a.get('proof',{});report=R/'docs/RPCCR_NS_TIMING_ALIGNMENT_V1182_REPORT.md';lines=['# V1182 南北参考等待时序对齐','',f'软件轮闭批；唯一选中候选全门通过={a["nominal_timing_source_passed"]}。',
        f'原等待1151原生步；新选中等待={a.get("selected_wait_native")}；驱动目标/速度/时长及2200停车尾不改。',
        '先对1964个等待整数做复用位姿的纯几何时序提案，含完整等待前缀净空；只对评分最好/最短等待的一项做真实模型完整传播与原全门审核。没有把相位平移提案当动力学证书。',
        f'最终完整传播raw={p.get("minimum_raw_m")}；原门.24353421020226934；目标上界={p.get("goal_upper_m")}；固定终端位置误差={p.get("fixed_terminal_position_error")}；拒绝门={p.get("failed_checks")}。',
        f'Cpp/Python解析步={a["analytical_cpp_native"]}/{a["analytical_python_native"]}；全状态控制记忆误差={a.get("maximum_cpp_python_memory_error")}；物理模型/积分/训练0。',
        '原小包缺实际侧速，沿原名义lateral=0约定，仅软件模型转接；不称完整实际状态、实测到达、三路线/24或通用W/全后继保证。原V1181失败与原所有窗口保持。',
        '错误：`'+json.dumps(a['error'],ensure_ascii=False)+'`。']
    report.write_text('\n\n'.join(lines)+'\n');current=read(R/'CURRENT_EXPERIMENT.json');current.update(active_zero_model_diagnostic=None,latest_report=str(report.relative_to(R)),latest_v1182=dict(closed=True,nominal_timing_source_passed=a['nominal_timing_source_passed'],models=0,new_mujoco_native=0,report=str(report.relative_to(R))));dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1182南北唯一初始等待修订软件闭批：nominal_pass={a["nominal_timing_source_passed"]}、wait={a.get("selected_wait_native")}、raw={p.get("minimum_raw_m")}、Cpp/Python={a["analytical_cpp_native"]}/{a["analytical_python_native"]}；1964相位仅提案/仅一完整传播，原驱动/门不降，0新模型物理，不计实际三路线24。{report.relative_to(R)}。\n')
    paths=[p for root in [C,O]for p in root.rglob('*')if p.is_file()and not p.is_symlink()and p.name not in ['console.log','LOCAL_MANIFEST.json','FINALIZED.json']and '__pycache__'not in p.parts];paths.append(report);files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in paths};assert sum(v['bytes']for v in files.values())<2*1024**3;dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True));assert all(sha(R/n)==v['sha256']for n,v in files.items());dump(O/'FINALIZED.json',dict(closed=True,nominal_timing_source_passed=a['nominal_timing_source_passed'],source_unchanged=a['source_unchanged'],manifest_readback=True,models=0,new_mujoco_native=0,files=len(files),closed_unix=time.time()));print(json.dumps({k:v for k,v in a.items()if k not in ['selected_rows','proof']}))
if __name__=='__main__':main()
