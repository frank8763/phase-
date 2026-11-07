"""Prepare one literature-informed, causally supported proposal-only revision."""
import ast
import hashlib
import json
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
old=repo/'experiments/v809_time_reference_global'
own=repo/'experiments/v812_soft_global_reference'
root=repo/'runs/v812_soft_global_reference'
assert not root.exists()
assert {p.name for p in own.iterdir()} == {'current_guide.py'}
read=lambda p:json.loads(p.read_text())
assert read(repo/'runs/v811_temporal_reference_diagnosis/FINAL_INDEPENDENT_AUDIT.json')['status']=='FIXED_SAVED_CAUSAL_DIAGNOSIS_AUDIT_PASS'
p=repo/'RPCCR_TEMPORAL_PROGRESS_LEDGER_20261105.json'
d=read(p);assert d['algorithm_revisions_started']==0
d.update(status='V812_PREPARING_ONLY_CANDIDATE',algorithm_revisions_started=1,
    candidate='V812_CURRENT_OCCUPANCY_SOFT_FORECAST_REFERENCE_AND_UNCHANGED_NATIVE_GATE')
p.write_text(json.dumps(d,indent=2)+'\n')
root.mkdir()
for p in old.iterdir():
    if p.is_file()and p.suffix in ['.py','.md','.json']and p.name!='CANDIDATE_FREEZE.json':
        (own/p.name).write_text(p.read_text().replace('v809_time_reference_global','v812_soft_global_reference'))
p=own/'future_guide.py';p.write_text('"""Current hard occupancy and soft future cost for references only."""\nfrom current_guide import route_world,HORIZON\n')
p=own/'run_static.py';s=p.read_text();assert s.count('from timed_reference import attach')==1;s=s.replace('from timed_reference import attach','from current_guide import attach');p.write_text(s)
# Preserve the original undetected spatial computation, including its original
# branch order and scores. Extra work exists only once a real detection exists.
p=own/'planner.py';s=p.read_text();a=s.index('def spatial_search(');b=s.index('\ndef timed_search(',a)
fn=s[a:b]
fn=fn.replace('work_limit=None):','work_limit=None,forward_only=False):',1)
fn=fn.replace('for gear in (1,-1):','for gear in ((1,) if forward_only else (1,-1)):',1)
fn=fn.replace('for piece,clearance,(gear,st) in zip(all_pieces,vals,choices):',
    """if getattr(field,'soft_forecast_state',None)is not None:
            soft=field.soft_forecast_cost(dense.reshape(-1,3)).reshape(len(choices),30).max(axis=1)
        else:soft=np.zeros(len(choices))
        for piece,clearance,(gear,st),heat in zip(all_pieces,vals,choices,soft):""")
fn=fn.replace("new+=.045*abs(st/max_steer)+.18*max(0.,.30-float(np.min(clearance)))",
    "new+=.045*abs(st/max_steer)+.18*max(0.,.30-float(np.min(clearance)))\n            if getattr(field,'soft_forecast_state',None)is not None:new+=.24*float(heat)")
