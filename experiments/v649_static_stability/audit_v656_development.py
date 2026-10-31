"""Independent zero-simulation gate for the six fixed-work development runs."""
import gzip
import hashlib
import json
from itertools import zip_longest
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2]
root=repo/'runs/v656_static_deterministic_work';window=root/'development02'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frozen=read(window/'SOURCE_FREEZE.json');docs=read(window/'DOCUMENT_FREEZE.json')
source=repo/'experiments/v656_static_deterministic_work'
records=[];repeats=[]
for seed,scene in [(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]:
    branch=[]
    for prefix in ['dev30_seed','dev30_repeat']:
        pair=root/f'{prefix}{seed}_{scene}/paired';cell=pair/'geometry_memory'
        result=read(cell/'result.json');native=read(pair/'NATIVE_REPLAY_AUDIT.json')
        execution=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()]
        trace=read(cell/'trace.json');admission=[json.loads(s)for s in(cell/'model_admission.jsonl').read_text().splitlines()]
        digest=hashlib.sha256();count=0
        with gzip.open(cell/'contacts.jsonl.gz','rb')as stream:
            for line in stream:digest.update(line);count+=1
        snapshot=pair.parent/'source_snapshot'
        old=repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
        checks={'snapshot':read(snapshot/'SHA256.json')==frozen and all(sha(snapshot/n)==h for n,h in frozen.items()),
                'raw_contact_sha_and_count':digest.hexdigest()==result['contacts']['contact_log_content_sha256']and count==result['contacts']['all_contact_records'],
                'strict_goal':result['strict_safe_arrival']and result['outcome']=='GOAL'and result['goal_distance_m']<=.45,
                'zero_contacts':all(result['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records'])and native['replay_obstacle_contact_records']==0,
                'counts':len(execution)==len(trace)==len(admission)==result['public_steps']and result['physics_steps']==native['replay_integration_steps']==8*len(trace),
                'state_replay':native['status']=='MATCHED_RECORDED_PUBLIC_STATES'and native['maximum_full_public_qpos_error']<=1e-8 and native['maximum_full_public_qvel_error']<=1e-8,
                'clearance':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']>=.15-1e-8 and native['reconstructed_native_states_below_015']==0,
                'self_domain':native['minimum_reconstructed_self_domain_margin_m']>=0 and result['minimum_actual_self_domain_margin_m']>=0 and result['self_geometry_checked_native_ticks']==result['physics_steps'],
                'same_model_as_v651':sha(pair/'scene_model.mjb')==native['scene_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256']==read(old/'STATIC_PROTOCOL.json')['full_model_sha256'],
                'same_initial_as_v651':result['normalized_initial_state_hash']==read(old/'geometry_memory/result.json')['normalized_initial_state_hash'],
                'causal_static_native':all(x['hidden_world_geometry_used']is False for x in admission)and result['static_obstacle_pose_unchanged']and result['root_mutations_outside_mjstep']==0}
        record={'name':pair.parent.name,'passed':all(checks.values()),'checks':checks,'public_steps':result['public_steps'],
                'native_steps':result['physics_steps'],'minimum_native_clearance_m':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']}
        records.append(record);branch.append((pair,result,execution))
    (a,ar,ae),(b,br,be)=branch
    errors={k:float(np.max(np.abs(np.array([x[k]for x in ae])-np.array([x[k]for x in be]))))if len(ae)==len(be)else None for k in ['qpos_full','qvel_full','ctrl']}
    xml=sha(a/'assets/isolated_indoor.xml');xml_same=xml==sha(b/'assets/isolated_indoor.xml');different=0;contact_count=0
    with gzip.open(a/'geometry_memory/contacts.jsonl.gz','rt')as left,gzip.open(b/'geometry_memory/contacts.jsonl.gz','rt')as right:
        for x,y in zip_longest(left,right):
            if x is None or y is None:different+=1;continue
            x,y=json.loads(x),json.loads(y);contact_count+=1
            for row,pair in [(x,a),(y,b)]:
                for geom in ['geom1','geom2']:
                    basis=row.get('classification_basis',{}).get(geom,{})
                    if'xml'in basis:
                        p=Path(basis['xml']);assert p.is_absolute()and p.resolve()==(pair/'assets/isolated_indoor.xml').resolve()
                        basis['xml']={'relative':'assets/isolated_indoor.xml','sha256':xml}
            different+=int(x!=y)
    checks={'full_state_ctrl':all(v is not None and v<=1e-8 for v in errors.values()),'same_xml_bytes':xml_same,
            'all_contact_events_equal_except_verified_xml_path':different==0,
            'same_normalized_initial':ar['normalized_initial_state_hash']==br['normalized_initial_state_hash']}
    repeats.append({'seed':seed,'scene':scene,'passed':all(checks.values()),'checks':checks,'maximum_errors':errors,
                    'contact_records':contact_count,'non_path_contact_differences':different})
checks={'six_physical_audits':len(records)==6 and all(x['passed']for x in records),
        'three_full_repeats':len(repeats)==3 and all(x['passed']for x in repeats),
        'source_and_protocol_frozen':all(sha(source/n)==h for n,h in frozen.items())and all(sha(source/n)==h for n,h in docs.items()),
        'zero_sim_clock_replay':read(root/'FIXED_WORK_ZERO_SIM_REPLAY.json')['passed'],
        'bounded_completion':read(window/'COMPLETION.json')['elapsed_s']<=read(window/'WINDOW.json')['limit_s']}
result={'development_passed':all(checks.values()),'static_acceptance_passed':False,'checks':checks,
        'runs':records,'repeats':repeats,'simulation_steps':0,'dynamic_started':False,'training_updates':0}
(root/'INDEPENDENT_DEVELOPMENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'development_passed':result['development_passed'],'checks':checks,'native_steps_audited':sum(x['native_steps']for x in records),'minimum_native_clearance_m':min(x['minimum_native_clearance_m']for x in records)},indent=2))
