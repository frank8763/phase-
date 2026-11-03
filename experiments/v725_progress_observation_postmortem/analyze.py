"""Post-closure raw trajectory comparison only; no simulator initialization."""
import csv,gzip,hashlib,json,math,os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v725_progress_observation_postmortem'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (repo/'REVIEW_PENDING').exists()
final=read(repo/'runs/v724_progress_observation_recovery/FINALIZED.json')
assert read(repo/'runs/v724_progress_observation_recovery/ROUND_WINDOW.json')['round_closed']
freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
root.mkdir(exist_ok=False);summaries=[];allrows={};pairs={}
for version,base in [('V712','v712_joint_field_continuation'),('V721','v721_recursive_unseen_navigation'),('V724','v724_progress_observation_recovery')]:
 if version=='V712':base='v712_joint_field_continuation'
 pair=repo/'runs'/base/'main01/paired'
 if not pair.exists()and version=='V712':
  pair=repo/'runs/v712_joint_field_continuation/development01/main01/paired'
 assert pair.exists(),str(pair)
 cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');result=read(cell/'result.json');rows=lines(cell/'v648_execution.jsonl');states=lines(cell/'motion_estimate.jsonl');events=lines(cell/'control_decisions.jsonl');xy=np.asarray([x['qpos_full'][:2]for x in rows]);goal=np.asarray(protocol['goal_xy']);start=np.asarray(protocol['start_qpos'][:2]);d=np.linalg.norm(xy-goal,axis=1);displacement=np.linalg.norm(xy-start,axis=1)
 rr=read(pair/'NATIVE_REPLAY_AUDIT.json');disc=read(cell/'FIRST_DISCOVERY.json')if (cell/'FIRST_DISCOVERY.json').exists()else None;choices=[e for e in events if e['stage']=='BACKUP_APPEND'and e.get('detail',{}).get('recovery_selection_metadata')is not None]
 selection=read(pair/'RECOVERY_SELECTION_AUDIT.json')if (pair/'RECOVERY_SELECTION_AUDIT.json').exists()else None
 if selection is None and choices:selection=dict(extra_visibility_evaluations=sum(x['detail']['recovery_selection_work']['visibility_evaluations']for x in choices),extra_selection_wall_seconds=sum(x['detail']['recovery_selection_work']['wall_seconds']for x in choices))
 summary=dict(version=version,run=str(pair.relative_to(repo)),outcome=result['outcome'],strict_arrival=result['strict_safe_arrival'],public_steps=len(rows),maximum_displacement_m=float(displacement.max()),closest_goal_distance_m=float(d.min()),final_goal_distance_m=float(d[-1]),first_discovery=disc,minimum_native_clearance_m=result['minimum_dynamic_native_clearance_m'],navigation_native_steps=result['physics_steps'],replay_native_steps=rr['replay_integration_steps'],private_integrations=result['prediction_steps'],wall_seconds=result['elapsed_s'],normalized_initial_state_hash=result['normalized_initial_state_hash'],model_sha256=sha(pair/'scene_model.mjb'),maximum_replay_error=max(rr['maximum_full_public_qpos_error'],rr['maximum_full_public_qvel_error'],rr['maximum_public_mocap_error']),recovery_selection_choices=len(choices),extra_selection_visibility_evaluations=None if selection is None else selection['extra_visibility_evaluations'],extra_selection_wall_seconds=None if selection is None else selection['extra_selection_wall_seconds'])
 summaries.append(summary);allrows[version]=rows;pairs[version]=pair
comparisons=[]
for version in ['V712','V721']:
 a=next(x for x in summaries if x['version']==version);b=summaries[-1];aa=allrows[version];bb=allrows['V724'];first=None
 for i,(x,y)in enumerate(zip(aa,bb)):
  if max(float(np.max(abs(np.asarray(x[k])-np.asarray(y[k]))))for k in ['qpos_full','qvel_full','ctrl','mocap_pos'])>1e-8:first=i+1;break
 comparisons.append(dict(base=version,new='V724',same_normalized_initial=a['normalized_initial_state_hash']==b['normalized_initial_state_hash'],same_model_bytes=a['model_sha256']==b['model_sha256'],first_physical_or_control_difference_public_step=first,maximum_displacement_delta_m=b['maximum_displacement_m']-a['maximum_displacement_m'],closest_goal_improvement_m=a['closest_goal_distance_m']-b['closest_goal_distance_m'],not_same_later_observation_input=first is not None,independent_new_confirmation_samples=0))
