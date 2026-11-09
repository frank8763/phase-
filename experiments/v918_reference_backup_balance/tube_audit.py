"""Independent saved causal provenance, analytical tube and actual execution checks."""
import gzip,json,math
from pathlib import Path
import numpy as np
def independent_lower(body,v,w,source_age,support,delay,known,source=None):
    # Twice the online sample density, separately written exact circular arc and
    # rectangle support functions; one-step Lipschitz reserve covers the gaps.
    from command_tube import NORMALS
    from snapshot_geometry import field
    from exact_footprint import pose_values
    t=np.linspace(0.,2.2,221);u=np.minimum(t,.2);a=body[2]+w*u
    if abs(w)<1e-10:x=body[0]+v*u*np.cos(body[2]);y=body[1]+v*u*np.sin(body[2])
    else:x=body[0]+(np.sin(a)-np.sin(body[2]))*v/w;y=body[1]+(np.cos(body[2])-np.cos(a))*v/w
    r=math.hypot(.44,.375);position_residual=.04 if v*body[3]<0 else .02
    reserve=position_residual+r*.035+delay*(.13+r*.16)+.01*(.13+r*.16+.08)
    poses=np.column_stack((x,y,a));static=float(pose_values(field(known),poses).min())-reserve
    dynamic=None
    if support is not None:
        projection=np.column_stack((x,y))@NORMALS.T
        theta=np.arctan2(NORMALS[:,1],NORMALS[:,0])[None,:]
        robot_min=projection-.44*abs(np.cos(a[:,None]-theta))-.375*abs(np.sin(a[:,None]-theta))
        high=np.asarray(support)[None,:]+.08*(source_age+delay+t[:,None])
        if source and source.get('periodic'):
            prior=source['periodic'];vertices=prior['vertices'];at=source['source_scan_sim_time']+source_age+delay+t
            basis=np.c_[np.ones(len(t)),np.sin(.32*at),np.cos(.32*at)]
            values=[basis@np.asarray(p).T for p in vertices]
            independent=np.c_[[z.max(axis=1)+2e-7 for z in values]+[-z.min(axis=1)+2e-7 for z in values]].T
            high=np.minimum(high,independent)
        distance=robot_min-high-.1
        dynamic=float(distance.max(axis=1).min())-reserve
    return static,dynamic
