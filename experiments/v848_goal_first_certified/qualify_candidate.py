"""Fast old-red/new-green feedback and genuine saved complete-certificate tests, zero models."""
import copy
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('NEW_POLICY_QUALIFICATION_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
import numpy as np
from common import R,C,W,ROOT,read,dump,sha
sys.path.insert(0,str(R/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'));sys.path.insert(0,str(W))
import planner
import early_joint
from early_joint_independent import check


def main():
    number=1
    while (ROOT/f'policy_qualification_{number:02d}').exists():number+=1
    out=ROOT/f'policy_qualification_{number:02d}';out.mkdir(exist_ok=False)
    old_spec=importlib.util.spec_from_file_location('old_planner',R/'experiments/v842_staged_long_navigation/planner.py')
    old=importlib.util.module_from_spec(old_spec);old_spec.loader.exec_module(old)
    source=R/'runs/v842_staged_long_navigation/v843_main_slot02/paired/geometry_memory'
    plan=read(source/'planning_1198.json');counter=[x for x in read(R/'runs/v847_gpu_reference_diagnosis/references/RESULTS.json')if x['step']==1198][0]
    a=np.asarray(plan['path']);b=np.asarray(counter['path']);fs=plan['stats'];bs=counter['stats']
    fake=SimpleNamespace(soft_forecast_state={},soft_forecast_cost=lambda p:np.zeros(len(p)))
    def search(*args,forward_only=False,**kwargs):return(a,dict(fs))if forward_only else(b,dict(bs))
    old.spatial_search=search
    old_path,old_stats=old.search(fake,plan['pose'],plan['causal_route_input']['goal'],1.,.5)
    assert old_stats['status']=='SAFE_PROGRESS_PREFIX'and np.array_equal(old_path,a)
    original=planner.spatial_search;planner.spatial_search=search
    try:new_path,new_stats=planner.search(fake,plan['pose'],plan['causal_route_input']['goal'],1.,.5)
    finally:planner.spatial_search=original
    assert new_stats['status']=='GLOBAL_GOAL_PATH'and np.array_equal(new_path,b)
    dump(out/'OLD_RED_NEW_GREEN.json',dict(old_complete_target_selected=False,new_complete_target_selected=True,
         actual_wrapper_executed=True,old_endpoint_goal_m=fs['goal_distance_m'],new_endpoint_goal_m=bs['goal_distance_m'],
         old_reference_source_sha256=sha(source/'planning_1198.json'),models=0,integrations=0))
    # Independently audit all four fixed real causal searches, without running new search.
    from audit_candidate_policy import check_plan
    protocol=read(source.parent/'STATIC_PROTOCOL.json')
    states={r['step']:r for r in map(json.loads,(source/'motion_estimate.jsonl').open())}
    qualified=[]
    for row in read(R/'runs/v847_gpu_reference_diagnosis/references/RESULTS.json'):
        p=read(source/f'planning_{row["step"]:04d}.json');af=np.asarray(p['path']);ab=np.asarray(row['path']);fstats=p['stats'];bstats=row['stats']
        from exact_footprint import build
        from current_guide import attach
        spec=importlib.util.spec_from_file_location('F',R/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
        f=build(F,p['causal_route_input']);f.base_heuristic=F.base._heuristic_grid;attach(f,states[p['step']])
        selected=planner.reference_choice(f,np.asarray(protocol['goal_xy']),af,fstats,ab,bstats)
        st=copy.deepcopy(fstats if selected else bstats)
        st['spatial_soft_reference']=dict(forward_reference_selected=selected,total_expanded=fstats.get('expanded',0)+bstats.get('expanded',0))
        st['goal_first_policy']=dict(version='V848_COMPLETE_GOAL_THEN_ORIGINAL_HEURISTIC_FORWARD_TIE',forward_path=af.tolist(),bidirectional_path=ab.tolist(),forward_stats=fstats,bidirectional_stats=bstats,bidirectional_called=True,selected_forward=selected,thresholds_unchanged=True)
        r=dict(step=p['step'],path=(af if selected else ab).tolist(),stats=st,causal_route_input=p['causal_route_input'])
        assert check_plan(r,protocol,states[p['step']]);qualified.append(dict(step=p['step'],selected_forward=selected,status=st['status']))
        bad=copy.deepcopy(r);bad['stats']['goal_first_policy']['selected_forward']=not selected
        try:check_plan(bad,protocol,states[p['step']])
        except AssertionError:pass
        else:raise AssertionError('WRONG_REFERENCE_CHOICE_NOT_REJECTED')
    # Invoke the actual new online selection with real saved certificates, no model stand-in physics.
    events=list(map(json.loads,(source/'early_joint_decisions.jsonl').open()))
    nom={r['step']:r for r in map(json.loads,(source/'control_decisions.jsonl').open())if r['stage']=='NOMINAL'and r['candidate_role']=='ORDINARY'}
    execution=list(map(json.loads,(source/'v648_execution.jsonl').open()));records=[];negatives=4
    selected_events=[e for e in events if any(p['summary']is not None for p in e['probes'])][:4]
    for e in selected_events:
        cell=out/f'step{e["step"]:04d}';cell.mkdir()
        for p in source.iterdir():
            if p.name not in ['early_joint','control_decisions.jsonl','early_joint_decisions.jsonl']:(cell/p.name).symlink_to(p,target_is_directory=p.is_dir())
        unique=[];seen=set()
        for c in sorted([c for c in nom[e['step']]['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True):
            key=tuple(c['first_command'])
            if key in seen:continue
            seen.add(key);z=np.load(source/'nominal_forecasts'/c['nominal_saved_forecast'])
            unique.append((c['score'],np.asarray(c['first_command']),z['poses'],c['nominal_spatial_minimum_clearance_m'],c['self_domain_margin_m']))
        probes={p['rank']:p for p in e['probes']};calls=[]
        real=SimpleNamespace(qpos=np.asarray(e['real_qpos']),qvel=np.asarray(execution[e['step']-1]['qvel_full']),ctrl=np.asarray(execution[e['step']-1]['ctrl']),time=float(e['step']*.08))
        class SavedCertificates:
            cache=None;cursor=0;expected=None;expected_ctrl=None;finish_pending=False;proactive=False
            public_goal_xy=protocol['goal_xy'];early_joint_started_step=e['started_step']
            def admit_nominal(self,real,command,field,state,step):
                rank=next(i for i,c in enumerate(unique)if np.array_equal(c[1],command));calls.append(rank);probe=probes[rank]
                self.last_attempt=copy.deepcopy(probe['detail'])
                if probe['summary']is not None:
                    import gzip
                    with gzip.open(source/probe['certificate'],'rt')as stream:self.cache=json.load(stream)
                    self.cache['qpos']=np.asarray(self.cache['qpos'])
                return copy.deepcopy(probe['summary'])
        reserved=SavedCertificates();gate=dict(segment_end_index=len(e['reference_path'])-1)
        output=early_joint.select(reserved,None,real,gate,None,None,e['step'],np.asarray(e['reference_path']),e['reference_index'],cell,unique)
        event=list(map(json.loads,(cell/'early_joint_decisions.jsonl').open()))[-1]
        assert output is not None and calls==event['representative_ranks'][:len(calls)]and event['selected_rank']==calls[-1]
        assert check(cell,event,nom[e['step']]['candidates'],protocol,deep=True,source_cell=source)
        for label,mutate in [('wrong_selection',lambda x:x.update(selected_rank=99)),('missing_probes',lambda x:x.update(probes=[])),('bad_command',lambda x:x['probes'][0]['first_command'].__setitem__(0,9.))]:
            bad=copy.deepcopy(event);mutate(bad)
            try:check(cell,bad,nom[e['step']]['candidates'],protocol,deep=True,source_cell=source)
            except (AssertionError,IndexError,KeyError):negatives+=1
            else:raise AssertionError('NEGATIVE_NOT_REJECTED_'+label)
        records.append(dict(step=e['step'],new_probes=len(calls),old_probes=len(e['probes']),chosen_rank=event['selected_rank'],complete_native_certificate_independently_verified=True))
    assert len(records)==4
    dump(ROOT/'POLICY_QUALIFICATION.json',dict(passed=True,old_red_new_green=True,reference_queries=qualified,actual_selection_saved_certificates=records,negative_cases=negatives,model_initializations=0,integrations=0,training=0))
    print(json.dumps(read(ROOT/'POLICY_QUALIFICATION.json')),flush=True)


if __name__=='__main__':main()
