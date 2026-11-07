"""Persisted t0 checks, without MuJoCo integration or online truth input."""
import hashlib,json,sys
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2];src=Path(__file__).resolve().parent
window=Path(sys.argv[1]);read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tasks=read(src/'ORIGINAL_V696_TASK_LIST.json');rows=read(window/'PREFLIGHTS.json')
parent=repo/'experiments/v695_discovery_verified_fixture'
old=repo/'runs/v695_discovery_verified_fixture/phase0/paired'
old_start=read(old/'STATIC_PROTOCOL.json')['start_qpos'];old_model=sha(old/'scene_model.mjb')
checks={'all24_in_original_order':[x['task'] for x in rows]==tasks,
        'original_task_bytes':sha(src/'ORIGINAL_V696_TASK_LIST.json')==sha(repo/'experiments/v696_discovery_fresh_confirmation/TASK_LIST.json'),
        'all_unchanged_inherited_sources':all(sha(src/p.name)==sha(p) for p in parent.glob('*.py') if (src/p.name).exists() and p.name not in ['factory.py','run_static.py','execute.py']),
        'only_output_namespace_changed_in_runner':(src/'run_static.py').read_text().replace("/'v697_rpccr_dynamic_initialization'/a.name","/'v695_discovery_verified_fixture'/a.name")== (parent/'run_static.py').read_text()}
details=[];packets=[];calls=[]
for record in rows:
    task=record['task'];pair=repo/record['run'];provenance=read(pair/'INITIALIZATION_PROVENANCE.json')
    initial=read(pair/'INITIAL_UNSEEN.json');protocol=read(pair/'STATIC_PROTOCOL.json');actor=read(pair/'DYNAMIC_PROTOCOL.json')
    local={'fixed_bootstrap':provenance['bootstrap_seed']==95000011,
           'distinct_task_noise_seed':provenance['task_noise_seed']==task['seed']==protocol['seed'],
           'bootstrap_zero_time':provenance['initial_time']==0.,
           'unchanged_legacy_gate':provenance['legacy_task_gate_unchanged'],
           'same_full_model_as_old_anchor':sha(pair/'scene_model.mjb')==old_model,
           'same_full_vehicle_initial_state':np.array_equal(protocol['start_qpos'],old_start),
           'same_goal':protocol['goal_xy']==[4.,-2.],
           'registered_actor_phase':actor['phase_rad']==task['phase'],
           'sensor_channels':len(initial['packet']['lidar'])==32 and len(initial['packet']['depth'])==15,
           'all_t0_gates':initial['passed'] and all(initial['checks'].values()),
           'actual_task_feasible':read(pair/'TASK_FEASIBILITY.json')['eligible'],
           'nonblocking':actor['swept_envelope_reference']['eligible'] and actor['protected_junction_clearance_of_sweep_m']>=.05}
    details.append({'slot':task['slot'],'checks':{k:bool(v) for k,v in local.items()},'passed':bool(all(local.values()))})
    packets.append(hashlib.sha256(json.dumps(initial['packet'],sort_keys=True).encode()).hexdigest())
    calls.append({k:v for k,v in provenance['noise_call_state_after_bootstrap'].items() if k.endswith('_call')})
checks.update(all24_model_sensor_scene_checks=len(details)==24 and all(x['passed'] for x in details),
              distinct_seeded_t0_packets=len(set(packets))==24,
              identical_bootstrap_sensor_call_counts=all(x==calls[0] for x in calls))
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':{k:bool(v) for k,v in checks.items()},'details':details,'initial_packet_sha256':packets,'bootstrap_sensor_call_counts':calls,'simulation_steps':0,'navigation_trials':0,'scope':'Reused task-list setup verification; not a new24 navigation confirmation or proof of algorithm superiority.'}
(window/'INITIALIZATION_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'failed_checks':[k for k,v in checks.items() if not v],'bad_slots':[x['slot'] for x in details if not x['passed']]}));assert all(checks.values())
