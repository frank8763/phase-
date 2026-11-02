"""Meaningful rejection tests plus exact reconstruction of every existing packet."""
import ast,copy,gzip,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from ray_packet_contract import RayPacketSchemaError,decode_saved_rays,saved_rays_equal

repo=Path(__file__).resolve().parents[2];src=Path(__file__).resolve().parent;root=repo/'runs/v699_dynamic_packet_audit'
old=repo/'experiments/v697_rpccr_dynamic_initialization'
node=next(n for n in ast.parse((old/'audit_discovery.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='rays')
scope={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),str(old/'audit_discovery.py'),'exec'),scope);rays=scope['rays']
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unit=[]
def case(name,check):
    result=bool(check());unit.append({'name':name,'passed':result});assert result,name
def rejected(payload):
    try:decode_saved_rays(payload)
    except RayPacketSchemaError:return True
    return False
sample=np.array([[-4.,-2.,1.,0.,1.2,.06,.02],[-4.,-2.,0.,1.,1.1,.09,.03]])
case('valid_empty_json_roundtrip',lambda:saved_rays_equal(np.empty((0,7)),json.loads(json.dumps([]))))
case('valid_nonempty_roundtrip',lambda:saved_rays_equal(sample,json.loads(json.dumps(sample.tolist()))))
for name,payload in [('null',None),('dict',{}),('tuple',()),('scalar',0.),('flat',sample[0].tolist()),('empty_nested',[[]]),('six_fields',[[0.]*6]),('eight_fields',[[0.]*8]),('ragged',[sample[0].tolist(),[0.]*6]),('extra_nesting',[[[0.]*7]]),('string_field',[[*sample[0,:6],'0.02']]),('bool_field',[[True,*sample[0,1:]]]),('null_field',[[None,*sample[0,1:]]]),('nan_field',[[float('nan'),*sample[0,1:]]]),('positive_inf',[[float('inf'),*sample[0,1:]]]),('negative_inf',[[float('-inf'),*sample[0,1:]]]),('nonrepresentable_integer',[[2**53+1,*sample[0,1:]]])]:
    case('reject_'+name,lambda payload=payload:rejected(payload))
for column in range(7):
    altered=sample.copy();altered[0,column]=np.nextafter(altered[0,column],np.inf)
    case('reject_one_ulp_column_%d'%column,lambda altered=altered:not saved_rays_equal(sample,altered.tolist()))
for name,payload in [('deleted_ray',sample[:1].tolist()),('added_ray',np.vstack((sample,sample[:1])).tolist()),('reordered_rays',sample[::-1].tolist()),('nonempty_erased',[])]:
    case('reject_'+name,lambda payload=payload:not saved_rays_equal(sample,payload))
for name,array in [('flat_reconstructed',np.array([])),('invalid_reconstructed_columns',np.empty((0,6))),('nan_reconstructed',np.full((1,7),np.nan)),('string_reconstructed',np.full((1,7),'1'))]:
    def check(array=array):
        try:saved_rays_equal(array,[])
        except RayPacketSchemaError:return True
        return False
    case('reject_'+name,check)

details=[];packet_count=nonempty_count=empty_count=0;numeric_mutations=0;row_removals=0;empty_to_hit_rejections=0;range_inside=range_outside=0;fingerprints={}
records=read(repo/'runs/v698_rpccr_dynamic_confirmation/confirmation01/RESULTS.json')
for record in records:
    pair=repo/record['run'];cell=pair/'geometry_memory';packetfile=cell/'sensor_packets.jsonl.gz';fingerprints[str(packetfile.relative_to(repo))]=sha(packetfile)
    with gzip.open(packetfile,'rt') as stream:packets=[json.loads(s) for s in stream]
    states=[json.loads(s) for s in (cell/'motion_estimate.jsonl').read_text().splitlines()];config=read(pair/'DYNAMIC_PROTOCOL.json');empty_steps=[];bad=[];negative_counts=0;empty_state_checks=[]
    for index,p in enumerate(packets):
        rr=rays(p);packet_count+=1
        if not saved_rays_equal(rr,p['rays']):bad.append(p['step'])
        if len(rr):
            nonempty_count+=1
            for column in range(7):
                mutation=copy.deepcopy(p['rays']);mutation[0][column]=float(np.nextafter(mutation[0][column],np.inf))
                assert not saved_rays_equal(rr,mutation),'ALTERED_REAL_PACKET_ACCEPTED'
                numeric_mutations+=1;negative_counts+=1
            assert not saved_rays_equal(rr,p['rays'][1:]),'DELETED_RAY_ACCEPTED';row_removals+=1
        else:
            empty_count+=1;empty_steps.append(p['step']);state=states[index];previous=states[index-1] if index else None
            check={'retains_tracked_actor':state['center'] is not None and state['information_mode']=='TRACKED',
                   'does_not_invent_observation':not state['observed_this_frame'] and state['certified_unknown_rays']==0,
                   'no_empty_ray_free_space_contraction':state['empty_sample_contract']['empty_points']==state['empty_sample_contract']['removed_cells']==0,
                   'age_increments_with_time':previous is not None and abs(state['age_s']-(previous['age_s']+p['time']-previous['time']))<=1e-10}
            empty_state_checks.append({'step':p['step'],'checks':check,'passed':all(check.values())});assert all(check.values()),'EMPTY_OBSERVATION_STATE_SEMANTICS_FAILED'
            mutated=copy.deepcopy(p);mutated['lidar'][0]=.5;assert not saved_rays_equal(rays(mutated),p['rays']),'CHANGED_RAW_SENSOR_ACCEPTED';empty_to_hit_rejections+=1
            # Truth is evaluated offline only to show that no-hit != obstacle absent.
            actor=np.asarray(config['anchor_xy'])+np.sin(config['omega_rad_s']*p['time']+config['phase_rad'])*config['amplitude_m']*np.asarray(config['axis_xy'])
            if np.linalg.norm(actor-np.asarray(p['xy']))-config['radius_m']<=3.:range_inside+=1
            else:range_outside+=1
    details.append({'slot':record['task']['slot'],'packets':len(packets),'empty_steps':empty_steps,'exact_reconstruction_failed_steps':bad,'numeric_mutations_rejected':negative_counts,'empty_state_checks':empty_state_checks,'passed':not bad and all(x['passed'] for x in empty_state_checks)})
initial_records=read(repo/'runs/v698_rpccr_dynamic_confirmation/confirmation01/PREFLIGHTS.json')
for record in initial_records:
    p=repo/record['run']/'INITIAL_UNSEEN.json';fingerprints[str(p.relative_to(repo))]=sha(p);packet=read(p)['packet'];assert saved_rays_equal(rays(packet),packet['rays'])
checks={'all_unit_positive_and_negative_cases':all(x['passed'] for x in unit),'all9934_existing_packets_exact':packet_count==9934 and all(x['passed'] for x in details),'all24_original_preflights_exact':len(initial_records)==24,'all136_real_empty_frames_valid':empty_count==136 and empty_to_hit_rejections==136,'real_nonempty_numeric_changes_rejected':numeric_mutations==7*nonempty_count,'deleted_actual_ray_rejected':row_removals==nonempty_count,'all_input_hashes_unchanged':all(sha(repo/n)==h for n,h in fingerprints.items())}
result={'status':'STRICT_EMPTY_PACKET_CONTRACT_VERIFIED' if all(checks.values()) else 'FAIL','checks':checks,'unit_cases':unit,'packets_checked':packet_count,'preflight_packets_checked':len(initial_records),'nonempty_packets':nonempty_count,'empty_packets':empty_count,'real_one_ulp_changes_rejected':numeric_mutations,'real_ray_deletions_rejected':row_removals,'changed_empty_raw_packets_rejected':empty_to_hit_rejections,'empty_frames_actor_still_partly_within_range':range_inside,'empty_frames_actor_outside_range':range_outside,'truth_scope':'Offline range-presence diagnosis only; no actor truth is inserted into navigation or audit-state reconstruction.','details':details,'input_fingerprints':fingerprints,'new_simulation_integrations':0,'original_confirmation_status_unchanged':'NOT_PASSED'}
(root/'CONTRACT_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['details','unit_cases','input_fingerprints']},indent=2));assert all(checks.values())
