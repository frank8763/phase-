"""Saved JSON evidence tables/plots/draft only; no planner/model/physics imports."""
from pathlib import Path
import csv,json,os,time
R=Path(__file__).resolve().parents[2];OUT=R/'runs/v1769_overnight_phase_campaign/paper';ROOT=R/'runs/v1643_formal_parent_metadata';read=lambda p:json.loads(p.read_text())
def main():
 os.sched_setaffinity(0,{4});OUT.mkdir(exist_ok=True);ledger=read(ROOT/'FORMAL_LEDGER.json');rows=[]
 for entry in ledger['rows']:
  aid=entry['assignment_id'];O=ROOT/'rounds'/aid;rv=read(O/'RUNTIME_CLOSED_REVIEW.json')if(O/'RUNTIME_CLOSED_REVIEW.json').exists()else{};p=rv.get('physical_telemetry')or{};replay=rv.get('replay')or{}
  rows.append(dict(assignment=aid,registered=bool(entry.get('registered')),closed=bool(entry.get('closed')),qualified_success=bool(entry.get('owner_passed')and entry.get('model_result')),actual_native=entry.get('actual_native'),own_replay_native=entry.get('own_replay_native'),goal_distance_m=p.get('goal_distance_m'),minimum_clearance_m=p.get('minimum_actual_clearance_m'),bad_contacts=p.get('bad_contacts'),replay_error=replay.get('maximum_qpos_qvel_ctrl_mocap_error'),audit_scope=rv.get('audit_scope'),source_version=entry.get('source_version_root'),first_error=(rv.get('first_error')or{}).get('error'),canonical_modelwork_total='unknown'))
 with(OUT/'FORMAL20.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 closed=sum(x['closed']for x in rows);success=sum(x['qualified_success']for x in rows);summary=dict(locked_denominator=20,closed=closed,qualified_success=success,non_success_closed=closed-success,unexecuted=20-sum(x['registered']for x in rows),q1159_and_worker_counts_are_subsets_total_unknown=True,known_course_new_phase_only=True,not_statistical_superiority=True,no_old_failed_task_repeated=True,created_unix=time.time());(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
 text='# 原合同新相位结果与论文材料\n\n本材料只汇总保存的真实RESULT、独立审核和正式账本；没有新积分、规划或重跑。\n\n固定20项：'+str(closed)+'项关闭，'+str(success)+'项完整合格成功，'+str(closed-success)+'项关闭非成功，未执行'+str(summary['unexecuted'])+'项。失败/技术censor及unknown保原分母，不能混旧weekend或暴露pilot。\n\n|任务|完整成功|actual/replay|末目标距离m|最小净空m|审核范围|首错|\n|---|---|---|---|---|---|---|\n'
 for r in rows:text+='|'+r['assignment']+'|'+str(r['qualified_success'])+'|'+str(r['actual_native'])+'/'+str(r['own_replay_native'])+'|'+str(r['goal_distance_m'])+'|'+str(r['minimum_clearance_m'])+'|'+str(r['audit_scope'])+'|'+str(r['first_error'])+'|\n'
 text+='\n实验解释：同已知课程新actor相位，route/sensorseed/模型/起终点/单actor与motionclass固定。WE full/no_onward仅执行前onward预检差分，EW full/no_time仅wait0候选资格，NS不造inactive消融。不同相位、不同合同及旧算法历史不可混作等条件独立样本。按4个成对EW/WE任务给描述性差分，不凭一两个成功声称统计优势、新地图泛化或实时保证。\n\n方法：原V1281 4cm/.035rad/.015steer、实际.15m净空、原保守预测储备、完整2200stop/200error尾与fullstate-ctrl-mocap1e-8、因果source/contact/self/root门保持。所有数值/Allocator/physics/replay仅CPU2 run_phase/execution.lock；EW单独spawn CPU2原优化器与原固定顺序/截止不变，父actual暂停。q1159和独立worker日志仅计数子集，normal/static/其他FFI/internalfactory总模型工作unknown，不能称equalwork。原四worker字段是历史元数据，实际资源以CPU2单worker记录为准。\n\n论文还需：将本表和配对机制图纳入Results；对首错分类功能拒绝/资源接口/独立证据缺口；逐例解释full/no_onward或full/no_time何时改善、何时无差；历史SCCR/DWA/Phase比较保持各自原实验合同，不能当成本新相位同平台全导航已比较；补Methods、局限性和复现索引。\n'
 (OUT/'RESULTS_METHODS_DRAFT.md').write_text(text)
 try:
  import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
  fig,axes=plt.subplots(2,1,figsize=(12,6),layout='constrained');labels=[x['assignment'].replace('phase_','').replace('__',' ')for x in rows];colors=['#27804b'if x['qualified_success']else'#b84b41'if x['closed']else'#b7bdc7'for x in rows]
  axes[0].bar(range(20),[1 if x['registered']else 0 for x in rows],color=colors);axes[0].set_ylim(0,1.15);axes[0].set_ylabel('Registered task');axes[0].set_title('Locked20: green complete qualified success, red closed non-success, grey unexecuted');axes[0].set_xticks(range(20),labels,rotation=65,ha='right')
  xs=[i for i,x in enumerate(rows)if x['minimum_clearance_m']is not None];axes[1].scatter(xs,[rows[i]['minimum_clearance_m']for i in xs],c=[colors[i]for i in xs]);axes[1].axhline(.15,color='black',linestyle='--',label='Original actual clearance floor');axes[1].set_ylabel('Minimum actual clearance (m)');axes[1].set_xticks(range(20),labels,rotation=65,ha='right');axes[1].legend();fig.savefig(OUT/'FORMAL20_STATUS.png',dpi=180);fig.savefig(OUT/'FORMAL20_STATUS.pdf');plt.close(fig)
 except Exception as e:(OUT/'PLOT_ERROR.json').write_text(json.dumps(dict(error=repr(e),no_scientific_outcome_changed=True))+'\n')
 print(json.dumps(summary))
if __name__=='__main__':main()
