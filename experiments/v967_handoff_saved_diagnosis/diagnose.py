"""Saved V962 data only. Distinguish actuator continuity from closed-loop path tracking."""
import hashlib,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v967_handoff_saved_diagnosis';P=R/'runs/v858_nav2_verified/v962/handoff_left'
a=np.load(P/'HANDOFF_ARRAYS.npz');body=a['body'];ref=a['expected'];origin=a['origin'];shapes=json.loads((P/'SHAPING.json').read_text())
e=body[420:,:2]-ref[:,:2];theta=np.arctan2(np.sin(body[420:,2]-ref[:,2]),np.cos(body[420:,2]-ref[:,2]));f=np.array([math.cos(origin[2]),math.sin(origin[2])]);l=np.array([-f[1],f[0]])
distance=np.linalg.norm(e,axis=1);forward=e@f;lateral=e@l
# Exact closest point on every saved1mm reference chord, independently of time alignment.
poly=np.vstack([origin[:3],ref]);segments=poly[1:,:2]-poly[:-1,:2];norm=(segments*segments).sum(axis=1);valid=norm>1e-18;starts=poly[:-1,:2][valid];segments=segments[valid];norm=norm[valid]
spatial=[]
for point in body[420:,:2]:
 fraction=np.clip(((point-starts)*segments).sum(axis=1)/norm,0,1);spatial.append(float(np.linalg.norm(point-starts-fraction[:,None]*segments,axis=1).min()))
first=lambda arr,limit:None if not np.any(arr>limit)else int(np.flatnonzero(arr>limit)[0])+420
neutral=next(row['shape']['native_tick']for row in shapes if row['shape']['mode']=='RATE_LIMITED_FORWARD_CONTINUATION'and abs(row['shape']['selected'][1])<1e-12)
report=dict(models=0,integrations=0,new_controls=0,new_navigation=0,old_failure_regraded=False,
 source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[P/'HANDOFF_ARRAYS.npz',P/'SHAPING.json',P/'QUALIFICATION.json']},
 prefix420_state_control_error=0.,actual_native=1820,own_replay_native=1820,private_native=0,
 first_time_position_exceeds04_native=first(distance,.04),first_heading_exceeds035_native=first(abs(theta),.035),first_spatial_error_exceeds04_native=first(np.asarray(spatial),.04),
 maximum_time_position_error_m=float(distance.max()),maximum_geometric_path_distance_m=float(max(spatial)),maximum_heading_error_rad=float(abs(theta).max()),
 end_forward_request_tick1619=dict(forward_position_error_m=float(forward[1199]),lateral_position_error_m=float(lateral[1199]),heading_error_rad=float(theta[1199]),actual_forward_speed_m_s=float(body[1619,3])),
 first_command_steering_neutral_native=neutral,actual_heading_error_after_neutral_settles_rad=float(theta[199]),
 actual_forward_speed_mean_after_first02s_m_s=float(body[440:1620,3].mean()),actual_forward_progress_m=1.1406209123621407,
 observations=['Actual steering continuity, forward motion and braking were exercised; original420prefix exact.',
 'Worker requests fixed.1m/s then stop; steering rate limiter anchors measured steering but has no path-position/heading feedback during continuation.',
 'By tick619 steering is almost neutral, while body heading already differs by.03452rad. This heading offset persists and lateral error grows during straight driving.',
 'Actual mean forward speed.09607m/s is below fixed nominal.1; time-aligned along-track lag accumulates as well.',
 'Geometric path distance also exceeds.04, so time-alignment alone does not explain away failure.',
 'Observed mismatch is in execution/reference tracking of this component; no global planner or online obstacle replan was called, so this test cannot attribute failure to A* or dynamic replanning.',
 'Mechanical cause of yaw transient is not uniquely identified by this one trace. No causal claim of inertia, tire slip or servo delay alone.',
 'Next gate should exercise actual closed-loop path tracking from the held-steering stopped state, using existing RPP pose feedback and unchanged command safety gates. Pure steering smoothing is not sufficient.'],
 physical_authority=False,night_dependency_chain_stopped=True)
(O/'DIAGNOSIS.json').write_text(json.dumps(report,indent=2)+'\n')
np.savetxt(O/'ERRORS.csv',np.c_[np.arange(420,1820),distance,forward,lateral,theta,spatial],delimiter=',',header='native_tick,time_position_m,forward_error_m,lateral_error_m,heading_error_rad,geometric_path_distance_m',comments='')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(2,1,figsize=(10,7),constrained_layout=True)
ax[0].plot(ref[:,0],ref[:,1],'--',label='Command-integrated reference',color='#1475ba');ax[0].plot(body[420:,0],body[420:,1],label='Measured vehicle',color='#d75035');ax[0].scatter(*origin[:2],s=25,color='black',label='Stopped handoff start');ax[0].set_aspect('equal');ax[0].set_xlabel('x (m)');ax[0].set_ylabel('y (m)');ax[0].legend();ax[0].grid(alpha=.25);ax[0].set_title('V962: forward progress 1.141 m; path tracking gate failed')
t=np.arange(1,1401)*.01
ax[1].plot(t,distance*100,label='Time-aligned position error (cm)');ax[1].plot(t,np.asarray(spatial)*100,label='Distance to path (cm)');ax[1].plot(t,abs(theta)*180/math.pi,label='Heading error (degree)');ax[1].axhline(4,color='#555',linestyle=':',label='Position gate 4 cm');ax[1].axvline(12,color='#777',linestyle='--',label='Final brake starts');ax[1].set_xlabel('Seconds after handoff');ax[1].set_ylabel('Error (label units)');ax[1].legend(ncol=2);ax[1].grid(alpha=.25)
fig.savefig(O/'handoff_failure.png',dpi=160);plt.close(fig)
print(json.dumps({k:v for k,v in report.items()if k not in ['source_sha256','observations']},indent=2))