assert all(x['same_normalized_initial']and x['same_model_bytes']for x in comparisons)
out=dict(status='CLOSED_PILOT_TRAJECTORIES_AND_ACCOUNT_COMPARISON_COMPLETE',v724_final_status=final['status'],summaries=summaries,comparisons=comparisons,new_initializations=0,new_integrations=0,training_updates=0,scope='Three sequential implementations on one observed old development case; divergent later observations, unequal total compute. Not independent confirmation, success-rate gain or global superiority.')
(root/'RESULT.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
with (root/'metrics.csv').open('w',newline='')as f:
 keys=[k for k in summaries[0]if k!='first_discovery'];w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(summaries)
fig,axes=plt.subplots(1,2,figsize=(12,4.7),constrained_layout=True)
p=read(pairs['V724']/'STATIC_PROTOCOL.json')
for r in p['known_rectangles']:
 x,y,hx,hy=r;axes[0].add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,facecolor='.82',edgecolor='.55'))
for x,y,r in p['known_circles']:axes[0].add_patch(Circle((x,y),r,facecolor='.82',edgecolor='.55'))
for version,color in [('V712','#666666'),('V721','#2563eb'),('V724','#d97706')]:
 rows=allrows[version];xy=np.asarray([p['start_qpos'][:2]]+[r['qpos_full'][:2]for r in rows]);t=np.arange(len(xy))*.08;d=np.linalg.norm(xy-np.asarray(p['goal_xy']),axis=1)
 axes[0].plot(xy[:,0],xy[:,1],color=color,label=version,lw=2);axes[0].scatter(*xy[-1],color=color,s=25,zorder=4)
 axes[1].plot(t,d,label=version,color=color,lw=2)
axes[0].set(xlim=(-4.6,-1.7),ylim=(-3.0,-1.15),aspect='equal',xlabel='x (m)',ylabel='y (m)',title='Executed paths near the starting area')
axes[1].set(xlabel='Simulation time (s)',ylabel='Euclidean goal distance (m)',title='Actual progress toward the same goal');axes[1].grid(alpha=.2)
axes[0].legend();axes[1].legend();fig.savefig(root/'executed_comparison.png',dpi=220);plt.close(fig)
text=['# V724恢复选择实际对照分析','',final['status']+'。以下均为同一已观察原开发例，不能计算独立总体成功率。','', '| 版本 | 实际结果 | 公开步 | 最大位移m | 最近目标m | 原生最低净空m |','|---|---|---:|---:|---:|---:|']
for x in summaries:text.append('| '+x['version']+' | '+x['outcome']+' | '+str(x['public_steps'])+' | %.6f | %.6f | %.6f |'%(x['maximum_displacement_m'],x['closest_goal_distance_m'],x['minimum_native_clearance_m']))
text+=['','原模型和规范初态匹配；首个完整状态/控制分叉与实际计算见下，分叉之后不能称同一观测输入：','',json.dumps(comparisons,ensure_ascii=False,indent=2),'','导航/重放/私有与额外排序计算：','']
for x in summaries:text.append(x['version']+'：'+str([x[k]for k in ['navigation_native_steps','replay_native_steps','private_integrations']])+'；墙钟'+str(x['wall_seconds'])+'秒；新排序可见性次数/排序墙钟'+str([x['extra_selection_visibility_evaluations'],x['extra_selection_wall_seconds']])+'。')
text+=['','原始状态图：[实际轨迹与目标进展](../runs/v725_progress_observation_postmortem/executed_comparison.png)。图中只有已执行状态，没有补画到达。','', '原全部安全/因果/控制/覆盖/尾与重放门按V724独立终审原结果保留；若功能未到达或审核失败，不能以零接触或某一进展指标替代。V723诊断1064旧重放/16656私有/4592副本验证另计，零新导航。V725新增初始化/积分/训练0。','', '后续问题应由新批实际终点及所有拒绝候选、缓存尾和真实观测是否持续续证来定位，不能自动调参或换任务凑通过。三路线联合导航与24确认/三重复、外部公平对比仍是独立后续步骤。']
(repo/'docs/RPCCR_PROGRESS_OBSERVATION_V724_ANALYSIS.md').write_text('\n'.join(text)+'\n')
assert all(sha(repo/n)==h for n,h in freeze['files'].items())
print(json.dumps({k:v for k,v in out.items()if k!='summaries'}))
