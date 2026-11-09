"""Closed campaigns only, zero-model summaries and corrected current pointers."""
import fcntl,hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v924_20261109'
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
rows=[]
for v in ['v920_native_ingress','v924_consistent_polygon_reference']:
 O=R/'runs'/v;assert read(O/'COMPLETION.json')['closed'];assert read(O/'FINALIZED.json')['all_sources_and_decompressed_sha_verified'];assert not(O/'FINALIZE_ERROR.json').exists()
 freeze=read(R/'experiments'/v/'SOURCE_FREEZE.json')['files'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze.items())
 row=dict(version=v,completion=read(O/'COMPLETION.json'),audits=[])
 for p in sorted((R/'runs/v858_nav2_verified'/v[:4]).glob('*/INDEPENDENT_AUDIT.json')):
  n=read(p.parent/'RESULT.json');a=read(p);row['audits'].append(dict(task=p.parent.name,native={k:n.get(k)for k in ['passed','status','actual_native','replay_native','private_native','goal_distance_m','minimum_actual_clearance_m','bad_contacts','actual_travel_after_detection_m','maximum_wall_lag_s','replay','error','final_translation_speed_m_s']},audit=a))
  target=R/'records'/f'nav2_{v[:4]}_20261109';dump(target/(p.parent.name+'_INDEPENDENT_AUDIT.json'),a);dump(target/(p.parent.name+'_RESULT.json'),n)
 rows.append(row)
REC.mkdir(exist_ok=True)
for base,files in [('v922_reference_consistency_diagnosis',['SAVED_DIAGNOSIS.json']),('v923_polygon_terminal_qualification',['RESULT.json','PREPARATION_ERROR01.json','PREPARATION_ERROR02.json'])]:
 for name in files:shutil.copy2(R/'runs'/base/name,REC/(base[:4]+'_'+name))
for base in ['v925_saved_control_and_timing_diagnosis','v926_static_tube_reference_qualification']:
 target=R/'runs'/base
 if(target/'RESULT.json').exists():shutil.copy2(target/'RESULT.json',REC/(base[:4]+'_RESULT.json'))
 if(target/'production/RESULT.json').exists():shutil.copy2(target/'production/RESULT.json',REC/(base[:4]+'_RESULT.json'))
