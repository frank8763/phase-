"""Full saved physical and closed-loop reference audit, no model initialization."""
import json
import math
import sys
import traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]

def tracking(path,actual):
    path=np.asarray(path);assert path.ndim==2 and path.shape[1]==3 and np.isfinite(path).all()
    keep=np.r_[True,np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1)>1e-12];path=path[keep];assert len(path)>=2
    xy=path[:,:2];delta=np.diff(xy,axis=0);norm=(delta*delta).sum(axis=1)
    assert np.all(norm>0)
    distance=heading=0.
    for p in actual:
        t=np.clip(((p[:2]-xy[:-1])*delta).sum(axis=1)/norm,0,1)
        d=np.linalg.norm(p[:2]-xy[:-1]-t[:,None]*delta,axis=1);i=int(np.argmin(d))
        a=path[i,2]+t[i]*math.atan2(math.sin(path[i+1,2]-path[i,2]),math.cos(path[i+1,2]-path[i,2]))
        distance=max(distance,float(d[i]));heading=max(heading,abs(math.atan2(math.sin(p[2]-a),math.cos(p[2]-a))))
    return dict(passed=distance<=.04 and heading<=.035,maximum_path_distance_m=distance,maximum_heading_error_rad=heading,samples=len(actual))

def independent_continuation(packet):
    q=packet['steering']['position'];left=math.tan(q[0])/(.6+.27*math.tan(q[0]));right=math.tan(q[1])/(.6-.27*math.tan(q[1]))
    assert abs(left-right)<=.02
    angle=math.atan(.6*max(-.758770385,min(.758770385,(left+right)/2)));rows=[list(packet['body'][:3])]
    for index in range(1200):
        x,y,a=rows[-1];wheel=math.copysign(max(0.,abs(angle)-6*(index+.5)*.001),angle);k=math.tan(wheel)/.6;b=a+k*.001
        if abs(k)<1e-12:point=[x+.001*math.cos(a),y+.001*math.sin(a),b]
        else:point=[x+(math.sin(b)-math.sin(a))/k,y+(math.cos(a)-math.cos(b))/k,b]
        rows.append(point)
    return np.asarray(rows)

