"""Independent early trigger, joint controller, source-prefix and reference audit."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
from early_joint_independent import check
ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);a=ap.parse_args();pair=a.pair;cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(x)for x in p.open()]if p.exists()else[]
protocol=read(pair/'STATIC_PROTOCOL.json');events=lines(cell/'early_joint_decisions.jsonl');starts=lines(cell/'early_joint_activation.jsonl');ad={x['step']:x for x in lines(cell/'model_admission.jsonl')};nom={x['step']:x for x in lines(cell/'control_decisions.jsonl')if x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY'};execution=lines(cell/'v648_execution.jsonl');records=[]
plans=[read(p)for p in cell.glob('planning_*.json')]
for e in events:
    step=e['step'];assert step in nom and np.array_equal(e['real_qpos'],execution[step-1]['qpos_full'])
    check(cell,e,nom[step]['candidates'],protocol,deep=True)
    assert any(p['step']<=step and p['path']==e['reference_path']for p in plans)
    if e['selected_rank']is not None:
        assert ad[step]['early_joint_selection']and ad[step]['joint_admission_distinct_command_rank']==e['selected_rank']
    records.append(dict(step=step,probes=len(e['probes']),selected_rank=e['selected_rank']))
for s in starts:
    step=s['step'];assert s['guard_m']==.155+.08*3.28 and s['previous_reserve_minimum_m']<s['guard_m']and not s['hidden_world_geometry_used']
    old=ad[step-1];assert old['recovery_reserve']['reserve_minimum_clearance_m']==s['previous_reserve_minimum_m']
for e in lines(cell/'early_joint_replan.jsonl'):
    assert e['observed_this_frame']and not e['authorizes_control']and e['step']-e['last_plan']>=12 and any(p['step']==e['step']for p in plans)
prefix=0;error=0.;budget_prefix=0;budget_error=0.
repo=Path(__file__).resolve().parents[2];result=read(cell/'result.json');seed=result['seed'];states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')}
if starts:
    assert len(starts)==1
    if result['source_revision'].startswith(('V848','V842','V841')):
        eligible=[step for step in sorted(nom)if step>0 and states[step]['center']is not None and ad.get(step-1,{}).get('recovery_reserve',{}).get('reserve_minimum_clearance_m',float('inf'))<.155+.08*3.28]
        assert eligible and starts[0]['step']==eligible[0],'FIRST_CAUSAL_TRIGGER_NOT_EXACT'
    anchors={10060002:'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory',10060008:'runs/v828_goal_dynamic_confirmation/main_slot08/paired/geometry_memory'}
    assert seed in anchors,'UNREGISTERED_PREFIX_ANCHOR'
    first=starts[0]['step']
    if result['source_revision'].startswith('V848'):
        affected=[p['step']for p in plans if 'goal_first_policy'in p['stats']]
        if affected:first=min(first,min(affected))
    old=repo/anchors[seed]
    with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as aa,gzip.open(old/'dynamic_native.jsonl.gz','rt')as bb:
        for i,(x,y)in enumerate(zip(aa,bb)):
            if i>=first*8:break
            x,y=json.loads(x),json.loads(y);error=max(error,max(float(np.max(abs(np.asarray(x[k])-y[k])))for k in['qpos_full','qvel_full','actual_ctrl','mocap_pos']));prefix+=1
    assert prefix==first*8 and error<=1e-8
if seed==10060002 and result['source_revision'].startswith('V842'):
    old=repo/'runs/v841_early_joint/main_slot01/paired/geometry_memory';expected=min(result['physics_steps'],3112)
    with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as aa,gzip.open(old/'dynamic_native.jsonl.gz','rt')as bb:
        for i,(x,y)in enumerate(zip(aa,bb)):
            if i>=expected:break
            x,y=json.loads(x),json.loads(y);budget_error=max(budget_error,max(float(np.max(abs(np.asarray(x[k])-y[k])))for k in['qpos_full','qvel_full','actual_ctrl','mocap_pos']));budget_prefix+=1
    assert budget_prefix==expected and budget_error<=1e-8,'BUDGET_ONLY_CONTROLS_OR_STATES_CHANGED'
out=dict(status='EARLY_JOINT_INDEPENDENT_PASS',checks=dict(causal_guard=True,bounded_joint_search=True,complete_native_certificates=True,original_prefix_exact=True,references_causal=True),records=records,first_trigger=None if not starts else starts[0]['step'],pre_trigger_native=prefix,pre_trigger_error=error,budget_only_native_prefix=budget_prefix,budget_only_native_error=budget_error,new_models=0,new_integrations=0)
(pair/'EARLY_JOINT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='records'}))
