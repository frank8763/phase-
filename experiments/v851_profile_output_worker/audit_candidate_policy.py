"""Independently reconstruct the new policy, complete geometry, and exact old prefix."""
import argparse
import gzip
import importlib.util
import json
import math
from pathlib import Path
import numpy as np
from exact_footprint import pose_values
from independent_soft_reference import field,dense_path

R=Path(__file__).resolve().parents[2]


def independent_choice(world,goal,forward,fs,alternate,bs):
    if forward is None:return False
    if alternate is None or fs['status']=='GLOBAL_GOAL_PATH':return True
    if bs['status']=='GLOBAL_GOAL_PATH':return False
    spec=importlib.util.spec_from_file_location('original_footprint',R/'current/footprint_map_b70_v513.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    # The independent geometric box below is deliberately not a search grid.
    # Reconstruct the original public grid separately for the original heuristic.
    f=mod.FootprintMap(world)
    f.free=f.clearance>=.15-f.config.resolution/math.sqrt(2)
    guide=mod.base._heuristic_grid(f,np.asarray(goal,float))
    def cost(path):
        eu=float(np.linalg.norm(path[-1,:2]-goal));idx=f.indices([path[-1,:2]])[0]
        if guide is not None and(idx>=0).all()and(idx<guide.shape).all()and np.isfinite(guide[tuple(idx)]):return max(eu,float(guide[tuple(idx)]))
        return eu+20. if guide is not None else eu
    return cost(forward)<=cost(alternate)+.02


def check_plan(record,protocol,state):
    policy=record['stats']['goal_first_policy'];f=field(protocol,state);goal=np.asarray(protocol['goal_xy'])
    forward=None if policy['forward_path']is None else np.asarray(policy['forward_path'])
    alternate=None if policy['bidirectional_path']is None else np.asarray(policy['bidirectional_path'])
    fs=policy['forward_stats'];bs=policy['bidirectional_stats']
    assert policy['version']=='V848_COMPLETE_GOAL_THEN_ORIGINAL_HEURISTIC_FORWARD_TIE'
    assert policy['thresholds_unchanged'] and policy['bidirectional_called']==(forward is None or fs['status']!='GLOBAL_GOAL_PATH')
    for p,s in [(forward,fs),(alternate,bs)]:
        if s is not None:assert 0<=s.get('expanded',0)<=16000
        if p is None:continue
        minimum=float(pose_values(f,dense_path(p)).min());distance=float(np.linalg.norm(p[-1,:2]-goal))
        assert minimum>=s['guard_m']-1e-8 and abs(minimum-s['minimum_clearance_m'])<=1e-8
        assert abs(distance-s['goal_distance_m'])<=1e-8
        if s['status']=='GLOBAL_GOAL_PATH':assert distance<.28
    selected=independent_choice(record['causal_route_input'],goal,forward,fs,alternate,bs)
    assert policy['selected_forward']==selected
    chosen=forward if selected else alternate
    assert (chosen is None and record['path']is None)or(chosen is not None and np.array_equal(chosen,record['path']))
    account=record['stats']['spatial_soft_reference']
    assert account['forward_reference_selected']==selected
    assert account['total_expanded']==fs.get('expanded',0)+(0 if bs is None else bs.get('expanded',0))
    return True


def main():
    ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);a=ap.parse_args();cell=a.pair/'geometry_memory'
    read=lambda p:json.loads(p.read_text());protocol=read(a.pair/'STATIC_PROTOCOL.json');result=read(cell/'result.json')
    states={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').open())}
    plans=[read(p)for p in sorted(cell.glob('planning_*.json'))]
    changed=[p for p in plans if 'goal_first_policy'in p['stats']]
    for p in changed:check_plan(p,protocol,states[p['step']])
    events=list(map(json.loads,(cell/'early_joint_decisions.jsonl').open()))if(cell/'early_joint_decisions.jsonl').exists()else[]
    if result['source_revision'].startswith(('V850','V848')):
        assert all(e.get('selection_policy')=='FIRST_FEASIBLE_IN_NOMINAL_ORDER_V848'for e in events)
        assert all('goal_first_policy'in p['stats']for p in plans if states[p['step']]['center']is not None)
    anchors={10010002:'runs/v842_staged_long_navigation/v843_main_slot02/paired/geometry_memory',10010001:'runs/v827_goal_route_validation/main_slot01/paired/geometry_memory',10010003:'runs/v827_goal_route_validation/main_slot03/paired/geometry_memory'}
    count=0;error=0.;first=None
    if result['source_revision'].startswith(('V850','V848')):
        assert result['seed']in anchors
        first=min([p['step']for p in changed]+[e['step']for e in events]+[result['public_steps']])
        with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as aa,gzip.open(R/anchors[result['seed']]/'dynamic_native.jsonl.gz','rt')as bb:
            for x,y in zip(aa,bb):
                if count>=first*8:break
                x,y=json.loads(x),json.loads(y)
                error=max(error,max(float(np.max(abs(np.asarray(x[k])-y[k])))for k in ['qpos_full','qvel_full','actual_ctrl','mocap_pos']));count+=1
        assert count==first*8 and error<=1e-8,'PRE_INTERVENTION_NATIVE_STATE_CONTROL_CHANGED'
    out=dict(status='GOAL_FIRST_CERTIFIED_POLICY_PASS',checks=dict(causal_complete_reference_policy=True,original_hard_geometry=True,early_selection_registered=True,old_prefix_exact=True),
             changed_plans=len(changed),early_joint_events=len(events),pre_intervention_public=first,pre_intervention_native=count,maximum_prefix_error=error,models=0,integrations=0)
    (a.pair/'CANDIDATE_POLICY_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))


if __name__=='__main__':main()
