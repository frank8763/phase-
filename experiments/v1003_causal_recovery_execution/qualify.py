"""No-model causal input-reference and copied predictor seam qualification."""
import copy,gzip,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1003_causal_recovery_execution'
sys.path.insert(0,str(C))
from plan import construct,predict,geometry,PARAMETERS
from predictor import Predictor,fixture,law
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')

def memory(origin,setup):
    old=law.base.Adapter;adapter=fixture.make(old,setup)
    commands=read(O/'prior_v974/physics/BODY_COMMANDS.json')
    with np.load(O/'prior_v974/physics/NATIVE_TRACE.npz')as z:ctrl=z['ctrl'][:origin,setup['actuator_ids']]
    error=0.
    for i,row in enumerate(commands[:origin]):error=max(error,float(abs(adapter.compute(*row[1:6])-ctrl[i]).max()))
    assert error<=1e-8,'ORIGINAL_MEMORY_NOT_RECONSTRUCTIBLE'
    return adapter.last.copy(),adapter.integral,error

def audit(plan,packet,source,known,setup):
    assert plan['passed']and plan['status']=='CAUSAL_PLANNED_INPUT_REFERENCE'
    assert source['source_native_tick']<=packet['native_tick']and plan['source_native_tick']==source['source_native_tick'],'FUTURE_OR_CHANGED_CAUSAL_SOURCE'
    assert plan['original_goal']==[4.,-2.]
    states,controls,requests=predict(setup,plan['initial'],plan['edge_targets'])
    assert np.array_equal(states,np.asarray(plan['state_path']))and np.array_equal(controls,np.asarray(plan['predicted_actuator_controls'])),'PREDICTION_STATE_OR_CONTROL_CHANGED'
    assert requests==plan['planned_body_requests']and np.array_equal(states[:,:3],np.array(plan['path'])),'PLANNED_INPUT_OR_PATH_CHANGED'
    assert np.max(abs(states[0,:3]-packet['body'][:3]))<=1e-12,'INITIAL_POSE_CHANGED'
    sys.path.insert(0,str(R/'experiments/v997_input_consistent_recovery'))
    from saved_qualification import independently_check_geometry
    dense=np.c_[states[:,:3],states[:,6]]
    raw=independently_check_geometry(dense,known,source['periodic'])
    rho=math.hypot(.44,.375);lower=raw-geometry.SPATIAL-.005*(.13+rho*.16)
    progress=float(np.linalg.norm(states[0,:2]-[4.,-2.])-np.linalg.norm(states[-1,:2]-[4.,-2.])-.08)
    assert lower>=.155 and raw>=plan['required_raw_clearance_m'],'INDEPENDENT_FULL_CYCLE_GEOMETRY'
    assert progress>=.4 and abs(progress-plan['actual_goal_progress_lower_m'])<1e-12,'PROGRESS_CHANGED'
    assert requests[-200:]==[[0.,0.,False]]*200 and abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03,'INCOMPLETE_STOP'
    return dict(passed=True,independent_raw_clearance_m=raw,independent_full_cycle_lower_m=lower,actual_goal_progress_lower_m=progress,models=0,integrations=0)

if __name__=='__main__':
    assert read(R/'runs/v1002_causal_response_predictor/CAUSAL_PREDICTION_QUALIFICATION.json')['passed']
    for row in read(O/'RESTORE_RECEIPT.json')['files']:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    setup=read(O/'prior_v974/physics/SETUP.json');saved=read(R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json');known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')
    # A fresh process with the strict NoModel finder proves exact V1002 copy equivalence.
    script=R/'experiments/v1002_causal_response_predictor';sys.path.insert(0,str(script))
    s=importlib.util.spec_from_file_location('v1003_original_fit_loader',script/'fit_and_qualify.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
    equivalence=[]
    for task in read(R/'experiments/v995_sim_time_response/TASKS.json'):
        row=old.load(task);f=Predictor(row['setup'],row['initial'],PARAMETERS);ref=old.Predictor(row['setup'],row['initial'],PARAMETERS);error=0.
        for request in row['requests']:
            a,u=f.step(*request);b,v=ref.step(*request);error=max(error,float(abs(a-b).max()),float(abs(u-v).max()))
        assert error==0.;equivalence.append(dict(name=task['name'],steps=f.steps,maximum_state_control_error=error))
    rows=[];negative=[]
    for index in [0,1]:
        packet=saved['rows'][index]['search_packet'];source=saved['rows'][index]['search_source'];origin=packet['native_tick']
        last,integral,error=memory(origin,setup);plan=construct(packet,source,[4.,-2.],known,setup,last,integral,time.time()+60)
        proof=audit(plan,packet,source,known,setup)if plan['passed']else None
        rows.append(dict(index=index,origin_native_tick=origin,plan=plan,audit=proof,memory_reconstruction_error=error))
        print(json.dumps(dict(index=index,passed=plan['passed'],checks=plan.get('checks'),audit=proof,steps=plan.get('analytical_prediction_steps'))),flush=True)
        dump(O/'RESULTS.json',rows)
        if not plan['passed']:break
        for kind in ['path','input','future_source','geometry','prediction_ctrl']:
            bad=copy.deepcopy(plan);ss=copy.deepcopy(source);kk=copy.deepcopy(known)
            if kind=='path':bad['path'][20][2]+=.01
            elif kind=='input':bad['planned_body_requests'][20][1]+=.01
            elif kind=='prediction_ctrl':bad['predicted_actuator_controls'][20][0]+=.01
            elif kind=='future_source':ss['source_native_tick']=origin+1
            else:kk['known_circles'].append([*packet['body'][:2],.5])
            try:audit(bad,packet,ss,kk,setup)
            except AssertionError as e:negative.append(dict(state=index,kind=kind,rejected=True,error=str(e)))
            else:raise AssertionError('NEGATIVE_NOT_REJECTED '+kind)
    result=dict(passed=len(rows)==2 and all(x['audit']and x['audit']['passed']for x in rows)and len(negative)==10,
        rows=rows,negative_cases=negative,predictor_equivalence=equivalence,models=0,mujoco_integrations=0,physical_replay=0,
        controller_software_ready=True,physical_ready=False,model_window_locked=False)
    dump(O/'QUALIFICATION.json',result);print(json.dumps(dict(passed=result['passed'],negative_cases=len(negative),models=0)))