s=s[:a]+fn+s[b:]
a=s.index('\ndef search(')
s=s[:a]+'''\ndef search(field,*args,**kwargs):
    if getattr(field,'soft_forecast_state',None)is None:
        return spatial_search(field,*args,**kwargs)
    preferred,ps=spatial_search(field,*args,**kwargs,forward_only=True)
    selected=preferred is not None
    if selected:path,stats=preferred,dict(ps)
    else:path,stats=spatial_search(field,*args,**kwargs)
    stats['spatial_soft_reference']={
        'forward_reference_selected':selected,'preferred_status':ps['status'],
        'preferred_expanded':ps.get('expanded',0),
        'original_bidirectional_fallback_called':not selected,
        'total_expanded':ps.get('expanded',0)+(0 if selected else stats.get('expanded',0)),
        'no_virtual_arrival_clock':True,'future_cost_is_soft':True,
        'does_not_authorize_execution':True}
    if path is not None:stats['soft_heat_at_path_nodes']=field.soft_forecast_cost(path[:,:3]).tolist()
    return path,stats
'''
p.write_text(s)
p=own/'audit_route_commitment.py';s=p.read_text();start=s.index(" if state['center']is None:");end=s.index(" error=abs",start)
s=s[:start]+" minimum=float(np.min(field.pose_values(path[index:min(len(path),index+26),:3])))\n"+s[end:];p.write_text(s)
p=own/'audit_projection_learning.py';s=p.read_text().replace("metadata['status']=='TIME_LABELLED_CURRENT_OCCUPANCY_REFERENCE'and metadata['beyond_horizon_is_uncertified_guidance']", "metadata['status']=='CURRENT_OCCUPANCY_WITH_SOFT_REACHABILITY'and metadata['reference_is_not_dynamic_execution_certificate']and metadata['all_actual_328_native_admission_unchanged']and metadata['all_original_657_coverage_unchanged']")
p.write_text(s)
p=own/'execute_development.py';s=p.read_text();start=s.index('unchanged();assert');end=s.index('with(repo/',start)
s=s[:start]+"unchanged();assert(repo/'REVIEW_PENDING').exists();assert read(root/'pre_navigation/FINAL_INDEPENDENT_AUDIT.json')['status']=='SOFT_REFERENCE_INDEPENDENT_QUALIFICATION_PASS';assert not(root/'ROUND_WINDOW.json').exists()\n"+s[end:]
s=s.replace("day=read(repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json');assert day['development_revisions_used']==1 and day.get('physical_batches_started',0)==0", "day=read(repo/'RPCCR_TEMPORAL_PROGRESS_LEDGER_20261105.json');assert day['algorithm_revisions_started']==1 and day.get('physical_batches_started',0)==0")
s=s.replace("deadline=day['development_absolute_deadline_unix']", "deadline=day['unique_absolute_deadline_unix']")
s=s.replace("('audit_time_reference.py',300)","('audit_proposal_separation.py',300)")
s=s.replace('V809_OUTER_TERMINATED','V812_OUTER_TERMINATED').replace('THREE_TIME_REFERENCE_MAIN_AND_REPEAT_PASSED','THREE_SOFT_REFERENCE_MAIN_AND_REPEAT_PASSED')
p.write_text(s)
p=own/'finalize_development.py';s=p.read_text().replace("'audit_time_reference.py']","'audit_proposal_separation.py']")
s=s.replace('THREE_TIME_REFERENCE_MAIN_AND_REPEAT_PASSED','THREE_SOFT_REFERENCE_MAIN_AND_REPEAT_PASSED').replace('THREE_TIME_REFERENCE_DEVELOPMENT_VERIFIED','THREE_SOFT_REFERENCE_DEVELOPMENT_VERIFIED')
s=s.replace('rpccr_time_reference_global_v809_20261104','rpccr_soft_global_reference_v812_20261105').replace('RPCCR_TIME_REFERENCE_GLOBAL_V809_REPORT.md','RPCCR_SOFT_GLOBAL_REFERENCE_V812_REPORT.md').replace('RP-CCR V809','RP-CCR V812')
s=s.replace('唯一科学新变化是V808资格已核验的时间标记参考，原执行控制安全合同不变。原V807失败不改写，本次不是新池确认。','新修订以当前占据和未来软代价引导全局空间参考，替换V809参考层6.56秒硬时间门；实际原完整动态控制安全合同及329/657覆盖不变。V809/V810原失败不改写，非新池确认或SANDO完整移植。')
p.write_text(s)
for p in own.glob('*.py'):ast.parse(p.read_text())
assert (own/'motion_tracker.py').read_bytes()==(old/'motion_tracker.py').read_bytes()
print(json.dumps(dict(status='ONE_CANDIDATE_PREPARED_NOT_FROZEN',models=0,integrations=0)))
