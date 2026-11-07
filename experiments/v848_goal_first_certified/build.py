"""Prepare one new scientific candidate; never edit any previous experiment."""
import ast
import hashlib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2]
C=Path(__file__).parent
OLD=R/'experiments/v842_staged_long_navigation'
W=R/'experiments/v848_goal_first_worker'
OPS=R/'experiments/v843_three_route_regression'
OUT=R/'runs/v848_goal_first_certified'
changes=[]


def replace(p,before,after):
    original=p.read_text()
    assert original.count(before)==1,(p.name,before[:100])
    p.write_text(original.replace(before,after))
    changes.append(dict(path=str(p.relative_to(R)),before=before,after=after))


def main():
    assert not W.exists()
    OUT.mkdir(exist_ok=False);W.mkdir()
    for p in OLD.iterdir():
        if p.is_file()and p.suffix in ['.py','.json']and p.name!='CANDIDATE_FREEZE.json':
            (W/p.name).write_bytes(p.read_bytes())
    for name in ['common.py','engine.py','audit_entry.py','registration.py','repeat.py','finalize.py','os_watch.py','start.py','TASK_LIST.json','REGISTERED_TASKS.json','qualify.py']:
        (C/name).write_bytes((OPS/name).read_bytes())
    for p in C.glob('*.py'):
        if p.name=='build.py':continue
        s=p.read_text().replace('v843_three_route_regression','v848_goal_first_certified').replace('v842_staged_long_navigation','v848_goal_first_worker').replace('v843_','v848_').replace('V843','V848')
        p.write_text(s)
    (W/'TASK_LIST.json').write_bytes((C/'TASK_LIST.json').read_bytes())
    protocol=C/'PROTOCOL.md'
    (W/'PROTOCOL.md').write_bytes(protocol.read_bytes())
    replace(W/'run_static.py',"'v842_staged_long_navigation'/a.name","'v848_goal_first_worker'/a.name")
    replace(W/'run_static.py',"'V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS'","'V848_GOAL_REFERENCE_AND_FIRST_CERTIFIED_NOMINAL'")
    p=W/'planner.py';s=p.read_text();marker='\ndef search(field,*args,**kwargs):'
    assert s.count(marker)==1
    old=s[s.index(marker):]
    new='''
def reference_choice(field,goal,forward,forward_stats,bidirectional,bidirectional_stats):
    """Complete target first, then strictly better original grid heuristic; forward ties."""
    if forward is None:return False
    if bidirectional is None:return True
    if forward_stats['status']=='GLOBAL_GOAL_PATH':return True
    if bidirectional_stats['status']=='GLOBAL_GOAL_PATH':return False
    field.free=field.clearance>=.15-field.config.resolution/math.sqrt(2)
    guide=field.base_heuristic(field,np.asarray(goal,float))if hasattr(field,'base_heuristic')else None
    def h(path):
        xy=path[-1,:2];eu=float(np.linalg.norm(xy-goal))
        if guide is None:return eu
        idx=field.indices([xy])[0]
        if(idx>=0).all()and(idx<guide.shape).all()and np.isfinite(guide[tuple(idx)]):return max(eu,float(guide[tuple(idx)]))
        return eu+20.
    return h(forward)<=h(bidirectional)+.02


def search(field,*args,**kwargs):
    if getattr(field,'soft_forecast_state',None)is None:
        return spatial_search(field,*args,**kwargs)
    preferred,ps=spatial_search(field,*args,**kwargs,forward_only=True)
    alternate=None;bs=None
    called=preferred is None or ps['status']!='GLOBAL_GOAL_PATH'
    if called:alternate,bs=spatial_search(field,*args,**kwargs)
    selected=reference_choice(field,np.asarray(args[1],float),preferred,ps,alternate,bs)
    path,stats=(preferred,dict(ps))if selected else(alternate,dict(bs))
    stats['spatial_soft_reference']={
        'forward_reference_selected':selected,'preferred_status':ps['status'],
        'preferred_expanded':ps.get('expanded',0),
        'original_bidirectional_fallback_called':called,
        'total_expanded':ps.get('expanded',0)+(0 if bs is None else bs.get('expanded',0)),
        'no_virtual_arrival_clock':True,'future_cost_is_soft':True,
        'does_not_authorize_execution':True}
    stats['goal_first_policy']={
        'version':'V848_COMPLETE_GOAL_THEN_ORIGINAL_HEURISTIC_FORWARD_TIE',
        'forward_path':None if preferred is None else preferred.tolist(),
        'bidirectional_path':None if alternate is None else alternate.tolist(),
        'forward_stats':ps,'bidirectional_stats':bs,'bidirectional_called':called,
        'selected_forward':selected,'thresholds_unchanged':True}
    if path is not None:stats['soft_heat_at_path_nodes']=field.soft_forecast_cost(path[:,:3]).tolist()
    return path,stats
'''
    p.write_text(s[:s.index(marker)]+new);changes.append(dict(path=str(p.relative_to(R)),before=old,after=new))
    replace(W/'early_joint.py',"return list(dict.fromkeys(choices))","return sorted(set(choices))")
    replace(W/'early_joint.py',"emit(cell,'control_decisions.jsonl',dict(step=step,candidate_role='ORDINARY',stage='EARLY_JOINT_APPEND',**row))", "emit(cell,'control_decisions.jsonl',dict(step=step,candidate_role='ORDINARY',stage='EARLY_JOINT_APPEND',**row))\n            if summary is not None:break")
    replace(W/'early_joint.py',"selection='max(complete328_minimum+.5*complete_goal_gain,nominal_score,-rank); all original gates plus336 continuation'", "selection_policy='FIRST_FEASIBLE_IN_NOMINAL_ORDER_V848',selection='first original nominal-ranked representative with complete328 and336 continuation; no later representative evaluated'")
    replace(W/'early_joint.py',"early_joint_probes=len(ranks)","early_joint_probes=len(records)")
    replace(W/'early_joint_independent.py',"expected=list(dict.fromkeys(indexes))", "expected=list(dict.fromkeys(indexes))\n    first=event.get('selection_policy')=='FIRST_FEASIBLE_IN_NOMINAL_ORDER_V848'\n    if first:expected=sorted(expected)")
    replace(W/'early_joint_independent.py',"assert event['hidden_world_geometry_used']is False and len(event['probes'])==len(expected)","assert event['hidden_world_geometry_used']is False\n    if first:\n        assert 0<len(event['probes'])<=len(expected)\n        assert [p['rank']for p in event['probes']]==expected[:len(event['probes'])]\n        good=[p for p in event['probes']if p['summary']is not None]\n        assert (len(good)==1 and good[0]is event['probes'][-1])if event['selected_rank']is not None else(not good and len(event['probes'])==len(expected))\n    else:assert len(event['probes'])==len(expected)")
    replace(W/'early_joint_independent.py',"selected=max(admitted,key=lambda x:x[:3])[-1]if admitted else None","selected=(admitted[0][-1]if first else max(admitted,key=lambda x:x[:3])[-1])if admitted else None")
    replace(W/'audit_early_joint.py',"result['source_revision'].startswith('V842')or result['source_revision'].startswith('V841')", "result['source_revision'].startswith(('V848','V842','V841'))")
    replace(W/'audit_early_joint.py',"first=starts[0]['step'];old=repo/anchors[seed]", "first=starts[0]['step']\n    if result['source_revision'].startswith('V848'):\n        affected=[p['step']for p in plans if 'goal_first_policy'in p['stats']]\n        if affected:first=min(first,min(affected))\n    old=repo/anchors[seed]")
    replace(W/'audit_proposal_separation.py',"fallback_account=policy['original_bidirectional_fallback_called']==(not selected)", "fallback_account=(policy['original_bidirectional_fallback_called']==r['stats']['goal_first_policy']['bidirectional_called'])if 'goal_first_policy'in r['stats']else(policy['original_bidirectional_fallback_called']==(not selected))")
    # Register V843 as the actual same-physics NS pre-intervention anchor.
    replace(C/'registration.py',"10010002:'runs/v827_goal_route_validation/repeat_slot02/paired/geometry_memory'", "10010002:'runs/v842_staged_long_navigation/v843_main_slot02/paired/geometry_memory'")
    # Qualification uses the genuine old saved V842 episode, not this new output directory.
    replace(C/'qualify.py',"base=RAW/'long_main08/paired'", "base=R/'runs/v842_staged_long_navigation/long_main08/paired'")
    replace(C/'qualify.py',"assert prefix_anchor(task['seed'])==actual/'geometry_memory'", "assert prefix_anchor(task['seed']).is_dir()")
    # The archived old stage's source snapshot remains old, as required by its canonical audit.
    p=C/'qualify.py';assert p.read_text().count("RAW/'development12'")==2;p.write_text(p.read_text().replace("RAW/'development12'","R/'runs/v842_staged_long_navigation/development12'"))
    # New stage adds independent audit of the changed reference and selection policy.
    replace(C/'common.py',"def tasks():", "AUDITS.append(('audit_candidate_policy.py','CANDIDATE_POLICY_AUDIT.json',1200))\ndef tasks():")
    replace(C/'qualify.py',"expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses'];", "expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses'];expected['audit_candidate_policy.py']='GOAL_FIRST_CERTIFIED_POLICY_PASS';")
    # Exact hard root stop is fixed by this evening's user authorization, never a rolling window.
    replace(C/'start.py',"deadline=started+43200", "deadline=1794009600.;assert deadline-started>6500,'INSUFFICIENT_NIGHT_REMAINING'")
    # Repeated operational revision counters are changed together below.
    # There are multiple plain text counters in the inherited operational script.
    p=C/'start.py';p.write_text(p.read_text().replace('scientific_revisions=0','scientific_revisions=1').replace('V842_SCIENTIFIC_WORKER_UNCHANGED_THREE_ROUTE_REGRESSION','V848_GOAL_REFERENCE_AND_FIRST_CERTIFIED_NOMINAL'))
    p=C/'common.py';p.write_text(p.read_text().replace("RAW=R/'runs/v848_goal_first_worker'", "RAW=R/'runs/v848_goal_first_worker'"))
    # Keep all three original task bytes, old science and the exact new-source diff.
    (OUT/'SOURCE_CHANGE_RECORD.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
    for base in [C,W]:
        for p in base.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    print(json.dumps(dict(prepared=True,new_worker=str(W.relative_to(R)),changes=len(changes),models=0,integrations=0)))


if __name__=='__main__':main()
