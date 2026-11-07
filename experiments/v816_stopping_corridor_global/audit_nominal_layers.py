"""Saved-only nominal spatial proposal / actual complete causal tail audit."""
import argparse,json,os,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(own))
from exact_footprint import pose_values
from serial_predictor import project_to_segment_path
from motion_tracker import install_time_gate
from self_geometry import containment_margin
from actuator_commands import CommandMap
ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);a=ap.parse_args();cell=a.pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(l)for l in p.open()]if p.exists()else[]
protocol=read(a.pair/'STATIC_PROTOCOL.json');states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')}
bounds=np.asarray(protocol['footprint_bounds']);base=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');command=CommandMap.__new__(CommandMap);command.ids=contract['ids'];command.lower=np.asarray(contract['limits'])[:,0];command.upper=np.asarray(contract['limits'])[:,1];command.rate=np.asarray(contract['rate'])
count=spatial_only=certs=0;maximum=0.;records=[]
for call in [x for x in lines(cell/'control_decisions.jsonl')if x['stage']=='NOMINAL']:
    state=states[call['step']];field=SimpleNamespace(**base);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    for c in call['candidates']:
        z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast']);poses=z['poses']
        static=float(pose_values(SimpleNamespace(**base),poses).min());causal=field.trajectory_values(poses,.01)
        margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['terminal_qvel'][:2]))
        reason='SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TIME_CLEARANCE'if static<.155 else None
        assert reason==c['reason']and c['nominal_causal_forecast_not_executed']is True
        assert max(abs(static-c['nominal_spatial_minimum_clearance_m']),abs(margin-c['self_domain_margin_m']),abs(speed-c['terminal_speed_m_s']))<=1e-8
        assert np.array_equal(z['target'],c['target_command'])and np.array_equal(command.sequence(z['target'],z['last_command'],240,80),z['controls'])
        if margin>=.002:
            maximum=max(maximum,abs(float(causal.min())-c['minimum_clearance_m']));assert maximum<=1e-8
        if reason is None:
            arc0,_,_=project_to_segment_path(z['initial_pose'][None],z['reference']);arc,contour,heading=project_to_segment_path(poses[-1:],z['reference'])
            err=abs((poses[-1,2]-heading[0]+np.pi)%(2*np.pi)-np.pi)
            value=8.*float(arc[0]-arc0[0])-5*float(contour[0])-5.*float(err)+.15*min(float(causal.min()),.30)-.0005*float(np.linalg.norm(z['controls'][0]-z['last_command']))
            if c['proposal_role']=='LEARNED':value+=.025
            assert abs(value-c['score'])<=1e-8
            spatial_only+=float(causal.min())<.155
        count+=1
for file in sorted((cell/'ordinary_certificates').glob('*.npz')):
    step=int(file.stem.split('_')[-1]);z=np.load(file);state=states[step]
    field=SimpleNamespace(**base);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    full=np.vstack([z['prefix_poses'],z['poses']]);minimum=float(field.trajectory_values(full,.01).min())
    assert len(full)==328 and minimum>=.155 and abs(minimum-float(z['minimum_causal_clearance']))<=1e-8
    assert np.array_equal(command.sequence(z['target'],z['prefix_command'],320,int(z['brake_after'])),z['controls'])
    assert float(z['self_margin'])>=.002 and np.linalg.norm(z['qvel'][-1,:2])<=.025
    assert abs(float(z['created_time'])-state['time'])<=1e-8
    records.append(dict(step=step,minimum_causal_clearance_m=minimum,complete_native=328));certs+=1
ordinary=[x for x in lines(cell/'model_admission.jsonl')if x['status']=='MODEL_SAFE_COMMAND'and not x.get('certified_backup_handover')and not x.get('observation_initialization')]
assert certs==len(ordinary)and count>0
result=dict(status='SPATIAL_NOMINAL_AND_COMPLETE_CAUSAL_TAIL_VERIFIED',nominal_candidates=count,
    spatial_only_admissible_future_rejected_nominal=spatial_only,ordinary_complete_causal_certificates=certs,
    maximum_geometry_error=maximum,records=records,new_models=0,new_integrations=0,
    scope='Nominal future is proposal-only. Every executed short prefix retains full original causal tail.')
(a.pair/'NOMINAL_LAYER_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='records'}))
