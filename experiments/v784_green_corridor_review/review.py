"""Compare original all-forward global proposals with actual failed execution.
Read-only saved data; no model, prediction or integration.
"""
import hashlib,json,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
r=Path(__file__).resolve().parents[2];raw=r/'runs/v778_global_retained_reentry/v780_main01/paired';cell=raw/'geometry_memory';out=r/'runs/v784_green_corridor_review';out.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
attachment=Path('/tmp/codex-clipboard-281f442f-aef3-46e2-888a-ce9a3886c948.png');shutil.copy2(attachment,out/'USER_GREEN_ROUTE_REFERENCE.png')
protocol=read(raw/'STATIC_PROTOCOL.json');actor=read(raw/'DYNAMIC_PROTOCOL.json');plans=[(p,read(p))for p in sorted(cell.glob('planning_*.json'))];execution=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];ad=[json.loads(s)for s in(cell/'model_admission.jsonl').read_text().splitlines()];dec=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()];details=[]
for p,x in plans:
 path=np.asarray(x['path']);assert path.ndim==2 and path.shape[1]==4
 details.append(dict(step=x['step'],path_points=len(path),status=x['stats']['status'],all_forward=bool(np.all(path[:,3]==1)),reverse_points=int(np.sum(path[:,3]<0)),central_opening_pose=path[np.argmin(abs(path[:,0]))].tolist(),path_sha256=sha(p)))
