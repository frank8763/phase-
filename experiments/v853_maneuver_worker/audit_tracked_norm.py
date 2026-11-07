"""Independent declaration/coverage and complete saved contract geometry audit."""
import argparse,gzip,hashlib,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values
from independent_norm import radial_lower,static_field

ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);a=ap.parse_args();pair=a.pair;cell=pair/'geometry_memory'
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text())
protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');contract=read(pair/'TRACKED_NORM_CONTRACT.json');base=static_field(protocol)
spec=importlib.util.spec_from_file_location('original_broad_tracked_gate',repo/'experiments/v812_soft_global_reference/motion_tracker.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
states=[json.loads(line)for line in(cell/'motion_estimate.jsonl').open()];times=np.arange(657)*.01;coverage=[]
for state in states:
    if state['center']is None:continue
    cells=np.asarray(state['outer_state_cells']);now=state['time'];true=np.asarray(config['anchor_xy'])+np.sin((now+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
    current=float(np.maximum(cells[:,0]-true[0],true[0]-cells[:,1]).max(axis=1).min());norm=float((np.linalg.norm(true-true[0],axis=1)-.08*times).max())
    assert current<=1e-7 and norm<=1e-7;coverage.append(dict(step=state['step'],current_cell_excess=current,norm_displacement_excess=norm))
records=[];accepted_beyond_original=0
def verify(label,poses,state,stored):
    global accepted_beyond_original
    poses=np.asarray(poses);clock=np.arange(1,len(poses)+1)*.01;f=SimpleNamespace(**base.__dict__);original.install_time_gate(f,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    old=f.causal_values_at_times(poses,clock)
    expected=old if state['center']is None else np.maximum(old,np.minimum(pose_values(base,poses),radial_lower(base,poses,state,clock)))
    minimum=float(expected.min());assert len(poses)==328 and minimum>=.155 and abs(minimum-float(stored))<=1e-8
    accepted_beyond_original+=int(old.min()<.155)
    records.append(dict(label=label,minimum_refined_m=minimum,original_broad_minimum_m=float(old.min()),maximum_stored_minimum_error=abs(minimum-float(stored))))
state_map={x['step']:x for x in states}
for file in sorted((cell/'ordinary_certificates').glob('*.npz')):
    z=np.load(file);step=int(file.stem.split('_')[-1]);verify(str(file.relative_to(pair)),np.vstack([z['prefix_poses'],z['poses']]),state_map[step],z['minimum_causal_clearance'])
for directory in ['recovery_contracts','handover_certificates','shadow_handover_certificates']:
    for file in sorted((cell/directory).glob('*.gz')):
        with gzip.open(file,'rt')as f:c=json.load(f)
        q=np.asarray(c['qpos']);poses=np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
        verify(str(file.relative_to(pair)),np.vstack([c['prefix_poses'],poses]),c['forecast_state'],c['minimum_causal_predicted_clearance_m'])
file=cell/'discovery_stop_certificate.json.gz'
if file.exists():
    with gzip.open(file,'rt')as f:c=json.load(f)
    q=np.asarray(c['qpos']);poses=np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
    verify(str(file.relative_to(pair)),poses,c['forecast_state'],c['minimum_causal_predicted_clearance_m'])
checks=dict(public_contract=contract['source']=='PUBLIC_DECLARED_COURSE'and contract['norm_speed_m_s']==.08 and contract['original_broader_axis_motion_class_claimed']is False and contract['threshold_m']==.155 and contract['native_ticks']==328 and contract['hidden_world_geometry_used']is False,
    actual_course_matches_declaration=abs(config['maximum_speed_m_s']-.08)<=1e-12 and abs(config['amplitude_m']*config['omega_rad_s']*np.linalg.norm(config['axis_xy'])-.08)<=1e-12,
    current_and_future_norm_coverage=bool(coverage),all_saved_complete_contracts=bool(records),no_true_actor_state_in_causal_tracker=all(s['hidden_world_geometry_used']is False for s in states))
checks={k:bool(v)for k,v in checks.items()}
out=dict(status='TRACKED_NORM_COMPLETE_INDEPENDENT_GEOMETRY_PASS'if all(checks.values())else'FAIL',checks=checks,contracts=records,tracked_frames=len(coverage),norm_657_coverage_samples=657*len(coverage),
    contracts_whose_original_broad_bound_would_reject=accepted_beyond_original,count_scope='Saved accepted contract certificates, not actual backup activations or independent task samples.',new_models=0,new_integrations=0,
    scope='Declared .08 Euclidean course only; broad .12/axis class not claimed. Actual native safety and full replay audited separately.')
(pair/'TRACKED_NORM_INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='contracts'}));assert all(checks.values())