def audit_tubes(out):
    out=Path(out);rows=json.loads(gzip.decompress((out/'COMMAND_TUBES.json.gz').read_bytes()))
    trace=np.load(out/'physics/NATIVE_TRACE.npz');q=trace['qpos'];vel=trace['qvel']
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    recorded=np.c_[q[:,:2],yaw,vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw),vel[:,5]]
    saved=json.loads(gzip.decompress((out/'MOTION_ENVELOPE.json.gz').read_bytes()))
    sources={x['native_tick']:x for x in saved['states']}
    known=json.loads((out/'physics/SETUP.json').read_text())['known']
    checks=dict(nonempty=bool(rows),causal=True,body_matches_native=True,source_matches_tracker=True,command_limits=True,finite_horizon=True,admission_threshold=True,independent_dense_geometry=True)
    accepted=0;fallback=0;maximum_body_error=0.;renewals=0;last_tick=-1;retained_count=0;anchors={}
    checks['wait_renewals_zero_and_causal']=True
    checks['terminal_cycle_independently_qualified']=True
    checks['retained_proof_chain_and_actual_body']=True
    checks['conditional_residual_class']=True
    for row in rows:
        p,s,a=row['packet'],row['source'],row['proof'];tick=p['native_tick']
        if row.get('wait_renewal'):
            renewals+=1;at=row.get('last_nominal_at')
            checks['wait_renewals_zero_and_causal'] &= row['wanted']==[0.,0.] and a['v']==0. and a['w']==0. and (at is None or a['issued_at']-at>=.15-1e-9) and tick>=last_tick
        last_tick=tick
        checks['causal'] &= s['source_native_tick']<=tick and a['body_native_tick']==tick and a['source_native_tick']==s['source_native_tick']
        error=float(np.max(abs(recorded[tick-1]-p['body']))) if 1<=tick<=len(recorded)else float('inf')
        maximum_body_error=max(maximum_body_error,error);checks['body_matches_native'] &= error<=1e-8
        src=sources.get(s['source_native_tick']);bounds=None if src is None else src.get('support_bounds')
        # tracker rows store their exact center support. A missing source is a failure.
        checks['source_matches_tracker'] &= src is not None and bounds==s['support_bounds']
        checks['command_limits'] &= abs(a['v'])<=.1+1e-10 and abs(a['w'])<=abs(a['v'])*.758770385+1e-9
        checks['finite_horizon'] &= a['commit_s']==.2 and a['brake_s']==2. and abs(a['expires_at']-a['issued_at']-.2)<1e-8
        if row.get('retained_previous'):
            retained_count+=1;old=anchors.get(row.get('retained_anchor_tick'));ok=old is not None
            if ok:
                dt=(tick-old['body_native_tick'])*.01
                ok=dt>=0 and (dt<=2.2+old['body_age_s']+.05+1e-8 or old.get('terminal_cycle_qualified')is True)
                u=min(dt,.2);v0,w0=old['v'],old['w'];b=old['body'];angle=b[2]+w0*u
                if abs(w0)<1e-10:xy=np.array(b[:2])+v0*u*np.array([math.cos(b[2]),math.sin(b[2])])
                else:xy=np.array(b[:2])+v0/w0*np.array([math.sin(angle)-math.sin(b[2]),math.cos(b[2])-math.cos(angle)])
                delay=old['body_age_s']+.05
                ok &= np.linalg.norm(np.array(p['body'][:2])-xy)<=old['residual_position_m']+.13*delay+1e-8
                ok &= abs(math.atan2(math.sin(p['body'][2]-angle),math.cos(p['body'][2]-angle)))<=.035+.16*delay+1e-8
            checks['retained_proof_chain_and_actual_body'] &= ok and not a['passed']
        if a['passed']:
            anchors[tick]=a
            checks['conditional_residual_class'] &= a['residual_position_m']==(.04 if a['v']*p['body'][3]<0 else .02)
            if s.get('periodic') is not None:
                from periodic_support import swept_bounds
                upper=swept_bounds(s['periodic']['vertices'],0.,2*math.pi/.32)
                v0,w0=a['v'],a['w'];b=p['body'];angle=b[2]+w0*.2
                if abs(w0)<1e-10:xy=np.array(b[:2])+v0*.2*np.array([math.cos(b[2]),math.sin(b[2])])
                else:xy=np.array(b[:2])+v0/w0*np.array([math.sin(angle)-math.sin(b[2]),math.cos(b[2])-math.cos(angle)])
                from command_tube import NORMALS
                theta=np.arctan2(NORMALS[:,1],NORMALS[:,0]);low=xy@NORMALS.T-.44*abs(np.cos(angle-theta))-.375*abs(np.sin(angle-theta))
                terminal=float(np.max(low-upper-.1)-a['spatial_reserve_m'])
                checks['terminal_cycle_independently_qualified'] &= a.get('terminal_cycle_qualified')is True and terminal>=.155 and abs(terminal-a['terminal_cycle_lower_m'])<=1e-9
            accepted+=1;fallback+=int([a['v'],a['w']]!=row['wanted'])
            checks['admission_threshold'] &= a['static_lower_m']>=.155 and (a['dynamic_lower_m'] is None or a['dynamic_lower_m']>=.155)
            sl,dl=independent_lower(p['body'],a['v'],a['w'],a['source_age_s'],s['support_bounds'],a['body_age_s']+.05,known,s)
            checks['independent_dense_geometry'] &= sl>=.155 and (dl is None or dl>=.155)
    deferrals=json.loads((out/'ADMISSION_DEFERRALS.json').read_text())
    accepted_proofs=[row['proof']for row in rows if row['proof']['passed']]
    deferred_ok=True
    for event in deferrals:
        old=event['retained_proof'];packet=event['packet'];tick=packet['native_tick'];age=event['at']-packet['body_measured_at'];elapsed=(tick-old['body_native_tick'])*.01
        deferred_ok &= old in accepted_proofs and event['reason']=='STALE_COMMAND_BODY' and .05<age<=.2
        deferred_ok &= elapsed>=0 and (elapsed<=2.2+old['body_age_s']+.05+1e-8 or old.get('terminal_cycle_qualified')is True)
        deferred_ok &= 1<=tick<=len(recorded) and np.max(abs(recorded[tick-1]-packet['body']))<=1e-8
    checks['stale_new_proposal_retains_only_old_accepted_proof']=bool(deferred_ok)
    commands=json.loads((out/'COMMANDS.json').read_text())['cmd_vel']
    checks['only_accepted_proofs_dispatched']=len(commands)==accepted
    ros=json.loads((out/'ROS_RESULT.json').read_text());n=json.loads((out/'RESULT.json').read_text())
    checks['actual_runtime_tube_monitor_completed']=n['status']=='NATIVE_COMPLETE' and 'EMPIRICAL_'not in str(n.get('error',''))
    checks['no_unqualified_command_failure']='COMMAND_CONTRACT_FAILURE'not in str(ros.get('error',''))
    return dict(passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},accepted_commands=accepted,zero_fallback_commands=fallback,
                maximum_saved_body_error=maximum_body_error,qualified_zero_wait_renewals=renewals,retained_certificate_decisions=retained_count,stale_proposal_deferrals=len(deferrals),empirical_limits_not_formal_reachability=True)
