"""Independent saved-state/control audit, including a proven pre-integration fault."""
import ast
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
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel());ROOT=Path(__file__).resolve().parents[2]
OPS=ROOT/'runs/v959_hold_response18';OUT=ROOT/'runs/v960_hold_response_closure';OUT.mkdir(exist_ok=True)
done=json.loads((OPS/'COMPLETION.json').read_text());assert done['closed']
tasks=json.loads((ROOT/'experiments/v959_hold_response18/TASKS.json').read_text())
path=ROOT/'experiments/v958_hold_steering_contract/vehicle_control.py'
spec=importlib.util.spec_from_file_location('closed_v958',path);control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
sources=json.loads((ROOT/'experiments/v959_hold_response18/SOURCE_FREEZE.json').read_text())['files']
unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sources.items())
vehicle_path=ROOT/'experiments/v858_nav2_verified/vehicle.py'
tree=ast.parse(vehicle_path.read_text());method=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='step')
compute_index=next(i for i,n in enumerate(method.body)if any(isinstance(c,ast.Call)and isinstance(c.func,ast.Attribute)and c.func.attr=='compute'for c in ast.walk(n)))
native_index=next(i for i,n in enumerate(method.body)if any(isinstance(c,ast.Call)and isinstance(c.func,ast.Attribute)and c.func.attr=='native'for c in ast.walk(n)))
assert compute_index<native_index
rows=[];evidence=[]
for result in done['rows']:
    index=result['index'];case=ROOT/tasks[index]['output'];raw=case/'physics'
    with np.load(raw/'NATIVE_TRACE.npz')as f:trace={k:f[k].copy()for k in f.files}
    setup=json.loads((raw/'SETUP.json').read_text());commands=json.loads((raw/'BODY_COMMANDS.json').read_text())
    contacts=json.loads(gzip.decompress((raw/'CONTACTS.json.gz').read_bytes()))
    q=trace['qpos'];vel=trace['qvel'];count=len(q)
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    body=np.c_[q[:,:2],yaw,vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw),vel[:,5]]
    enc=np.c_[q[:,setup['steering_qpos_addresses']],vel[:,setup['steering_qvel_addresses']]]
    ctrl=trace['ctrl'][:,setup['actuator_ids']];bounds=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])
    a=control.Adapter.__new__(control.Adapter);a.dt=.01;a.last=np.zeros(4);a.integral=0.;a.wheelbase=.6;a.track=.54;a.radius=.12
    a.center_limit=.42722137342572125;a.max_curvature=np.tan(a.center_limit)/a.wheelbase
    a.commands=SimpleNamespace(lower=bounds[:,0],upper=bounds[:,1],rate=rates*.08,legal=lambda u:bool(np.all(u>=bounds[:,0])and np.all(u<=bounds[:,1])))
    a.mode='DRIVING';a.stable_ticks=0;at=[-1]
    a.encoders=lambda:(setup['initial_steering_position'],setup['initial_steering_velocity'])if at[0]<0 else(enc[at[0],:2],enc[at[0],2:])
    maximum=0.;phases=[]
    for tick,(_,v,w,mv,mw,stale)in enumerate(commands):
        at[0]=tick-1;maximum=max(maximum,float(abs(a.compute(v,w,mv,mw,stale)-ctrl[tick]).max()));phases.append(a.mode)
    complete=(case/'BODY_AND_STEERING.npz').exists();array_match=True;function_checks={}
    if complete:
        with np.load(case/'BODY_AND_STEERING.npz')as f:
            array_match=float(abs(f['body']-body).max())<=1e-8 and float(abs(f['steering']-enc).max())<=1e-8 and np.array_equal(f['phases'],phases)
        origin=body[199];v,w=tasks[index]['command'];t=np.minimum(np.arange(1,221)*.01,.2)
        angle=origin[2]+w*t
        if abs(w)<1e-10:
            x=origin[0]+v*t*np.cos(origin[2]);y=origin[1]+v*t*np.sin(origin[2])
        else:
            x=origin[0]+v/w*(np.sin(angle)-np.sin(origin[2]));y=origin[1]-v/w*(np.cos(angle)-np.cos(origin[2]))
        expected=np.c_[x,y,angle];observed=body[200:]
        position=float(np.linalg.norm(observed[:,:2]-expected[:,:2],axis=1).max())
        heading=float(abs(np.arctan2(np.sin(observed[:,2]-angle),np.cos(observed[:,2]-angle))).max())
        bound=.04 if v*origin[3]<0 else .02
        function_checks=dict(position=position<=bound,heading=heading<=.035,speed=float(abs(body[:,3]).max())<=.13,
            yaw_rate=float(abs(body[:,4]).max())<=.16,half_second_settle=float(abs(body[269:,3:5]).max())<=.03)
        function_checks['reported_metrics_match_independent']=abs(position-result['position_residual_max_m'])<=1e-8 and abs(heading-result['angle_residual_max_rad'])<=1e-8
        # Every actual zero/stale command holds the existing steering target.
        function_checks['zero_commands_hold_steering']=all(np.array_equal(ctrl[i,:2],ctrl[i-1,:2])for i,row in enumerate(commands)if i>0 and(row[5]or abs(row[1])<.005))
    error=None;fault_before_integration=False
    if not complete:
        at[0]=count-1
        try:a.compute(0.,0.,*body[-1,3:5])
        except ValueError as exception:error=str(exception)
        fault_before_integration=error=='ALIGNMENT_BODY_ENVELOPE_EXCEEDED'and compute_index<native_index
    bad=sum(c[2]in{'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for c in row)
    native=result.get('native',result.get('partial',{}))
    replay=json.loads((raw/'REPLAY.json').read_text())if(raw/'REPLAY.json').exists()else None
    replay_good=replay is not None and replay['passed']and replay['replay_native']==count and replay['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and replay['contact_mismatched_ticks']==0
    checks=dict(native_and_command_rows=count==len(commands)==native['actual_native']==native['fully_recorded_native']==native['root_guard_native_count'],
        controller_reconstruction=maximum<=1e-8,body_encoder_phase_arrays=array_match,
        native_clearance=float(trace['clearance'].min())>=.15,self_containment=float(trace['self_margin'].min())>=-1e-10,
        bad_contacts0=bad==0,ctrl_bounds=bool(np.all(ctrl>=bounds[:,0])and np.all(ctrl<=bounds[:,1])),
        ctrl_slew=bool(np.all(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates*.01+1e-10)),
        completed_own_replay_or_proven_fault=replay_good if complete else fault_before_integration)
    evidence.append(all(checks.values()))
    rows.append(dict(index=index,component_passed=result['passed'],independent_function_checks={k:bool(v)for k,v in function_checks.items()},
        position_max_m=position if complete else None,heading_max_rad=heading if complete else None,position_bound_m=bound if complete else None,
        complete_response=count==420 and complete,
        evidence_checks={k:bool(v)for k,v in checks.items()},recorded_actual_native=count,
        exact_actual_native=count if complete or fault_before_integration else None,
        original_declared_actual_native=result['actual_native'],own_replay_native=0 if replay is None else replay['replay_native'],
        own_replay_verified=replay_good,unreplayed_native=0 if replay_good else count,
        ctrl_reconstruction_error=maximum,minimum_actual_clearance_m=float(trace['clearance'].min()),
        final_body=body[-1].tolist(),final_steering=enc[-1].tolist(),phases={k:phases.count(k)for k in set(phases)},
        reproduced_next_fault=error,pre_integration_fault=fault_before_integration,
        body_after_half_second_max=float(abs(body[269:,3:5]).max())if count>269 else None))
result=dict(passed=done['passed']and len(rows)==18 and all(r['component_passed']and all(r['independent_function_checks'].values())for r in rows)and unchanged,
    evidence_integrity_verified=unchanged and all(evidence),all_frozen_sources_unchanged=unchanged,rows=rows,
    actual_native=sum(r['exact_actual_native']for r in rows)if all(r['exact_actual_native']is not None for r in rows)else None,
    original_campaign_actual_native=done['actual_native'],replay_native=sum(r['own_replay_native']for r in rows),
    unreplayed_native=sum(r['unreplayed_native']for r in rows),private_native=0,navigation=0,new24=0,
    attempted_cases=done['attempted_cases'],unexecuted_cases=done['unexecuted_cases'],models=done['models_initialized'],
    accounting_proof=dict(original_campaign_total=done['actual_native'],all_completed_counts_reconciled=all(r['complete_response']and r['own_replay_verified']for r in rows),compute_statement_index=compute_index,native_statement_index=native_index,
        vehicle_source_sha256=hashlib.sha256(vehicle_path.read_bytes()).hexdigest(),
        explanation='Each of18 completed responses has420 saved native states,420 command rows,420 root checks and420 verified own-control replay steps. No partial/unknown count is replaced.'),
    new_models_during_audit=0,new_integrations=0)
(OUT/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2));assert result['evidence_integrity_verified']
