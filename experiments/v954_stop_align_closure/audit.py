"""Independent closed component arrays, encoders, phase table and source audit."""
import gzip
import hashlib
import importlib.abc
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v954_stop_align_closure';OUT.mkdir(exist_ok=True)
OPS=ROOT/'runs/v953_stop_align_components'
closed=json.loads((OPS/'COMPLETION.json').read_text());assert closed['closed']
tasks=json.loads((ROOT/'experiments/v953_stop_align_components/TASKS.json').read_text())
spec=importlib.util.spec_from_file_location('closed_v952_adapter',ROOT/'experiments/v952_stopped_steering_alignment/vehicle_control.py')
controller=importlib.util.module_from_spec(spec);spec.loader.exec_module(controller)
rows=[];unexecuted=[]
for index,task in enumerate(tasks):
    case=ROOT/task['output'];physical=case/'physics'
    if not(physical/'NATIVE_TRACE.npz').exists():unexecuted.append(index);continue
    with np.load(physical/'NATIVE_TRACE.npz')as file:trace={k:file[k].copy()for k in file.files}
    with np.load(case/'BODY_AND_STEERING.npz')as file:
        body=file['body'];steering=file['steering'];origin=file['origin'];expected=file['expected'];phases=file['phases']
    setup=json.loads((physical/'SETUP.json').read_text());commands=json.loads((physical/'BODY_COMMANDS.json').read_text())
    replay=json.loads((physical/'REPLAY.json').read_text());contacts=json.loads(gzip.decompress((physical/'CONTACTS.json.gz').read_bytes()))
    q=trace['qpos'];vel=trace['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    derived=np.c_[q[:,:2],yaw,vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw),vel[:,5]]
    actual=body[200:]if index<18 else body[400:1600]
    position=float(np.linalg.norm(actual[:,:2]-expected[:,:2],axis=1).max())
    angle=float(abs(np.arctan2(np.sin(actual[:,2]-expected[:,2]),np.cos(actual[:,2]-expected[:,2]))).max())
    limit=(.04 if task['command'][0]*origin[3]<0 else .02)if index<18 else .04
    ids=setup['actuator_ids'];ctrl=trace['ctrl'][:,ids];bounds=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])
    ticks=420 if index<18 else 1800
    enc=np.c_[q[:,setup['steering_qpos_addresses']],vel[:,setup['steering_qvel_addresses']]]
    # Reconstruct controller outputs without initializing/integrating a model.
    adapter=controller.Adapter.__new__(controller.Adapter)
    adapter.dt=.01;adapter.last=np.zeros(4);adapter.integral=0.;adapter.wheelbase=.60;adapter.track=.54;adapter.radius=.12;adapter.center_limit=.42722137342572125
    adapter.max_curvature=np.tan(adapter.center_limit)/adapter.wheelbase
    adapter.commands=SimpleNamespace(lower=bounds[:,0],upper=bounds[:,1],rate=rates*.08,
        legal=lambda value:bool(np.all(value>=bounds[:,0])and np.all(value<=bounds[:,1])))
    adapter.mode='DRIVING';adapter.stable_ticks=0
    encoder_index=[-1]
    def encoders():
        i=encoder_index[0]
        return (setup['initial_steering_position'],setup['initial_steering_velocity'])if i<0 else(steering[i,:2],steering[i,2:])
    adapter.encoders=encoders;maximum=0.;phase='DRIVING';stable=0;phase_good=True;held_while_moving=True
    for i,(_,v,w,mv,mw,stale)in enumerate(commands):
        encoder_index[0]=i-1
        maximum=max(maximum,float(abs(adapter.compute(v,w,mv,mw,stale)-ctrl[i]).max()))
        stopping=stale or abs(v)<.005
        if not stopping:phase='DRIVING';stable=0
        else:
            stopped=abs(mv)<=.005 and abs(mw)<=.005
            stable=min(10,stable+1)if stopped else 0
            if not stopped:phase='BRAKING'
            elif stable>=10:phase='ALIGNING'
            elif phase!='ALIGNING':phase='BRAKING'
            if not stopped:
                previous=np.zeros(2)if i==0 else ctrl[i-1,:2]
                held_while_moving=held_while_moving and np.array_equal(ctrl[i,:2],previous)
        phase_good=phase_good and phases[i]==phase
    checks=dict(complete_native=len(q)==len(body)==len(commands)==ticks,
        body_from_native=float(abs(body-derived).max())<=1e-8,
        encoders_from_native=float(abs(steering-enc).max())<=1e-8,
        actual_clearance=float(trace['clearance'].min())>=.15,self_containment=float(trace['self_margin'].min())>=-1e-10,
        bad_contacts0=not any(c[2]in{'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for c in row),
        complete_own_replay=replay['passed']and replay['replay_native']==ticks,
        ctrl_bounds=bool(np.all(ctrl>=bounds[:,0])and np.all(ctrl<=bounds[:,1])),
        ctrl_rates=bool(np.all(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates*.01+1e-10)),
        exact_controller_reconstruction=maximum<=1e-8,
        phase_table=phase_good,no_steering_centering_while_moving=held_while_moving,
        position=position<=limit,heading=angle<=.035,
        speed=float(abs(body[:,3]).max())<=.13,yaw_rate=float(abs(body[:,4]).max())<=.16,
        half_second_settle=bool(abs(body[(269 if index<18 else 1649):,3:5]).max()<=.03),
        final_measured_alignment=bool(abs(steering[-1,:2]).max()<=.01 and abs(steering[-1,2:]).max()<=.03))
    gain=None
    if index==18:
        at=body[399];gain=float((body[1599,:2]-at[:2])@[np.cos(at[2]),np.sin(at[2])])
        checks['measured_stop_alignment_before_forward']=max(abs(at[3:]))<=.03 and abs(steering[399,:2]).max()<=.01 and abs(steering[399,2:]).max()<=.03
        checks['actual_progress_at_least1m']=gain>=1.
        checks['no_reverse_request']=all(row[1]>=0 for row in commands)
    rows.append(dict(index=index,passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},actual_native=ticks,
        replay_native=replay['replay_native'],private_native=0,position_max_m=position,heading_max_rad=angle,
        native_min_clearance_m=float(trace['clearance'].min()),controller_max_error=maximum,
        forward_progress_m=gain,aligning_ticks=int(np.sum(phases=='ALIGNING'))))
sources=json.loads((ROOT/'experiments/v953_stop_align_components/SOURCE_FREEZE.json').read_text())['files']
unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sources.items())
result=dict(passed=closed['passed']and len(rows)==19 and all(r['passed']for r in rows)and unchanged,
    rows=rows,unexecuted_cases=unexecuted,all_sources_unchanged=unchanged,
    actual_native=sum(r['actual_native']for r in rows),replay_native=sum(r['replay_native']for r in rows),
    private_native=0,navigation=0,new24=0,new_models_during_audit=0,new_integrations_during_audit=0,
    scope='Complete recorded native body/encoder/ctrl/phase and source validation plus own-control replay receipts. Component qualification only, not full navigation.')
result['evidence_integrity_verified']=bool(unchanged and len(rows)==closed['attempted_cases'] and
    all(all(value for key,value in row['checks'].items() if key!='final_measured_alignment') for row in rows) and
    result['actual_native']==closed['actual_native'] and result['replay_native']==closed['replay_native'])
original=OUT/'FIRST_AUDIT_EXPECTED_NOT_PASSED.json'
if not original.exists() and (OUT/'FINAL_INDEPENDENT_AUDIT.json').exists():
    original.write_bytes((OUT/'FINAL_INDEPENDENT_AUDIT.json').read_bytes())
(OUT/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
assert result['evidence_integrity_verified'],'RECORDED_FAILURE_EVIDENCE_NOT_VERIFIED'
