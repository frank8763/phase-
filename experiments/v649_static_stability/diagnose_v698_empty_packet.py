"""Zero-integration diagnosis; preserve original frozen FAIL and all denominators."""
import ast,gzip,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np

repo=Path(__file__).resolve().parents[2];root=repo/'runs/v698_rpccr_dynamic_confirmation'
src=repo/'experiments/v697_rpccr_dynamic_initialization';sys.path.insert(0,str(src))
from range_circle_memory import measured_rays
from motion_tracker import Tracker
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(root/'ROUND_WINDOW.json')['round_closed'],'ROUND_STILL_RUNNING'
freeze=read(repo/'experiments/v698_rpccr_dynamic_confirmation/CANDIDATE_FREEZE.json')
assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED'
node=next(n for n in ast.parse((src/'audit_discovery.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='rays')
scope={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),str(src/'audit_discovery.py'),'exec'),scope)
original_rays=scope['rays'];details=[];inputs={};packet_count=empty_count=0;maximum_numeric_error=0.
for slot in range(1,14):
    pair=repo/'runs/v697_rpccr_dynamic_initialization'/f'v698_slot{slot:02d}'/'paired';cell=pair/'geometry_memory'
    packet_file=cell/'sensor_packets.jsonl.gz';inputs[str(packet_file.relative_to(repo))]=sha(packet_file)
    audit_file=pair/'DISCOVERY_CHAIN_AUDIT.json';inputs[str(audit_file.relative_to(repo))]=sha(audit_file)
    mismatches=[];scalar_mismatches=[];semantic_mismatches=[];empty_steps=[];packets=[]
    with gzip.open(packet_file,'rt') as stream:
        for line in stream:
            p=json.loads(line);packets.append(p);packet_count+=1;rr=original_rays(p)
            scalar=measured_rays(SimpleNamespace(robot_xy=np.asarray(p['xy']),robot_yaw=p['yaw'],phase17c_last_lidar=np.asarray(p['lidar']),phase17c_lidar_max_range=p['lidar_max_range'],phase17c_last_depth=np.asarray(p['depth']),phase17c_depth_max_range=p['depth_max_range']))
            saved=np.asarray(p['rays'],float)
            assert isinstance(p['rays'],list) and all(isinstance(row,list) and len(row)==7 for row in p['rays']),'MALFORMED_NONEMPTY_RAY_ROWS'
            canonical=saved.reshape(-1,7)
            if p['rays']==[]:empty_steps.append(p['step']);empty_count+=1
            if not np.array_equal(rr,p['rays']):mismatches.append({'step':p['step'],'reconstructed_shape':list(rr.shape),'json_decoded_shape':list(saved.shape),'empty_json':p['rays']==[]})
            if not np.array_equal(scalar,canonical):scalar_mismatches.append(p['step'])
            if not np.array_equal(rr,canonical):semantic_mismatches.append(p['step'])
            if len(canonical):maximum_numeric_error=max(maximum_numeric_error,float(np.max(abs(rr-canonical))))
    original=read(audit_file)
    details.append({'slot':slot,'packets':len(packets),'empty_ray_steps':empty_steps,'original_comparison_mismatches':mismatches,'scalar_online_function_mismatch_steps':scalar_mismatches,'schema_preserving_vector_mismatch_steps':semantic_mismatches,'original_chain_status':original['status'],'original_failed_checks':[k for k,v in original['checks'].items() if not v]})
    if slot==13:
        protocol=read(pair/'STATIC_PROTOCOL.json');tracker=Tracker();states=[]
        for p in packets:
            _,state=tracker.update_rays(np.asarray(p['rays'],float).reshape(-1,7),protocol['known_rectangles'],protocol['known_circles'],p['time'])
            states.append({'step':p['step'],**state})
        saved_states=[json.loads(s) for s in (cell/'motion_estimate.jsonl').read_text().splitlines()]
        details[-1]['all_saved_causal_states_exact_from_schema_typed_packets']=states==saved_states
        inputs[str((cell/'motion_estimate.jsonl').relative_to(repo))]=sha(cell/'motion_estimate.jsonl')

# The semantic observation is a list of seven-field rows. No numeric tolerance,
# row deletion, failure replacement, or online-state alteration is introduced.
checks={'original_batch_failed':read(root/'FINAL_INDEPENDENT_AUDIT.json')['status']=='NOT_PASSED',
        'original_slot13_chain_fail_unchanged':details[12]['original_chain_status']=='FAIL' and details[12]['original_failed_checks']==['all_raw_packets_reconstructed'],
        'first12_original_audits_pass':all(d['original_chain_status']=='PASS' and not d['original_comparison_mismatches'] for d in details[:12]),
        'every_original_difference_is_empty_shape':bool(details[12]['original_comparison_mismatches']) and all(x['empty_json'] and x['reconstructed_shape']==[0,7] and x['json_decoded_shape']==[0] for d in details for x in d['original_comparison_mismatches']),
        'all_packets_exact_under_unchanged_seven_field_schema':all(not d['scalar_online_function_mismatch_steps'] and not d['schema_preserving_vector_mismatch_steps'] for d in details),
        'slot13_causal_state_exact':details[12]['all_saved_causal_states_exact_from_schema_typed_packets'],
        'numeric_difference_zero':maximum_numeric_error==0.,
        'empty_shape_regression_reproduced':not np.array_equal(np.empty((0,7)),[]) and np.array_equal(np.empty((0,7)),np.asarray([],float).reshape(-1,7)),
        'changed_numeric_value_remains_rejected':not np.array_equal(np.ones((1,7)),np.nextafter(np.ones((1,7)),np.inf)),
        'all_read_inputs_unchanged':all(sha(repo/n)==h for n,h in inputs.items()),
        'all_frozen_inputs_unchanged':all(sha(repo/n)==h for n,h in freeze['files'].items())}
result={'status':'EMPTY_JSON_SHAPE_ONLY_CAUSE_VERIFIED' if all(checks.values()) else 'DIAGNOSIS_NOT_ESTABLISHED','checks':{k:bool(v) for k,v in checks.items()},'packets_checked':packet_count,'empty_packets':empty_count,'maximum_nonempty_numeric_error':maximum_numeric_error,'details':details,'original_evidence_sha256':inputs,'diagnostic_source_sha256':sha(Path(__file__)),'simulation_integrations':0,'training_updates':0,'new_navigation_trials':0,'original_confirmation_status_not_changed':'NOT_PASSED','original_completed_chain_audits_passed':12,'actual_strict_arrival_results':13,'remaining_main_navigation_unexecuted':11,'confirmation_repeats_unexecuted':3,'scope':'Offline semantic representation diagnosis only. Existing FAIL/COMPLETION/independent audit and locked24 denominator are immutable; this does not resume or pass the confirmation.'}
(root/'EMPTY_PACKET_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['details','original_evidence_sha256']},indent=2));assert all(checks.values())
