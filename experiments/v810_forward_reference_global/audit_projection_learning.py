"""Recompute only persisted causal projection and learned proposals; zero integration."""
import os,sys,json,argparse,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from future_guide import route_world
from union_belief import future_cells
from learned_proposer import Proposer
p=argparse.ArgumentParser();p.add_argument('paired');p.add_argument('--model');a=p.parse_args();root=Path(a.paired);cell=root/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
states={s['step']:s for s in lines(cell/'motion_estimate.jsonl')};r=read(cell/'result.json');records=[];all_plans=[]
for file in sorted(cell.glob('planning_*.json')):
    x=read(file);state=states[x['step']];new,metadata=route_world(x['causal_input'],state)
    assert new==x['causal_route_input']and metadata==x['route_projection_metadata']
    all_plans.append(x['step'])
    if state['center']is None:continue
    times=np.linspace(0,6.56,657);lower,upper=future_cells(state['outer_state_cells'],times)
    pl=np.asarray(state['position_lower']);pu=np.asarray(state['position_upper']);vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper']);tt=times[:,None]
    lo=np.maximum(pl+tt*vl-.02*tt*tt,pl-.12*tt)-1e-5;hi=np.minimum(pu+tt*vu+.02*tt*tt,pu+.12*tt)+1e-5
    excess=float(max(np.max(lo[:,None,:]-lower),np.max(upper-hi[:,None,:])));assert excess<=1e-7
    assert metadata['status']=='TIME_LABELLED_CURRENT_OCCUPANCY_REFERENCE'and metadata['beyond_horizon_is_uncertified_guidance']and len(new['rectangles'])==len(read(root/'STATIC_PROTOCOL.json')['known_rectangles'])+1
    records.append({'step':x['step'],'maximum_containment_excess':excess,'source_hidden_world_geometry_used':state['hidden_world_geometry_used']})

model=Proposer(a.model)if a.model else None;decisions=lines(cell/'control_decisions.jsonl');ad=lines(cell/'model_admission.jsonl');samples=lines(cell/'proposal_learning_samples.jsonl');inference_error=0.;learned_safe=learned_total=0
for x in decisions:
    if x['stage']!='NOMINAL':continue
    proposed=[c for c in x['candidates']if c['proposal_role']=='LEARNED']
    if model is None:assert not proposed
    else:
        # SPATIAL_PROPOSAL_UNAVAILABLE logs no candidate at all.
        if not x['candidates']:continue
        assert len(proposed)==1
        c=proposed[0];inference_error=max(inference_error,float(np.max(abs(model.predict(c['features'])-c['target_command']))));learned_total+=1;learned_safe+=c['reason']is None
checks={'causal_projection_sources':all(s['hidden_world_geometry_used']is False for s in states.values()),'all_registered_plans_recomputed':bool(all_plans) and len(all_plans)==len(list(cell.glob('planning_*.json'))) and len(records)==sum(states[k]['center']is not None for k in all_plans),'projection_contains_original_joint_cells':all(x['maximum_containment_excess']<=1e-7 for x in records),'model_sha_matches':r['proposal_model_sha256']==(None if model is None else model.sha256),'learned_inference_matches':inference_error<=1e-10,'teacher_samples_executed_only':all(s['step']<r['public_steps']and ad[s['step']]['status']=='MODEL_SAFE_COMMAND'and not ad[s['step']].get('observation_initialization')for s in samples),'course_distance_matches':abs(float(np.linalg.norm(np.asarray(read(root/'STATIC_PROTOCOL.json')['goal_xy'])-np.asarray(read(root/'STATIC_PROTOCOL.json')['start_qpos'])[:2]))-r['course_distance_m'])<=1e-12}
out={'status':'PASS'if all(checks.values())else'FAIL','checks':{k:bool(v)for k,v in checks.items()},'planning_records':records,'all_recomputed_plan_steps':all_plans,'tracked_projection_count':len(records),'learned_candidates_total':learned_total,'learned_candidates_safe':int(learned_safe),'maximum_learned_target_error':inference_error,'learned_actual_ordinary_steps':sum(s['selected_role']=='LEARNED'for s in samples),'ordinary_teacher_sample_count':len(samples),'verification_integrations':0,'scope':'causal geometric proposal containment and actual finite learned-target participation, not learned model superiority'}
(root/'PROJECTION_LEARNING_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='planning_records'},indent=2));assert out['status']=='PASS'
