"""Independent offline gate for V657, recomputing physical and repeat evidence.

Does not trust the batch's final booleans, never alters original outcomes,
never imports an online runner or creates a simulator.
"""
import gzip
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2]
root=repo/'runs/v657_static_fixed_work_confirmation';window=root/'confirmation01'
def read(path,default=None):return json.loads(path.read_text())if path.exists()else default
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
frozen=read(window/'SOURCE_FREEZE.json',{})
documents=read(window/'DOCUMENT_FREEZE.json',{})
selection=read(window/'SELECTION_FREEZE.json',{})
tasks=selection.get('tasks',[]);rows=read(window/'CONFIRMATION_RESULTS.json',[])
ledger=read(window/'LEDGER.json',[]);done=read(window/'COMPLETION.json',{})
src=repo/'experiments/v657_static_fixed_work_confirmation'
records=[]

def audit_pair(pair):
    cell=pair/'geometry_memory';r=read(cell/'result.json');native=read(pair/'NATIVE_REPLAY_AUDIT.json')
    if not r or not native:
        record={'pair':str(pair.relative_to(repo)),'passed':False,'reason':'missing full result/native replay'}
        records.append(record);return record
    protocol=read(pair/'STATIC_PROTOCOL.json');trace=read(cell/'trace.json',[])
    execution=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()]
    admissions=[json.loads(s)for s in(cell/'model_admission.jsonl').read_text().splitlines()]
    snapshot=pair.parent/'source_snapshot'
    h=hashlib.sha256();contacts=0;anomalies=0
    with gzip.open(cell/'contacts.jsonl.gz','rb')as stream:
        for line in stream:
            h.update(line);contacts+=1;c=json.loads(line)
            if c['contact_type']in ['robot_obstacle','unknown']:anomalies+=1
    plans={int(p.stem.split('_')[-1])for p in cell.glob('planning_*.json')}
    f=cell/'gear_transitions.jsonl';switches={json.loads(s)['step']for s in f.read_text().splitlines()}if f.exists()else set()
    bypass=[b['step']for a,b in zip(admissions[:-1],admissions[1:])if a['active_gear']!=b['active_gear']and b['step']not in plans and b['step']not in switches]
    checks={'snapshot':read(snapshot/'SHA256.json')==frozen and all(sha(snapshot/n)==h for n,h in frozen.items()),
            'contact_digest_and_count':h.hexdigest()==r['contacts']['contact_log_content_sha256']and contacts==r['contacts']['all_contact_records'],
            'zero_obstacle_and_unknown_contacts':anomalies==0 and all(r['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']),
            'public_native_counts':len(trace)==len(execution)==len(admissions)==r['public_steps']and r['physics_steps']==8*len(trace)==native['replay_integration_steps'],
            'model':sha(pair/'scene_model.mjb')==protocol['full_model_sha256']==native['scene_model_sha256']and protocol['model_sha256']=='4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f',
            'native_replay':native['status']=='MATCHED_RECORDED_PUBLIC_STATES'and native['maximum_full_public_qpos_error']<=1e-8 and native['maximum_full_public_qvel_error']<=1e-8,
            'native_clearance':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']>=.15-1e-8 and native['reconstructed_native_states_below_015']==0 and native['replay_obstacle_contact_records']==0,
            'self_domain':native['minimum_reconstructed_self_domain_margin_m']>=0 and r['minimum_actual_self_domain_margin_m']>=0 and r['self_geometry_checked_native_ticks']==r['physics_steps'],
            'native_only_static':r['static_obstacle_pose_unchanged']and r['root_mutations_outside_mjstep']==0,
            'causal_and_cusp':not bypass and all(x['hidden_world_geometry_used']is False for x in admissions),
            'unknown_count':len(protocol['physical_unknown_obstacles'])==(1 if protocol['scene']=='single_event'else 2)}
    record={'pair':str(pair.relative_to(repo)),'passed':all(checks.values()),'checks':checks,
            'native_steps':r['physics_steps'],'public_steps':r['public_steps'],
            'minimum_native_clearance_m':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']}
    records.append(record);return record


def compare_contacts_independent(a,b):
    # Independent implementation of the protocol; do not call the driver's helper.
    xml_a=sha(a/'assets/isolated_indoor.xml');xml_b=sha(b/'assets/isolated_indoor.xml')
    if xml_a!=xml_b:return {'passed':False,'reason':'different XML bytes'}
    count=0;different=0
    with gzip.open(a/'geometry_memory/contacts.jsonl.gz','rt')as x,gzip.open(b/'geometry_memory/contacts.jsonl.gz','rt')as y:
        for left,right in zip_longest(x,y):
            if left is None or right is None:return {'passed':False,'reason':'contact length mismatch'}
            count+=1;left,right=json.loads(left),json.loads(right)
            for row,pair in [(left,a),(right,b)]:
                for key in ['geom1','geom2']:
                    basis=row.get('classification_basis',{}).get(key,{})
                    if'xml'in basis:
                        path=Path(basis['xml'])
                        if not path.is_absolute()or path.resolve()!=(pair/'assets/isolated_indoor.xml').resolve():
                            return {'passed':False,'reason':'unregistered XML path'}
                        basis['xml']={'relative':'assets/isolated_indoor.xml','verified_content_sha256':xml_a}
            if left!=right:different+=1
    return {'passed':different==0,'contact_records':count,'non_path_differences':different,'xml_sha256':xml_a}

success=[]
for i,row in enumerate(rows):
    task=tasks[i]if i<len(tasks)else{}
    pair=root/row['name']/'paired';record=audit_pair(pair);r=read(pair/'geometry_memory/result.json',{})
    same=(row['seed'],row['scene'])==(task.get('seed'),task.get('scene'))and read(pair/'STATIC_PROTOCOL.json',{}).get('full_model_sha256')==task.get('scene_model_sha256')
    success.append(bool(record['passed']and same and r.get('strict_safe_arrival')and r.get('goal_distance_m',1) <=.45))
repeats=[]
for seed,scene in [(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]:
    pair=root/f'repeat_{seed}_{scene}/paired';base=repo/'runs/v656_static_deterministic_work'/f'dev30_seed{seed}_{scene}/paired'
    r=read(pair/'geometry_memory/result.json')
    if not r:
        repeats.append({'seed':seed,'scene':scene,'passed':False,'reason':'not completed'});continue
    record=audit_pair(pair);old=read(base/'geometry_memory/result.json')
    a=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    b=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    errors={k:float(np.max(np.abs(np.array([x[k]for x in a])-np.array([x[k]for x in b]))))if len(a)==len(b)and a else None for k in ['qpos_full','qvel_full','ctrl']}
    contact=compare_contacts_independent(base,pair)
    same=record['passed']and contact['passed']and r['strict_safe_arrival']and r['outcome']==old['outcome']=='GOAL'and r['normalized_initial_state_hash']==old['normalized_initial_state_hash']and read(base/'STATIC_PROTOCOL.json')['full_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256']and all(v is not None and v<=1e-8 for v in errors.values())
    repeats.append({'seed':seed,'scene':scene,'passed':bool(same),'maximum_full_state_error':errors,'contact_comparison':contact,
                    'raw_contact_sha_equal':r['contacts']['contact_log_content_sha256']==old['contacts']['contact_log_content_sha256']})
screened=[x for x in ledger if x['feasibility_only']]
expected=[]
for scene in ['single_event','legacy_two']:
    expected +=[x for x in screened if x['scene']==scene and x['feasibility']and x['feasibility']['eligible']][:12]
expected.sort(key=lambda x:x['seed'])
references=len(expected)==24 and all(x['feasibility']['search']['minimum_clearance_m']>=.155-1e-8 and x['feasibility']['continuous_polygonal_pose_clearance_lower_bound_m']>=.15 and x['feasibility']['reference_goal_distance_m']<=.28 for x in expected)
parent=repo/'experiments/v656_static_deterministic_work';parent_hash=read(parent/'SOURCE_FREEZE.json');proof=read(src/'DECISION_EQUIVALENCE.json',{})
equivalence={}
for name in proof.get('files',{}):
    text=(src/name).read_text()
    if name=='run_static.py':text=text.replace("/'v657_static_fixed_work_confirmation'/a.name","/'v656_static_deterministic_work'/a.name")
    equivalence[name]=hashlib.sha256(text.encode()).hexdigest()==parent_hash[name]==sha(parent/name)
classes={s:sum(ok for row,ok in zip(rows,success)if row['scene']==s)for s in ['single_event','legacy_two']}
win=read(window/'WINDOW.json',{})
checks={'source_and_protocol_frozen':bool(frozen)and bool(documents)and all(sha(src/n)==h for n,h in frozen.items())and all(sha(src/n)==h for n,h in documents.items()),
        'unchanged_online_decisions':bool(equivalence)and all(equivalence.values()),
        'fresh_screening_order':bool(screened)and [x['seed']for x in screened]==list(range(95000001,95000001+len(screened))),
        'same_first12_each_locked24':len(tasks)==24 and [(x['seed'],x['scene'])for x in tasks]==[(x['seed'],x['scene'])for x in expected],
        'prelocked_before_first_navigation':bool(selection.get('locked_unix')and all(x['feasibility_only']for x in ledger[:len(screened)])),
        'registered_reference_requirements':references,'all24_attempts':len(rows)==24,'at_least23_audited_arrivals':sum(success)>=23,
        'single_at_least11':classes['single_event']>=11,'two_at_least11':classes['legacy_two']>=11,
        'all27_physical_audits':len(records)==27 and all(x['passed']for x in records),
        'three_full_state_and_exact_contact_repeats':all(x['passed']for x in repeats),
        'bounded_before_overnight_deadline':bool(done and done['elapsed_s']<=win['limit_s']and win['absolute_deadline_unix']<=win['overnight_absolute_deadline_unix'])}
result={'static_engineering_acceptance_passed':all(checks.values()),'checks':checks,
        'strict_audited_arrivals':sum(success),'class_successes':classes,'attempts':len(rows),
        'runs':records,'repeats':repeats,'source_equivalence':equivalence,'simulation_steps':0,'training_updates':0,'dynamic_started':False,
        'scope':'fresh selected finite benchmark; exact physical events with only preregistered verified XML provenance path normalization; old V652/V653 failures unchanged'}
(root/'INDEPENDENT_ACCEPTANCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
