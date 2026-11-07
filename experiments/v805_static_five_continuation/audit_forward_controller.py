"""Independent saved causal guide, no fixed scan, and six-candidate bank audit."""
import os,sys,json,argparse
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
from exact_footprint import pose_values
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired);cell=root/'geometry_memory';read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
protocol=read(root/'STATIC_PROTOCOL.json');b=np.asarray(protocol['footprint_bounds']);f=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));f.pose_values=MethodType(pose_values,f);guides=[]
for file in sorted(cell.glob('planning_*.json')):
 x=read(file);g=x['stats'].get('forward_curve')
 if g is None:continue
 if not g['selected']:guides.append(dict(step=x['step'],selected=False));continue
 old=np.asarray(g['original_path']);new=np.asarray(x['path']);n=g['sample_count'];dense=np.asarray(g['dense_prefix']);rn=g['returned_prefix_count'];k=g['guide_anchor_index'];q=np.asarray(x['pose']);end=old[k];h=end[0]-q[0];t=(dense[:,0]-q[0])/h;A=2*t**3-3*t**2+1;B=t**3-2*t**2+t;C=-2*t**3+3*t**2;D=t**3-t**2;y=A*q[1]+B*h*np.tan(q[2])+C*end[1]+D*h*np.tan(end[2]);dy=((6*t*t-6*t)*q[1]+(3*t*t-4*t+1)*h*np.tan(q[2])+(-6*t*t+6*t)*end[1]+(3*t*t-2*t)*h*np.tan(end[2]))/h
 assert np.max(abs(dense[:,1]-y))<1e-10 and np.max(abs(dense[:,2]-np.arctan(dy)))<1e-10 and np.array_equal(new[rn:],old[k+1:])and np.all(new[:,3]==1)
 assert g['continuous_static_clearance_lower_m']>=.18 and g['continuous_curvature_upper']<=g['steering_curvature_limit']+1e-10 and abs(float(f.pose_values(dense[:,:3]).min())-g['minimum_prefix_static_clearance_m'])<=1e-10 and not g['hidden_world_geometry_used']
 arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(dense[:,:2],axis=0),axis=1))];samples=np.r_[np.arange(0,arc[-1],.04),arc[-1]];expected=np.column_stack([np.interp(samples,arc,dense[:,i])for i in range(3)]+[np.ones(len(samples))]);assert np.array_equal(new[:rn],expected)
 guides.append(dict(step=x['step'],selected=True,continuous_static_clearance_lower_m=g['continuous_static_clearance_lower_m'],curvature_upper=g['continuous_curvature_upper']))
bank=[]
for d in lines(cell/'control_decisions.jsonl'):
 if d['stage']!='NOMINAL' or not d.get('candidates'):continue
 cs=d['candidates'];diff=[x for x in cs if x['proposal_role']=='DIFFERENTIAL'];features=np.asarray(cs[0]['features']);speed=features[-1];wheel=float(np.clip((speed+1.3*(speed-features[4]))/.12,-12,12));mean=.45*wheel;half=min(2,abs(mean));fronts=sorted({tuple(c['target_command'][:2])for c in cs if c['proposal_role']=='ANALYTIC'});three=[fronts[0],min(fronts,key=lambda x:abs(x[0])+abs(x[1])),fronts[-1]];expected=[[*front,mean-sign*half,mean+sign*half]for front in three for sign in[-1,1]];assert len(diff)==6 and all(np.max(abs(np.asarray(x['target_command'])-y))<=1e-12 for x,y in zip(diff,expected));bank.append(d['step'])
r=read(cell/'result.json');checks=dict(no_fixed_scan=not(cell/'observation_scan_certificate.json.gz').exists()and r['early_scan_started_step']is None,all_guide_checks=True,first_global_guide_registered_behavior=bool(guides)and guides[0]['step']==0 and (guides[0]['selected']if read(root/'ARENA_CONSTRUCTION.json')['case']['id']=='WEST_EAST'else not guides[0]['selected']),six_legal_differential_targets=bool(bank),full_native_replay=read(root/'NATIVE_REPLAY_AUDIT.json')['maximum_full_native_state_ctrl_error']<=1e-8)
out=dict(status='FORWARD_GUIDANCE_BANK_PASS'if all(checks.values())else'FAIL',checks=checks,guides=guides,bank_evaluations=len(bank),new_integrations=0);(root/'FORWARD_GUIDANCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert all(checks.values())
