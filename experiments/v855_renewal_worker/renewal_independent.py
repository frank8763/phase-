"""Saved-only reconstruction of the extra128 native continuation witness."""
import numpy as np
from reference_certificate_audit import independent_values,check_successor
from self_geometry import containment_margin


def verify(c,protocol,actuator):
    extra=c['renewal_reserve'];q=np.asarray(extra['extra_qpos']);v=np.asarray(extra['extra_qvel']);tail=np.asarray(extra['extra_controls']);bounds=np.asarray(extra['extra_self_bounds'])
    assert extra['total_native_ticks']==456 and len(q)==len(v)==len(tail)==128 and len(bounds)==129
    assert np.isfinite(q).all()and np.isfinite(v).all()and np.isfinite(tail).all()and np.isfinite(bounds).all()
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));poses=np.c_[q[:,:2],yaw]
    assert np.max(abs(poses-extra['extra_poses']))<=1e-12
    full=np.vstack((c['prefix_poses'],c['poses'],poses));values=independent_values(full,c['forecast_state'],protocol)
    assert len(values)==456 and abs(float(values.min())-extra['minimum_clearance_m'])<=1e-8
    assert type(extra['required'])is bool
    if extra['required']:assert values.min()>=.155
    else:assert np.linalg.norm(np.asarray(c['qpos'])[-1,:2]-np.asarray(protocol['goal_xy']))<=.45
    limit=np.asarray(actuator['limits']);rate=np.asarray(actuator['rate']);original=check_successor(c,protocol,limit,rate)
    self_margin=float(containment_margin(bounds,np.asarray(protocol['footprint_bounds'])).min());speed=float(np.linalg.norm(v[-1,:2]));assert self_margin>=.002 and speed<=.025 and abs(speed-extra['terminal_speed_m_s'])<=1e-10
    assert extra['minimum_self_margin_m']<=self_margin+1e-10 and extra['minimum_self_margin_m']>=.002
    assert abs(extra['absolute_end_time']-c['created_time']-4.56)<=1e-8 and extra['no_future_observations_assumed']is True
    controls=np.vstack((c['prefix_command'],c['controls'],tail));assert np.all(controls>=limit[:,0]-1e-12)and np.all(controls<=limit[:,1]+1e-12)and np.all(abs(np.diff(controls[::8],axis=0))<=rate+1e-12)
    previous=np.asarray(c['controls'])[-1];target=np.r_[np.asarray(c['target'])[:2],0.,0.]if 'reference_following'not in c else np.r_[np.asarray(c['reference_following']['targets'])[-1,:2],0.,0.];expected=[]
    for _ in range(0,128,8):
        previous=np.clip(np.clip(target,limit[:,0],limit[:,1]),previous-rate,previous+rate);expected.extend([previous.copy()for _ in range(8)])
    assert np.max(abs(tail-np.asarray(expected)))<=1e-12
    successor=c['one_cycle_continuation']
    for key in ['qpos','qvel','poses','controls']:assert np.array_equal(np.asarray(extra['extra_'+key])[:8],np.asarray(successor['extra_'+key]))
    return dict(passed=True,native_ticks=456,minimum_clearance_m=float(values.min()),extra_self_margin_m=self_margin,extra_terminal_speed_m_s=speed,original_successor336=original,models=0,integrations=0)