for mode in ['SOFT','HARD']:shutil.copy2(R/'runs/v922_reference_consistency_diagnosis'/mode/'RESULT.json',REC/('V922_'+mode+'_RESULT.json'))
last=rows[-1]['completion'];main=rows[-1]['audits'][0]['native'];all_native=sum(x['native']['actual_native']for r in rows for x in r['audits']);all_replay=sum(x['native']['replay_native']for r in rows for x in r['audits'])
summary=dict(closed=True,scientific_status=last['status'],all_actual_native=all_native,all_own_replay_native=all_replay,private_native=0,new24=0,training=0,hardware=0,batches=rows,original_hard_end=last['deadline_unix'],guard_original=True,execution_lock_idle=True,models_in_closure=0)
dump(REC/'CLOSED_COMPARISON.json',summary)
current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',current_experiment='v924_consistent_polygon_reference',last_completed_candidate='V924_CONSISTENT_POLYGON_REFERENCE',last_completed_outcome=last['status'],current_report='docs/NAV2_NATIVE_INGRESS_V920_V924_ANALYSIS.md',active_run=None,active_pid=None,active_entrypoint=None,entrypoint=None,active_window=None,active_authorization=None,active_protocol=None,active_automation=None,current_active=False,execution_window_closed=True,window_closed=True,automatic_additional_simulation=False,no_automatic_followup=True,latest_dynamic_development_result=last['status'],dynamic_stability_acceptance_passed=False,finite_full_field_dynamic_acceptance_passed=False);dump(R/'CURRENT_EXPERIMENT.json',current)
text='''# V920–V924 动态开发与阻塞归因

V920和V924独立冻结，后者沿本次原15:59:23.739940硬截止，未重置旧窗口。原失败全部保留。结论以各批独立审核为准，开发、重复、未执行与旧确认分母分开。

V920在146.54秒停止，实际14654/完整自身控制重放14654/私有0；发现后实际2.028222米，余2.194795米，最低净空.269149864米、坏接触0、完整qpos/qvel/ctrl/mocap误差0。两次72.937/163.539毫秒迟到新包丢弃并保留旧凭证，全14654步逐步锚点/控制到期/残差重建通过；整批仍NOT_PASSED。原始接收日志明确ROS先因最新原子观测陈旧发stop，随后222.655毫秒排队零命令在STOPPING被COMMAND_BEFORE_ARM拒绝。历史回调具体CPU/IO/调度归因未被记录，不能伪称已查明或修复。

冻结函数复算V920全部767次前进请求回退：全部仅全周期终端下界不足，原短时静态/动态门均不拒绝。几何复算中位.769毫秒/最大2.328毫秒，不能据此归因历史222毫秒阻塞。原100Hz物理最大墙钟滞后2.617毫秒，整回合运行耗时如今与仿真时间同量级；长期等待的主证据是规划参考与执行终端要求不一致。

V922在同三个实际保存态47.01/70.01/146.01秒，两个独立真实Nav2栈各做3次同任务几何查询：全周期软参考3个都有路，但全周期要求不成立；硬参考早期208、后两条有路。原16方向下界为.104922/.117248米，不能当.155门通过。V923用同一原因果16半平面外包集合的完整矩形-多边形距离，减原actor半径/原残差后，再减连续SE2插值误差，两条硬参考下界.159855509/.168239692米通过，三软参考仍拒绝；距离表示单独不能恢复767原软参考请求。8项几何/256固定构造/4194304单位方向独立检验通过。两个零模型导入准备错误原样保留，没有物理入口。

因此V924同时把全局参考改为全周期硬占据、终端取原投影和同集合完整距离的max、完整返回路径逐姿态检查同一距离要求；预测.155/实际.15、有限.2+2秒管、.02同向零/.04反转与.035角度经验界、模型/控制/测距均保持。线上向量距离与独立机体坐标标量算法3072姿态最大误差1.33e-15，真实生产路径服务器原3态早208晚2过，完整Nav2前目标启动门通过。原V920接收修订保留；ROS陈旧观测门未放宽，未知回调延迟未宣称解决。

V925零模型固定4态控制复核：新版剩余781次请求回退全部为静态下界不足；713次落入反转.04经验类，其中668次仅测量速度绝对值<1毫米/秒而命令异号。不能无资格修改该分类。固定10998态7个零/倒车几何请求合格，12999和14798态连新零命令也不合格，原有效终端凭证仍持续保留。全2960原包原因果重新计算tracker最大68.121毫秒/周期集合最大7.084毫秒；这些软件重算不识别历史心跳时延的CPU/调度/IO原因。V926下一步仅检查推导静态余量(.155+最大原管空间reserve)和全局padding.27的3个固定真实保存态实际Nav2几何可行性；没有新增物理。

V924最终结果：

```json
'''+json.dumps(dict(status=last['status'],tasks=[dict(task=x['task'],**x['native'])for x in rows[-1]['audits']],repeat=read(R/'runs/v924_consistent_polygon_reference/REPEAT.json')if(R/'runs/v924_consistent_polygon_reference/REPEAT.json').exists()else'UNEXECUTED',total_actual_native=all_native,total_replay_native=all_replay),ensure_ascii=False,indent=2)+'''
```

只覆盖公开omega.32/幅<=.25的单actor课程及条件经验动力学误差，发现前较弱反应式静态条件保持。不能声称任意方向.08速度类、原.12轴类、任意遮挡/多actor/地图、递归安全、普遍实时、RAS方法创新或新24验收。异步完整重复要求同模型规范初态和各自完整重放，不冒称两条实际轨迹逐点精确相同。

必要源码/报告/汇总Git、完整原始接收/状态/控制/接触/传感/模型/重放/资格证据同仓库Release；下载解压逐来源SHA通过后只清已验证缓存。V920失败不追认通过，V924未执行项目不填0/24。下一阶段仍需同版本三路线及未暴露确认，公平基线/消融和后续实机证据。
'''
(R/'docs/NAV2_NATIVE_INGRESS_V920_V924_ANALYSIS.md').write_text(text)
with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- FINAL本次V920/V924均已闭批；V924='+last['status']+'，新增实际总'+str(all_native)+'/完整自身重放'+str(all_replay)+'/私有0。完整停止原因及独立各门见docs/NAV2_NATIVE_INGRESS_V920_V924_ANALYSIS.md；V920及全部旧失败不改，新24/训练/实机0，原REVIEW_PENDING字节恢复/锁空闲，本次不再物理候选。V922/V923为零模型固定输入诊断/几何资格，未执行项目不当成功率分母。\n')
print(json.dumps(dict(status=last['status'],actual_native=all_native,replay_native=all_replay,models=0)),flush=True)
