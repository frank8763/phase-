"""Preregistered8search comparisons and independent geometry, zero physics."""
import hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
from search import ref,search,prefix
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v999_search_resolution_diagnosis'
sys.path.insert(0,str(R/'experiments/v997_input_consistent_recovery'))
from saved_qualification import reconstruct,independently_check_geometry
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
if __name__=='__main__':
    end=read(O/'ROUND_WINDOW.json')['source_only_deadline_unix'];assert time.time()<end
    saved=read(R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json');old=read(R/'records/nav2_v977_20261110/ZERO_MODEL_QUALIFICATION.json')
    known=read(R/'records/nav2_v991_20261110/V992_RESPONSE_DIAGNOSIS.json').get('known')
    if known is None:
        setup=read(R/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1/KNOWN_FIELD.json')if(R/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1/KNOWN_FIELD.json').exists()else None
        if setup is not None:known=setup
    if known is None:known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')
    row=saved['rows'][1];packet=row['search_packet'];source=row['search_source'];initial=ref.snapshot_state(packet,source,packet['body_measured_at'])
    baseline=ref.search_static(initial,np.array([4.,-2.]),known)
    dump(O/'EXACT_BASELINE_REPRODUCTION.json',dict(models=0,integrations=0,original=baseline))
    assert not baseline['passed']and baseline['expanded']==1697 and baseline['generated']==2009,'BASELINE_FAILURE_NOT_REPRODUCED'
    matrix=read(C/'RESOLUTION_MATRIX.json');rows=[]
    for index in matrix['states']:
        sample=saved['rows'][index];packet=sample['search_packet'];source=sample['search_source'];initial=ref.snapshot_state(packet,source,packet['body_measured_at'])
        for variant in matrix['variants']:
            assert time.time()<end-65
            route=search(initial,np.array([4.,-2.]),known,variant,min(end,time.time()+60))
            if index==1 and variant['name']=='original':assert route['expanded']==baseline['expanded']and route['generated']==baseline['generated']
            plan=prefix(route,initial,[4.,-2.],known,source);independent=None
            if plan['passed']:
                dense=reconstruct(plan['initial_state'],plan['edge_targets']);error=float(abs(dense[::25]-np.array(plan['state_path'])).max())
                raw=independently_check_geometry(dense,known,source['periodic']);rho=math.hypot(.44,.375);gradient=ref.GAIN*ref.K+abs(ref.RATE_COUPLING)*ref.VIRTUAL_RATE/ref.REFERENCE_SPEED
                lower=raw-ref._old.SPATIAL-.00025*(1+rho*gradient)
                independent=dict(passed=error<=1e-5 and lower>=.155 and plan['actual_goal_progress_lower_m']>=.4,reconstruction_error=error,full_cycle_lower_m=lower,
                    actual_progress_lower_m=plan['actual_goal_progress_lower_m'],physical_tracking_qualified=False)
            item=dict(state=index,source_native_tick=source['source_native_tick'],body_native_tick=packet['native_tick'],route=route,prefix=plan,independent_geometry=independent)
            rows.append(item);dump(O/'RESULTS.json',rows)
            print(json.dumps(dict(state=index,variant=variant['name'],route_found=route['passed'],status=route['status'],expanded=route['expanded'],prefix_passed=plan['passed'],independent=independent)),flush=True)
    result=dict(completed=True,models=0,integrations=0,private_predictions=0,physics_replay=0,baseline_failure_reproduced=True,rows=rows,physical_authority=False,
        any_second_state_prefix_passed=any(x['state']==1 and x['independent_geometry']and x['independent_geometry']['passed']for x in rows))
    dump(O/'COMPLETION.json',result)