starts=[x for x in ad if x['status']=='RETAINED_REVERSE_BRAKE_CONTRACT'and x['contract_native_cursor']==0];failures=[]
for a in starts:
 decision=next(x for x in dec if x['step']==a['step']and x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY');failures.append(dict(step=a['step'],time_before_action_s=a['step']*.08,nominal_candidates=len(decision['candidates']),time_clearance_rejected=sum(x['reason']=='TIME_CLEARANCE'for x in decision['candidates']),backup_target=a['recovery_kind'],old_certificate_step=a['retained_from_step'],predicted_reverse_goal_loss_m=float(np.linalg.norm(np.asarray(a['predicted_end_pose'])[:2]-protocol['goal_xy'])-np.linalg.norm(np.asarray(execution[a['step']-1]['qpos_full'])[:2]-protocol['goal_xy']))))
assert len(details)==4 and all(x['all_forward']for x in details)and [x['step']for x in failures]==[98,153] and all(x['nominal_candidates']==x['time_clearance_rejected']==25 for x in failures)
summary=dict(status='USER_ROUTE_INTENT_AND_GLOBAL_CONTROL_DISCREPANCY_VERIFIED',user_image_sha256=sha(out/'USER_GREEN_ROUTE_REFERENCE.png'),user_intent='sustained forward travel through central opening then continue to goal; online dynamic avoidance',user_drawn_line_not_metric_or_dynamic_safety_certificate=True,all_global_plans_forward=True,global_plans=details,controller_reverse_starts=failures,original_outcome=read(cell/'result.json')['outcome'],new_model_initializations=0,new_integrations=0,new_predictions=0,new_navigation=0,route_controller_changed=False,unknown_actor_truth_not_added_to_online_inputs=True)
(out/'RESULT.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
# A scientific diagram, not an edit of the user's image. Green is the original planner's path.
fig,(ax,zx)=plt.subplots(1,2,figsize=(12,5),layout='constrained');path=np.asarray(plans[0][1]['path']);xy=np.asarray([x['qpos_full'][:2]for x in execution])
for plot in [ax,zx]:
 for cx,cy,hx,hy in protocol['known_rectangles']:plot.add_patch(Rectangle((cx-hx,cy-hy),2*hx,2*hy,color='#b8bec7'))
 for cx,cy,rad in protocol['known_circles']:plot.add_patch(Circle((cx,cy),rad,color='#b8bec7'))
 plot.plot(path[:,0],path[:,1],c='#149447',lw=2.5,label='Original global path (all forward)');plot.plot(xy[:,0],xy[:,1],c='#be382f',lw=2,label='Actual failed execution');plot.scatter(*protocol['start_qpos'][:2],marker='o',s=38,c='#2467a5',zorder=5,label='Start');plot.scatter(*protocol['goal_xy'],marker='*',s=95,c='#2467a5',zorder=5,label='Goal');plot.set_aspect('equal');plot.grid(alpha=.2);plot.set(xlabel='x (m)',ylabel='y (m)')
for i in [28,84,140,196]:
 d=path[i+4,:2]-path[i,:2];ax.annotate('',xy=path[i+4,:2],xytext=path[i,:2],arrowprops=dict(arrowstyle='->',color='#149447',lw=1.7))
center=np.asarray(actor['anchor_xy'])+np.sin(actor['phase_rad'])*actor['amplitude_m']*np.asarray(actor['axis_xy']);ax.add_patch(Circle(center,.1,color='#dd8b24',label='Actor at t=0 (evaluation only)'))
for number,x in enumerate(failures,1):
 q=np.asarray(execution[x['step']-1]['qpos_full']);zx.scatter(q[0],q[1],s=50,c='#9532a0',marker='x',zorder=5);zx.annotate(f"Fallback {number}: step {x['step']}",(q[0],q[1]),xytext=(-3.8,-1.60+number*.13),arrowprops=dict(arrowstyle='-',lw=.6),fontsize=8)
ax.set(xlim=(-5,5),ylim=(-5,5),title='The planner already proposes forward travel');zx.set(xlim=(-4.3,-2.7),ylim=(-2.3,-1.2),title='Reverse comes from the backup controller');ax.legend(fontsize=7,loc='upper right');zx.legend(fontsize=7,loc='lower left')
figure=r/'docs/figures/RPCCR_GREEN_CORRIDOR_REVIEW_V784';fig.savefig(str(figure)+'.png',dpi=180);fig.savefig(str(figure)+'.pdf');plt.close(fig)
report=r/'docs/RPCCR_GREEN_CORRIDOR_REVIEW_V784.md';report.write_text('''# 用户绿线与全局控制机制核对\n\n用户要求车辆沿图示通路持续前行，通过中央开口并到达右侧目标。手绘是通行方向意图，不是精确的整车曲率/动态安全证书；真实动态位置不进入线上控制。\n\n保存的4次全局路径均GLOBAL_GOAL_PATH、所有节点gear=+1、倒车节点0，均通过中央开口；原路线与用户绿线的右侧具体形状不同，不能说逐点相同。原初始路线x≈0时y≈-.801m，所选静态通路明确存在。\n\n实际倒车出自第98、153步控制器安全回退：当时25/25普通候选均TIME_CLEARANCE，遂执行前一步已经冻结的REVERSE_BRAKE尾；不是全局路径要求倒车。原保留后备评分还含反向位移奖励。直接照着绿线强制前进会绕开当前未知域安全门，不能当作算法已解决；同样不能只删除倒车然后在无新证书时随意停车。\n\n后续实现应保持朝全局目标的前进通行意图，将退让前的风险预警、可认证减速/观察及恢复前进联合选择；以有符号路径进度和后续可续证性考核，避免只以局部净空选择深倒车。可控前进将失证时提前选择新的完整安全合同，而不是等25个候选全拒后才执行深倒车。必要的短退让仍须完整物理证书，之后有明确的回归前进条件。具体绕动态障碍的路径由实时因果观测确定。\n\n这是一项零模型/零积分的保存证据核对，未改控制器、未新导航，不能称已按绿线跑通。后续仍需完整场地从起点至目标的冻结开发、完整发现/制动/重规划/续行/到达和原全部安全/状态重放审核；旧失败不改。\n\n图中绿色为原算法实际保存的全局规划路径，红色为实际执行，不是对用户原图的像素重建。\n''',encoding='utf-8');print(json.dumps(summary,indent=2,ensure_ascii=False))
