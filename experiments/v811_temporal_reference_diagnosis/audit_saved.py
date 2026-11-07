"""Independent saved geometry and actual reference-contour diagnosis; no models."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'experiments/v809_time_reference_global'))
from independent_time_reference import field
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text())
root=repo/'runs/v811_temporal_reference_diagnosis'
rows=read(root/'RESULTS.json')
protocol=read(repo/'runs/v809_time_reference_global/main_slot01/paired/STATIC_PROTOCOL.json')
records=[]
for r in rows:
    z=np.load(root/f'step{r["step"]:04d}.npz')
    f=field(protocol,r['causal_state'])
    v=pose_values(f,z['dense'])
    error=float(np.max(abs(v-z['current_values'])))
    checks=dict(source_sha=hashlib.sha256((repo/r['input_file']).read_bytes()).hexdigest()==r['input_sha256'],
        independent_current_geometry=error<=1e-10,
        current_floor=v.min()>=r['current_only_forward_stats']['guard_m']-1e-8,
        forward_only=bool(np.all(z['path'][:,3]==1)),
        rejected_future_not_mislabelled=bool(np.any(z['original_timed_values']<r['current_only_forward_stats']['guard_m']-1e-8))and r['reference_is_not_actual_execution_admission'])
    checks={k:bool(v)for k,v in checks.items()}
    records.append(dict(step=r['step'],checks=checks,passed=all(checks.values()),maximum_geometry_error=error))
cell=repo/'runs/v809_time_reference_global/main_slot01/paired/geometry_memory'
trace=read(cell/'trace.json');plans=[read(p)for p in sorted(cell.glob('planning_*.json'))];contours=[];heading=[]
for r in trace:
    if r['step']<303:continue
    plan=next(x for x in reversed(plans)if x['step']<=r['step'])
    if plan['path']is None:continue
    p=np.asarray(plan['path']);point=np.asarray(r['pose'][:2]);a=p[:-1,:2];d=p[1:,:2]-a
    u=np.clip(np.sum((point-a)*d,axis=1)/np.maximum(np.sum(d*d,axis=1),1e-18),0,1)
    projection=a+u[:,None]*d;dist=np.linalg.norm(point-projection,axis=1);j=int(np.argmin(dist));contours.append(float(dist[j]))
    yaw=p[j,2]+u[j]*((p[j+1,2]-p[j,2]+np.pi)%(2*np.pi)-np.pi)
    heading.append(abs(float((r['pose'][2]-yaw+np.pi)%(2*np.pi)-np.pi)))
out=dict(status='FIXED_SAVED_CAUSAL_DIAGNOSIS_AUDIT_PASS'if len(rows)==4 and all(x['passed']for x in records)else'FAIL',
    records=records,tracking=dict(samples=len(contours),maximum_contour_m=max(contours),p95_contour_m=float(np.percentile(contours,95)),
        mean_contour_m=float(np.mean(contours)),samples_above_005_m=sum(x>.05 for x in contours),maximum_nearest_heading_error_rad=max(heading),
        scope='Nearest segment of contemporaneous saved full reference; not proof of commanded cusp or vehicle dynamics.'),
    new_models=0,integrations=0,scope='Causal contrast and independent current geometry, not a physical execution certificate.')
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out));assert out['status']=='FIXED_SAVED_CAUSAL_DIAGNOSIS_AUDIT_PASS'