def audit(task):
    out=Path(task['output']);answer=dict(passed=False,evidence_passed=False,functional_passed=False)
    try:
        native=json.loads((out/'RESULT.json').read_text());ros=json.loads((out/'ROS_RESULT.json').read_text())
        stages=json.loads((out/'CLOSED_HANDOFF.json').read_text())['stages']if(out/'CLOSED_HANDOFF.json').exists()else[]
        if len(stages)!=2:
            answer.update(reason='TWO_ACTUAL_RPP_STAGES_NOT_COMPLETED',native=native);raise AssertionError('INCOMPLETE_CLOSED_LOOP_COMPONENT')
        adjusted=dict(task,dynamic=False,goal_xy=stages[1]['path'][-1][:2])
        sys.path.insert(0,str(R/'experiments/v862_ready_static'))
        from audit_result import audit as base_audit
        answer=base_audit(adjusted)
        with np.load(out/'physics/NATIVE_TRACE.npz')as f:
            q=f['qpos'];v=f['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
            body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
            setup=json.loads((out/'physics/SETUP.json').read_text());enc=np.c_[q[:,setup['steering_qpos_addresses']],v[:,setup['steering_qvel_addresses']]]
        checks={};reports=[]
        for i,s in enumerate(stages):
            start=s['start_packet'];end=s['end_packet'];lo=start['native_tick'];hi=end['native_tick'];assert hi>lo
            for p in [start,end,s['path_generation_packet']]:
                n=p['native_tick'];assert n>0 and np.max(abs(np.asarray(p['body'])-body[n-1]))<=1e-8
                assert np.max(abs(np.r_[p['steering']['position'],p['steering']['velocity']]-enc[n-1]))<=1e-8
            observed=tracking(s['path'],body[lo:hi]);reports.append(observed)
            checks['full_stage'+str(i)+'_reference_tracking']=observed['passed']
            checks['stage'+str(i)+'_actual_stop']=bool(max(abs(end['body'][3]),abs(end['body'][4]))<=.03 and abs(enc[hi-1,2:]).max()<=.03)
            checks['stage'+str(i)+'_RPP_action_success']=s['follow_status']==4
        first=stages[0];second=stages[1];initial=np.asarray(first['start_packet']['body']);held=np.asarray(first['end_packet']['body']);last=np.asarray(second['end_packet']['body'])
        checks['actual_curve_and_held_wheels_exercised']=bool(np.linalg.norm(held[:2]-initial[:2])>=.12 and abs(enc[first['end_packet']['native_tick']-1,:2]).max()>=.2)
        x,y,a=first['path_generation_packet']['body'][:3];k=.758770385
        first_expected=np.asarray([[x+(math.sin(a+k*s)-math.sin(a))/k,y+(math.cos(a)-math.cos(a+k*s))/k,a+k*s]for s in np.linspace(0.,.20,201)])
        checks['first_path_exact_causal_arc']=bool(np.max(abs(first_expected-first['path']))<=1e-9)
        checks['second_path_exact_causal_measured_steering']=bool(np.max(abs(independent_continuation(first['end_packet'])-second['path']))<=1e-9)
        progress=float((last[:2]-held[:2])@np.array([math.cos(held[2]),math.sin(held[2])]))
        checks['actual_forward_at_least1m']=progress>=1.
        checks['endpoint_within04']=float(np.linalg.norm(last[:2]-second['path'][-1][:2]))<=.04
        checks['full_final_half_second_settled']=bool(abs(body[-50:,3:5]).max()<=.03)
        checks['original_body_limits']=bool(abs(body[:,3]).max()<=.13 and abs(body[:,4]).max()<=.16)
        sys.path.insert(0,str(C))
        from motion_audit import audit as motion_audit
        from tube_audit import audit_tubes
        from ingress_audit import audit_ingress
        from recovery_audit import audit as recovery_audit
        from shaping_audit import audit as shaping_audit
        sub={name:fn(out)for name,fn in [('motion',motion_audit),('tube',audit_tubes),('ingress',audit_ingress),('recovery',recovery_audit),('shaping',shaping_audit)]}
        master=ros.get('global_master_readiness',{});replies=master.get('accepted_replies',[])
        checks['actual_full_map_before_arm']=bool(master.get('passed')and master.get('native_tick')==0 and len(replies)==2 and all(x['passed']and x['missing_static_cells']==0 and x['unknown_cells']==0 and x['required_static_cells']==72683 and x['cells']==1000000 for x in replies))
        sensor=json.loads((out/'physics/EXACT_SENSOR_BINDING.json').read_text())
        checks['original_sensor_and_actor']=bool(sensor['passed']and setup['dynamic']and setup['actor']['phase_rad']==task['phase']and setup['actor']['maximum_speed_m_s']==.08 and setup['actor']['amplitude_m']==.25 and setup['actor']['radius_m']==.1)
        checks['all_original_causal_command_and_native_audits']=all(v['passed']for v in sub.values())
        answer.update(component_checks=checks,tracking=reports,subaudits=sub,actual_forward_progress_m=progress,
            component_scope='Actual installed RPP curve-stop and1.2m steering-continuous forward handoff; no full-route/dynamic denominator',
            functional_passed=bool(answer['functional_passed']and all(checks.values())),evidence_passed=bool(answer['evidence_passed']and checks['all_original_causal_command_and_native_audits']and checks['actual_full_map_before_arm']and checks['original_sensor_and_actor']))
        answer['passed']=bool(answer['functional_passed']and answer['evidence_passed']and native['passed'])
    except BaseException as e:answer.update(passed=False,error=repr(e),traceback=traceback.format_exc())
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(answer,indent=2)+'\n');return answer
