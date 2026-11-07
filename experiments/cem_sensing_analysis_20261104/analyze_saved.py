"""Additional saved-state interpretation and packet/native binding; zero models."""
import gzip, hashlib, json, math
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2]
root=repo/'runs/v795_cem_sensing_fixture'
read=lambda p:json.loads(p.read_text())
assert (repo/'REVIEW_PENDING').exists() and read(root/'ROUND_WINDOW.json')['round_closed']
assert not(root/'INTERPRETATION.json').exists()
r=read(root/'RESULT.json');audit=read(root/'SAVED_AUDIT.json')
assert audit['status']=='ALL_FIXED_CEM_SENSING_SAVED_EVIDENCE_VERIFIED'
old=read(repo/'runs/v793_saved_diagnosis/RESULT.json')
rows=[json.loads(s)for s in(repo/'runs/v793_complete_joint_navigation/main_slot01/paired/geometry_memory/v648_execution.jsonl').read_text().splitlines()]
stats=[];contexts={};bad=0;native=0
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
    for line in f:
        x=json.loads(line);contexts.setdefault(x['context'],[]).append(x)
        native+=1
        assert x['account_native']==native and x['clearance']>=.15 and x['self_margin']>=0
        bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in x['contacts'])
assert bad==0 and native==r['original_replay_native']+r['actual_validation_native']+r['branch_replay_native']
packet_pose_error=0.;packet_count=0;actual_ends=[]
for rec in r['records']:
    step=rec['step'];start=np.asarray(rows[step-1]['qpos_full'])[:2]
    for role in ['MANEUVER','CONTINUATION']:
        cs=read(root/f'S{step}_{role}_CANDIDATES.json')
        stats.append(dict(step=step,role=role,proposals=len(cs),admissible=sum(x['admissible']for x in cs),
            static_rejections=sum(x['static_minimum_m']<.155 for x in cs),
            causal_future_clearance_rejections=sum(x['clearance_m']<.155 for x in cs),
            self_rejections=sum(x['self_margin_m']<.002 for x in cs),
            terminal_linear_rejections=sum(x['terminal_speed_m_s']>.025 for x in cs),
            terminal_angular_rejections=sum(x['terminal_angular_rad_s']>.025 for x in cs),
            nonzero_observation_opportunity=sum(x['observation_opportunity']>0 for x in cs),
            best_causal_clearance_m=max(x['clearance_m']for x in cs)))
        label=f'S{step}_{role}'
        if label not in contexts:continue
        for suffix in ['', '_REPEAT']:
            actual=contexts[label+suffix]
            with gzip.open(root/(label+suffix+'_OBSERVATIONS.json.gz'),'rt')as f:obs=json.load(f)
            assert len(actual)==328 and len(obs)==41
            for i,value in enumerate(obs):
                a=actual[i*8+7];q=np.asarray(a['qpos']);p=value['packet']
                xy=q[:2].astype(np.float32).tolist()
                yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
                error=max(abs(np.asarray(xy)-p['xy']).max(),abs(yaw-p['yaw']),abs(a['time']-p['time']))
                assert error==0 and p['step']==a['public']
                packet_pose_error=max(packet_pose_error,float(error));packet_count+=1
        actual=contexts[label];end=np.asarray(actual[-1]['qpos'])[:2]
        actual_ends.append(dict(step=step,role=role,end_xy=end.tolist(),
            absolute_goal_progress_m=float(8.-np.linalg.norm(end-[4.,-2.])),
            crossed_central_x0=any(a['qpos'][0]>=0 for a in actual)))
assert packet_count==r['actual_packets']
interpretation=dict(status='SAVED_COMPONENT_INTERPRETATION_AND_PACKET_NATIVE_BINDING_VERIFIED',
    proposal_stats=stats,actual_endpoints=actual_ends,packet_native_pose_time_error=packet_pose_error,
    actual_packet_count=packet_count,actual_native_logs=native,bad_contacts=bad,
    observation_opportunity_all_zero=True,active_information_reward_benefit_established=False,
    same_continuation_old_aged_min_m=r['records'][1]['aged_same_continuation_min_m'],
    same_continuation_renewed_min_m=r['records'][1]['forward_continuation']['clearance_m'],
    old_v793_maximum_absolute_progress_m=old['maximum_goal_progress_m'],
    old_frontier_exceeded=False,full_global_dynamic_passed=False,
    model_initializations=0,integrations=0,
    physical_batch_model_initializations_occurred=True,
    physical_batch_exact_model_constructor_count_not_instrumented=True,
    next_hypothesis='Retain full-safe compound schedules and actual sensor renewal, then separately test reference-aligned continuation at the central-approach bottleneck; objective must have nonzero task-relevant visibility variation before claiming active-perception contribution.',
    no_additional_control_or_model_test_executed=True)
(root/'INTERPRETATION.json').write_text(json.dumps(interpretation,indent=2)+'\n')
text='''# V795 实际结论与下一步（零模型解释）

本轮获得一个固定旧状态的组合控制/实际感知更新资格；完整场地动态仍未通过。

- 原第200步，两段328原生控制实际向目标推进0.359748m和0.318928m，合计0.678676m。两段完整重复与全状态控制/测距/因果域/真实接触一致，误差0。
- 同一个第二段，保持旧观测并按真实时间老化，最低证书净空0.128050m，不满足0.155；使用第一段实际新测距后为0.351418m。这个固定比较支持真实观测更新对该续行证书有用，不是虚构未来感知。
- 原第125步只有第一段0.050361m进展，随后128提案全部因未来因果净空拒绝，最好也仅0.088288m；没有合格续行。静态几何、自体、末速度在这128项中均通过，不能称实际有碰撞或证明所有控制无解。
- 本次640提案中，观察机会评分全部为0。实际结果不能归功于主动信息奖励，也不能证明CEM优于原算法；局部进展只能归为本有限组合控制与真实更新的可执行性证据。
- 第200步分支末原任务绝对目标进展2.930407m，未超过原V793最好2.979145m，没有跨过中央x=0，也没有发现原动态actor。因此不是“动态全局已经跑通”。

实际记账：1600旧重放、211232私有预测、984新分支验证、984完整分支重放、246实际测距（含重复）。真实最低净空0.305892278m，障碍/穿透/未知0，原生预测/重放误差0。完整导航与新确认0；模型构造确已发生，精确构造器数量未单独计数，不能写成零模型物理实验。独立保存审核与本解释脚本为零模型/零积分。

V794错误引用原XML±.45，实际保存模型为±.52，在0积分入口停止；全部失败与归档保留。V795仅此一次元数据修正，控制参数仍±.42，方法/随机字节完全相同。旧窗口和本轮原总截止不延长。

下一步应先在原中央接近瓶颈处检验“沿走廊的安全组合控制+真实更新”是否能超过旧停滞位置；同时修复或证明感知效用的任务相关变化，才能做其独立消融。不应因为本地0.679m就直接宣称主动感知MPC成立、全局动态验收或RAS创新。该后续控制实现、完整导航和新分母本轮均未运行；原单候选与唯一夹具修正额度已闭合，不继续追加物理搜索。
'''
(root/'INTERPRETATION.md').write_text(text)
(repo/'docs/RPCCR_CEM_SENSING_V795_ANALYSIS.md').write_text(text)
print(json.dumps(interpretation))
