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
prefix=0;error=0.
if starts:
    assert len(starts)==1 and starts[0]['step']==295
    repo=Path(__file__).resolve().parents[2];old=repo/'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory'
    with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as aa,gzip.open(old/'dynamic_native.jsonl.gz','rt')as bb:
        for i,(x,y)in enumerate(zip(aa,bb)):
            if i>=295*8:break
            x,y=json.loads(x),json.loads(y);error=max(error,max(float(np.max(abs(np.asarray(x[k])-y[k])))for k in['qpos_full','qvel_full','actual_ctrl','mocap_pos']));prefix+=1
    assert prefix==295*8 and error<=1e-8
out=dict(status='EARLY_JOINT_INDEPENDENT_PASS',checks=dict(causal_guard=True,bounded_joint_search=True,complete_native_certificates=True,original_prefix_exact=True,references_causal=True),records=records,first_trigger=None if not starts else starts[0]['step'],pre_trigger_native=prefix,pre_trigger_error=error,new_models=0,new_integrations=0)
(pair/'EARLY_JOINT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='records'}))
