"""Independent zero-integration V697 final evidence and budget audit."""
import hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];src=Path(__file__).resolve().parent
root=repo/'runs/v697_rpccr_dynamic_initialization';window=root/'development01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=read(window/'COMPLETION.json');ledger=read(root/'ROUND_WINDOW.json');freeze=read(src/'CANDIDATE_FREEZE.json')
checks={'frozen_files_unchanged':all(sha(repo/n)==h for n,h in freeze['files'].items()),
        'closed':c['round_closed'] and ledger['round_closed'],
        'within_registered_window':ledger['elapsed_s']<=3605 and ledger['absolute_deadline_unix']-ledger['started_unix']==3600,
        'preflight24_passed':(window/'INITIALIZATION_AUDIT.json').exists() and read(window/'INITIALIZATION_AUDIT.json')['status']=='PASS',
        'three_registered_navigation_runs':len(c['results'])==3 and [x['name'] for x in c['results']]==['anchor_phase0','original_slot12','original_slot12_repeat'],
        'algorithm_and_training_unchanged':ledger['algorithm_revisions']==ledger['supervised_gradient_updates']==ledger['sac_gradient_updates']==0}
details=[]
for record in c['results']:
    pair=repo/record['run'];r=record['result'];local={}
    for filename,status in [('INDEPENDENT_CANONICAL_AUDIT.json','ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'),('ROUTE_COMMITMENT_AUDIT.json','PASS'),('PROJECTION_LEARNING_AUDIT.json','PASS'),('DISCOVERY_CHAIN_AUDIT.json','PASS'),('NATIVE_REPLAY_AUDIT.json','MATCHED_RECORDED_PUBLIC_STATES')]:
        local[filename]=(pair/filename).exists() and read(pair/filename)['status']==status
    local['strict_arrival']=r is not None and r['strict_safe_arrival'] and r['goal_distance_m']<=.45
    local['source_result_matches']=r is not None and r==read(pair/'geometry_memory/result.json')
    local['native_contact_clearance']=r is not None and r['minimum_dynamic_native_clearance_m']>=.15 and r['root_mutations_outside_mjstep']==0 and all(r['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records'])
    local['replay_length']=local['NATIVE_REPLAY_AUDIT.json'] and read(pair/'NATIVE_REPLAY_AUDIT.json')['replay_integration_steps']==r['physics_steps']==8*r['public_steps']
    details.append({'name':record['name'],'checks':{k:bool(v) for k,v in local.items()},'passed':bool(all(local.values())),'public_steps':None if r is None else r['public_steps'],'native_steps':None if r is None else r['physics_steps'],'private_integrations':None if r is None else r['prediction_steps'],'goal_distance_m':None if r is None else r['goal_distance_m'],'minimum_clearance_m':None if r is None else r['minimum_dynamic_native_clearance_m']})
checks['all_physical_functional_evidence']=len(details)==3 and all(x['passed'] for x in details)
for name in ['anchor_phase0','original_slot12_repeat']:
    path=root/name/'paired/EXACT_REPEAT_AUDIT.json';checks[name+'_complete_equivalence']=path.exists() and read(path)['passed']
result={'status':'ALL_DEVELOPMENT_CHECKS_PASS' if all(checks.values()) else 'NOT_PASSED','checks':{k:bool(v) for k,v in checks.items()},'details':details,'navigation_native_steps':sum(x['native_steps'] or 0 for x in details),'private_integrations':sum(x['private_integrations'] or 0 for x in details),'independent_fresh_confirmation_trials':0,'simulation_steps_this_audit':0,'scope':'Initialization repair and original slot12 development only; no24 navigation acceptance or superiority claim.'}
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
