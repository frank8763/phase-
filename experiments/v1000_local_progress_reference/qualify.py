"""Independent path/response/causal geometry checks; no physical qualification."""
import copy,hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
from reference import construct,ref
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v1000_local_progress_reference'
sys.path.insert(0,str(R/'experiments/v997_input_consistent_recovery'))
from saved_qualification import reconstruct,independently_check_geometry
def read(p):return json.loads(p.read_text())
def audit(plan,packet,source,known):
    assert plan['passed']and plan['status']=='CAUSAL_FINITE_PROGRESS_REFERENCE'
    assert plan['original_goal']==[4.,-2.]and source['source_native_tick']<=packet['native_tick'],'FUTURE_SOURCE_OR_GOAL_CHANGED'
    initial=ref.snapshot_state(packet,source,packet['body_measured_at'])
    assert np.max(abs(np.array(plan['initial_state'])-initial))<=1e-12,'INITIAL_STATE_CHANGED'
    dense=reconstruct(plan['initial_state'],plan['edge_targets']);coarse=dense[::25];states=np.array(plan['state_path']);path=np.array(plan['path'])
    assert states.shape==coarse.shape and abs(states-coarse).max()<=1e-5,'REFERENCE_NOT_RECONSTRUCTIBLE'
    assert path.shape==states[:,:3].shape and abs(path-states[:,:3]).max()<=1e-12,'PATH_STATE_MISMATCH'
    assert len(plan['edge_targets'])<=12 and len(plan['edge_targets'])>0 and abs(dense[:,3]).max()<=ref.MAX_DELTA+1e-10
    raw=independently_check_geometry(dense,known,source['periodic']);rho=math.hypot(.44,.375);grad=ref.GAIN*ref.K+abs(ref.RATE_COUPLING)*ref.VIRTUAL_RATE/ref.REFERENCE_SPEED
    lower=raw-ref._old.SPATIAL-.00025*(1+rho*grad)
    assert lower>=.155,'INDEPENDENT_GEOMETRY_REJECTED'
    nominal=float(np.linalg.norm(dense[0,:2]-[4.,-2.])-np.linalg.norm(dense[-1,:2]-[4.,-2.]));progress=nominal-.08
    assert progress>=.4 and abs(progress-plan['actual_goal_progress_lower_m'])<1e-5,'INSUFFICIENT_PROGRESS'
    return dict(passed=True,independent_full_cycle_lower_m=lower,actual_progress_lower_m=progress,reconstruction_error=float(abs(states-coarse).max()),
        models=0,integrations=0,physical_tracking_qualified=False)
if __name__=='__main__':
    end=read(O/'ROUND_WINDOW.json')['source_only_deadline_unix'];saved=read(R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json');known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');rows=[]
    for i in [0,1]:
        sample=saved['rows'][i];p=sample['search_packet'];s=sample['search_source'];plan=construct(p,s,[4.,-2.],known,p['body_measured_at'],min(end,time.time()+60))
        proof=audit(plan,p,s,known)if plan['passed']else None
        rows.append(dict(index=i,plan=plan,audit=proof));print(json.dumps(dict(index=i,found=plan['passed'],status=plan['status'],expanded=plan['expanded'],proof=proof)),flush=True)
        (O/'RESULTS.json').write_text(json.dumps(rows,indent=2)+'\n')
    negative=[]
    for row in rows:
        if not row['plan']['passed']:continue
        i=row['index'];p=saved['rows'][i]['search_packet'];s=saved['rows'][i]['search_source']
        for name in ['path','future_source','progress','geometry']:
            plan=copy.deepcopy(row['plan']);source=copy.deepcopy(s);k=copy.deepcopy(known)
            if name=='path':plan['path'][3][2]+=.01
            elif name=='future_source':source['source_native_tick']=p['native_tick']+1
            elif name=='progress':plan['actual_goal_progress_lower_m']=0.
            else:k['known_circles'].append([*p['body'][:2],.5])
            try:audit(plan,p,source,k)
            except AssertionError as e:negative.append(dict(state=i,kind=name,rejected=True,error=str(e)))
            else:raise AssertionError('NEGATIVE_NOT_REJECTED_'+name)
    result=dict(source_qualification_passed=all(x['audit']and x['audit']['passed']for x in rows),models=0,integrations=0,new_navigation_trials=0,
        physical_authority=False,causal_controller_predictor_ready=False,rows=rows,negative_cases=negative,old_V997_failure_preserved=True)
    (O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(source_qualification_passed=result['source_qualification_passed'],negative_cases=len(negative),models=0)))
