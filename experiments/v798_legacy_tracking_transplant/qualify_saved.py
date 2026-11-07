"""Saved target provenance and synthetic interface tests; zero model/steps."""
import copy,json,sys,ast
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v793_complete_joint_navigation'))
sys.path.insert(0,str(own))
from legacy_method import environment,guidance,OriginalNominal,Proposer,schedule
from actuator_commands import CommandMap
from retained_schedule import prepare,current,fingerprint
root=repo/'runs/v798_preparation';assert not(root/'QUALIFICATION.json').exists();root.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
pair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired/geometry_memory'
row=next(json.loads(l)for l in(pair/'v648_execution.jsonl').open()if json.loads(l)['step']==199)
old=next(json.loads(l)for l in(pair/'control_decisions.jsonl').open()if json.loads(l)['step']==200 and json.loads(l).get('stage')=='NOMINAL')
real=SimpleNamespace(qpos=np.asarray(row['qpos_full']),qvel=np.asarray(row['qvel_full']),ctrl=np.asarray(row['ctrl']),time=row['time'])
q=real.qpos;yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));pose=np.r_[q[:2],yaw]
path=np.asarray(read(own/'REFERENCE_PATH.json')['path']);index,steer,speed=guidance(path,pose,11)
command=CommandMap.__new__(CommandMap);c=read(own/'ACTUATOR_CONTRACT.json')
command.ids=c['ids'];command.lower=np.asarray(c['lower']);command.upper=np.asarray(c['upper']);command.rate=np.asarray(c['rate_per_public'])
predictions=[]
def fake_prediction(target):
    z=dict(qpos=np.tile(real.qpos,(328,1)),qvel=np.zeros((328,len(real.qvel))),poses=np.tile(pose,(328,1)),
        controls=schedule(target,real.ctrl[command.ids],command),self_bounds=np.tile([-.43,-.36,.43,.36],(329,1)))
    predictions.append(z);return z
model=SimpleNamespace(opt=SimpleNamespace(timestep=.01));env=environment(real,model)
legacy=OriginalNominal(command,Proposer(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'),fake_prediction)
field=SimpleNamespace(trajectory_values=lambda p,dt:np.full(len(p),.5))
legacy.select(env,field,path,index,pose,steer,speed,real.ctrl[command.ids])
gold=[x for x in old['candidates']if x['proposal_role']!='DIFFERENTIAL'];assert len(gold)==len(legacy.last_diagnostics)==19
error=0.
for a,b in zip(gold,legacy.last_diagnostics):
    for key in ['features','target_command','first_command']:
        error=max(error,float(np.max(abs(np.asarray(a[key])-b[key]))))
        assert np.allclose(a[key],b[key],rtol=0,atol=1e-12),(key,a[key],b[key])
    assert a['proposal_role']==b['proposal_role']
detail=dict(label='SYNTHETIC_INTERFACE_ONLY',admissible=True,clearance_m=.2,self_margin_m=.01,arc_progress_m=0.)
state=dict(hidden_world_geometry_used=False,time=real.time)
target=np.asarray(gold[0]['target_command']);z=predictions[0]
cert=prepare(real,z,target,detail,state,command,200);h=fingerprint(cert);current(cert,0,real,command)
negative=[]
for key in ['qpos','qvel','ctrl','time','schedule','clearance','self','terminal_linear','terminal_angular','truth','stale_time']:
    rr=copy.deepcopy(real);zz=copy.deepcopy(z);dd=copy.deepcopy(detail);ss=copy.deepcopy(state)
    if key in ['qpos','qvel','ctrl']:getattr(rr,key)[0]+=.1
    elif key=='time':rr.time+=.1
    elif key=='schedule':zz['controls'][0,0]+=.1
    elif key=='clearance':dd['clearance_m']=.1
    elif key=='self':dd['self_margin_m']=.001
    elif key=='terminal_linear':zz['qvel'][-1,0]=.1
    elif key=='terminal_angular':zz['qvel'][-1,3]=.1
    elif key=='truth':ss['hidden_world_geometry_used']=True
    else:ss['time']+=.1
    try:
        if key in ['qpos','qvel','ctrl','time']:current(cert,0,rr,command)
        else:prepare(rr,zz,target,dd,ss,command,200)
    except AssertionError:negative.append(key)
    else:raise AssertionError(('NEGATIVE_ACCEPTED',key))
    assert fingerprint(cert)==h
result=dict(status='LEGACY_PROPOSER_SAVED_INTERFACE_QUALIFIED',old_original_targets=19,
    maximum_feature_target_first_command_error=error,old_index=index,nominal_steer=steer,nominal_speed=speed,
    negative_cases=negative,synthetic_array_interface_only=True,no_physical_prediction_claimed=True,
    full_legacy_pipeline_identical=False,model_initializations=0,integrations=0)
(root/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
