"""Closed V892 evidence/metrics only; no model imports or simulation."""
import datetime,fcntl,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v892_dynamic_terminal_consistency';REC=R/'records/nav2_v892_20261108'
def read(p):return json.loads(p.read_text())
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    completion=read(O/'COMPLETION.json');assert completion['closed'];assert read(O/'FINALIZED.json')['source_and_decompressed_sha_verified']
    rows=[];traces=[]
    for row in completion['rows']:
        root=Path(row['output']);n=read(root/'RESULT.json');a=read(root/'INDEPENDENT_AUDIT.json');ros=read(root/'ROS_RESULT.json');setup=read(root/'physics/SETUP.json')
        item=dict(task_id=row['task_id'],passed=bool(row['passed']),actual_native=n.get('actual_native'),fully_recorded_native=n.get('fully_recorded_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),replay_status=n.get('replay_status'),sim_s=None if n.get('actual_native')is None else n['actual_native']*.01,minimum_clearance_m=n.get('minimum_actual_clearance_m'),bad_contacts=n.get('bad_contacts'),goal_m=n.get('goal_distance_m'),final_speed_m_s=n.get('final_translation_speed_m_s'),first_actor_detection=n.get('first_actor_detection'),actual_postdetection_path_m=n.get('actual_travel_after_detection_m'),successful_periodic_routes_after_detection=a.get('successful_routes_after_detection'),maximum_physics_lag_s=n.get('maximum_wall_lag_s'),maximum_own_state_error=n.get('replay',{}).get('maximum_qpos_qvel_ctrl_mocap_error'),contact_replay_mismatched_ticks=n.get('replay',{}).get('contact_mismatched_ticks'),motion_audit=a.get('motion_enclosure_independent_audit'),error=n.get('error'),ros_error=ros.get('error'))
        rows.append(item)
        if(root/'physics/NATIVE_TRACE.npz').exists():
            with np.load(root/'physics/NATIVE_TRACE.npz')as z:traces.append((item,setup,z['qpos'][:,:2].copy(),z['time'].copy(),z['clearance'].copy()))
    def total(key):return None if any(x.get(key)is None for x in rows)else sum(x[key]for x in rows)
    pair=read(O/'REPEAT_COMPARISON.json')if(O/'REPEAT_COMPARISON.json').exists()else dict(passed=False,reason='CONDITIONAL_REPEAT_NOT_COMPLETED')
    summary=dict(status=completion['status'],passed=completion['status']=='SINGLE_ACTOR_DYNAMIC_DEVELOPMENT_PASSED'and pair['passed']and all(x['passed']for x in rows),rows=rows,total_actual_native=total('actual_native'),total_replay_native=total('replay_native'),total_private_native=total('private_native'),attempted_navigation=completion['attempted_navigation'],unexecuted_navigation=completion['unexecuted_navigation'],complete_same_version_rerun=pair['passed'],new24_executed=0,independent_confirmation_denominator=0,static_NS_EW_same_new_mechanism_unexecuted=True,models_this_summary=0,integrations_this_summary=0,models_stopped=True,actual_environment_initializations_completed=1+len(rows),internal_factory_model_compile_load_count='NOT_SEPARATELY_INSTRUMENTED',source='New independent user-approved90min, original WE/seed/phase only; all old V890/V888 failures unchanged')
    (REC/'RESULT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    for name in ['ROUND_WINDOW.json','PREFLIGHTS.json','FINALIZED.json','REPEAT_COMPARISON.json']:
        if(O/name).exists():(REC/name).write_bytes((O/name).read_bytes())
    tz=datetime.timezone(datetime.timedelta(hours=8));start=datetime.datetime.fromtimestamp(completion['started_unix'],tz).isoformat();end=datetime.datetime.fromtimestamp(completion['deadline_unix'],tz).isoformat();closed=datetime.datetime.fromtimestamp(completion['closed_unix'],tz).isoformat()
    lines=['# V892观测运动占据动态开发',f"\n状态：{completion['status']}。新90分钟窗口{start}至{end}，实际闭批{closed}；旧V890及所有原失败/截止不改。",'\n原WEST_EAST/10010001/phase.6573753567727383：t0→单主→全部通过才完整重复。新增16法向凸位置外集合/欧氏速度传播，同一1.5s运动+1s工程时延余量送双map和终点准入；发现后固定49目标候选距原目标<=.24，控制到达容差.35收紧到.20，合计.44<原.45；反向虚拟终点根205记原错并转208有限Wait，真实车根205不改；开启双map完整快照。V884名义RPP核心、V887精确扫描、原物理与.15/100ms/200ms/250ms安全时序门不变。','\n|任务|通过|仿真s|实际原生|自身重放|目标距离m|最低净空m|末速m/s|','|---|---|---|---|---|---|---|---|']
    for x in rows:lines.append('|'+ '|'.join(str(x.get(k))for k in ['task_id','passed','sim_s','actual_native','replay_native','goal_m','minimum_clearance_m','final_speed_m_s'])+'|')
    lines += [f"\n实际/自身重放/私有合计：{summary['total_actual_native']}/{summary['total_replay_native']}/{summary['total_private_native']}；未执行导航{summary['unexecuted_navigation']}。None为未完成/未知，不填0，不用前缀证据追认功能或安全通过。",'\n每任务实际原测距首次发现—真实续行>=1m—之后有成功周期参考—ROS动作成功/原目标<=.45—实际停稳<=.03及全部安全/自身全状态接触重放必须，周期更新不称发现事件触发。重复同物理setup/初态并各自完整门通过；异步实际轨迹可以不同。', '\n只一固定WE动态开发任务及其条件完整重复，不是两独立确认样本、不是三动态路线或新24验收；新机制的NS/EW静态/动态回归、算法比较、机制消融和实机均未执行。V891包含真值仅离线覆盖评价，线上输入无actor真值/raw；发现前弱反应式条件、单小actor与仿真真值里程计假设保留。', '\n位置/有限运动包含不是完整动力学/制动/递归安全证明，1s地图延迟只是工程预留；原RP-CCR328合同未执行，不能称恢复原保证、论文创新优势或RAS验证。准备阶段原保存三份相同t0导致严格重复时刻拒绝、资格脚本语法错误均记录保持，资格0车辆积分；原205红例、12集合/栅格/错误门和真实Nav2五固定软件探针通过后才冻源启动，原末阻挡仍208而另一实际后续扫描168点全路径通过，不冒称实际回波续接必然。', '\n参考：官方固定Nav2 1.3.13 [StaticLayer源码](https://raw.githubusercontent.com/ros-navigation/navigation2/1.3.13/nav2_costmap_2d/plugins/static_layer.cpp)；新增层以完整map替换其自身数据、最大组合保留已知静态，已做真实软件载入/更新/清除核验。', '\n独立终审/来源与解压SHA/无损32MiB分块重组FINALIZED，必要记录Git+Release，远端digest/下载SHA/实际成员恢复核验后才清本轮缓存及V891按需输入；旧同步不重试。guard原字节恢复/执行锁空闲，当前无模型任务。']
    (R/'docs/NAV2_DYNAMIC_TERMINAL_V892_REPORT.md').write_text('\n'.join(lines)+'\n')
    current=read(R/'CURRENT_EXPERIMENT.json');current['v892_dynamic_terminal_consistency'].update(summary,report='docs/NAV2_DYNAMIC_TERMINAL_V892_REPORT.md',storage_status='LOCAL_FINALIZED_REMOTE_PENDING');current['latest_nav2_simulation'].update(status=completion['status'],latest_report='docs/NAV2_DYNAMIC_TERMINAL_V892_REPORT.md',dynamic_development_WE_passed=summary['passed'],dynamic_passed=False,new_dynamic_navigation=completion['attempted_navigation'],new24=0);(R/'CURRENT_EXPERIMENT.json').write_text(json.dumps(current,indent=2)+'\n')
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- FINAL V892 '+json.dumps(summary,ensure_ascii=False)+'；只原WE单actor有限开发/条件重复，不混新24分母；无冻结后修补/其他路线/比较训练实机。报告docs/NAV2_DYNAMIC_TERMINAL_V892_REPORT.md，随后零模型完整传感原算法回读/远端交付。\n')
    if traces:
        import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle,Circle
        fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
        for x,setup,position,times,clearance in traces:
            axes[0].plot(position[:,0],position[:,1],label=x['task_id']);axes[1].plot(times,clearance,label=x['task_id'])
            if x['first_actor_detection']:axes[0].scatter(*x['first_actor_detection']['xy'],s=25)
        for px,py,hx,hy in setup['known']['known_rectangles']:axes[0].add_patch(Rectangle((px-hx,py-hy),2*hx,2*hy,color='0.8'))
        for px,py,rad in setup['known']['known_circles']:axes[0].add_patch(Circle((px,py),rad,color='0.8'))
        axes[0].scatter(*setup['case']['goal_xy'],marker='*',s=80,color='black');axes[0].set(xlim=(-4.5,4.5),ylim=(-3.5,.5),aspect='equal',title='V892 actual saved trajectories',xlabel='x (m)',ylabel='y (m)');axes[0].legend(fontsize=8)
        axes[1].axhline(.15,color='red',linestyle='--',label='Original 0.15m floor');axes[1].set(title='Actual native clearance',xlabel='Simulation time (s)',ylabel='Clearance (m)');axes[1].legend(fontsize=8);fig.savefig(REC/'DYNAMIC_TRAJECTORIES.png',dpi=150);plt.close(fig)
    print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
