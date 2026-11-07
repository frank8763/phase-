"""Independent saved-only common progress, execution commitment and reference audit."""
import argparse,gzip,hashlib,json,math
from pathlib import Path
import numpy as np


def wrap(x):return(x+math.pi)%(2*math.pi)-math.pi


def pose(q):return np.array([q[0],q[1],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))])


def segment(path,index):
    p=np.asarray(path,float);gear=int(p[min(index+1,len(p)-1),3]);lo=index;hi=index+1
    while lo>0 and int(p[lo,3])==gear:lo-=1
    while hi<len(p)-1 and int(p[hi+1,3])==gear:hi+=1
    return p[lo:hi+1,:3],gear,hi==len(p)-1


def measure(path,q):
    point=pose(q);length=0.;best=None
    for start,end in zip(path[:-1],path[1:]):
        delta=end[:2]-start[:2];norm=float(delta@delta);fraction=float(np.clip((point[:2]-start[:2])@delta/max(norm,1e-12),0,1));distance=float(np.linalg.norm(point[:2]-start[:2]-fraction*delta));arc=length+fraction*math.sqrt(norm);heading=start[2]+fraction*wrap(end[2]-start[2]);error=abs(wrap(point[2]-heading));row=(distance,arc,error)
        if best is None or distance<best[0]:best=row
        length+=math.sqrt(norm)
    contour,arc,heading=best;return dict(merit=arc-.625*contour-.625*heading,contour=contour,heading=heading)


def stopping(path,last,goal,q,v):
    p=pose(q)
    cusp=not last and np.linalg.norm(p[:2]-path[-1,:2])<=.16 and abs(wrap(p[2]-path[-1,2]))<=.25 and np.linalg.norm(v[:2])<=.05
    reached=last and np.linalg.norm(p[:2]-goal)<=.45
    return bool(cusp or reached)


def check_certificate(c,old=None):
    m=c['maneuver_contract'];p,gear,last=segment(m['reference_path'],m['reference_index']);q=np.asarray(c['qpos']);v=np.asarray(c['qvel']);origin=np.asarray(c['prefix_initial_qpos']);commit=m['committed_native_ticks'];assert commit in[32,64,328]
    a=measure(p,origin);short=measure(p,q[commit-9]);end=measure(p,q[-1]);short_gain=short['merit']-a['merit'];full_gain=end['merit']-a['merit'];goal=np.asarray(m['goal_xy'])
    assert len(q)==len(v)==len(c['controls'])==320 and len(c['prefix_poses'])==8
    assert max(abs(short_gain-m['route_merit_gain_commit_m']),abs(full_gain-m['route_merit_gain328_m']),abs(end['contour']-m['terminal_contour_m']),abs(end['heading']-m['terminal_heading_error_rad']))<=1e-9
    allowed=end['contour']<=.20 and end['heading']<=.50 and(short_gain>=.02-1e-10 or stopping(p,last,goal,q[commit-9],v[commit-9]))and(full_gain>=.02-1e-10 or stopping(p,last,goal,q[-1],v[-1]))
    if old is not None:
        cursor=m['old_cursor'];oldq=old['initial_qpos']if cursor==0 else old['qpos'][cursor-1];oldv=old['initial_qvel']if cursor==0 else old['qvel'][cursor-1]
        assert max(np.max(abs(origin-oldq)),np.max(abs(np.asarray(m['real_entry_qvel'])-oldv)))<=1e-8
        assert abs(c['created_time']-old['start_time']-.01*cursor)<=1e-8
        improvement=end['merit']-measure(p,np.asarray(old['qpos'])[-1])['merit'];assert abs(improvement-m['old_terminal_merit_improvement_m'])<=1e-9;allowed=allowed and improvement>=.02-1e-10
    assert m['normal_allowed']==bool(allowed)
    if not allowed:assert m['mode']=='EXPLICIT_FINITE_RECOVERY'and m['old_created_step']is None
    assert c['minimum_causal_predicted_clearance_m']>=.155 and c['minimum_predicted_self_domain_margin_m']>=.002 and np.linalg.norm(v[-1,:2])<=.025
    if 'one_cycle_continuation'in c:
        e=c['one_cycle_continuation'];assert len(e['extra_qpos'])==8 and e['minimum_clearance_m']>=.155 and e['minimum_self_margin_m']>=.002 and e['terminal_speed_m_s']<=.025
    return dict(gear=gear,normal_allowed=bool(allowed),short_gain=short_gain,full_gain=full_gain,commit_native=m['execution_commit_native'])


def audit(pair):
    cell=pair/'geometry_memory';read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(x)for x in p.read_text().splitlines()]if p.exists()else[]
    execution=lines(cell/'v648_execution.jsonl');ad=lines(cell/'model_admission.jsonl');states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};plans=[read(p)for p in cell.glob('planning_*.json')];ids=read(cell/'ACTUATOR_COMMAND_CONTRACT.json')['ids'];snapshots={};records=[]
    for d in ['progress_certificates','handover_certificates','recovery_contracts']:
        for f in(cell/d).glob('*.gz'):
            c=json.load(gzip.open(f,'rt'));snapshots[c['created_step']]=c
    for row in ad:
        if row['status']!='MODEL_SAFE_COMMAND'and not row.get('certified_backup_handover'):continue
        s=row['step'];c=snapshots[s];tracked=states[s]['center']is not None
        if not tracked:assert 'maneuver_contract'not in c;continue
        m=c['maneuver_contract'];assert m['created_step']==s and m['hidden_world_geometry_used']is False
        assert any(p['step']<=s and p['path']==m['reference_path']for p in plans),'REFERENCE_WITHOUT_CAUSAL_PLAN'
        assert np.array_equal(m['goal_xy'],read(pair/'STATIC_PROTOCOL.json')['goal_xy'])
        old=None if m['old_created_step']is None else snapshots[m['old_created_step']];verified=check_certificate(c,old)
        if 'renewal_reserve'in c:
            from reference_certificate_audit import independent_values
            extra=c['renewal_reserve'];assert extra['total_native_ticks']==456 and len(extra['extra_qpos'])==len(extra['extra_qvel'])==len(extra['extra_controls'])==128
            from self_geometry import containment_margin
            q=np.asarray(extra['extra_qpos']);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));full=np.vstack((c['prefix_poses'],c['poses'],np.c_[q[:,:2],yaw]));values=independent_values(full,c['forecast_state'],read(pair/'STATIC_PROTOCOL.json'));assert len(values)==456 and abs(float(values.min())-extra['minimum_clearance_m'])<=1e-8
            if extra.get('required',True):assert values.min()>=.155
            else:assert np.linalg.norm(np.asarray(c['qpos'])[-1,:2]-np.asarray(m['goal_xy']))<=.45 and independent_values(full[:328],c['forecast_state'],read(pair/'STATIC_PROTOCOL.json')).min()>=.155
            assert containment_margin(np.asarray(extra['extra_self_bounds']),np.asarray(read(pair/'STATIC_PROTOCOL.json')['footprint_bounds'])).min()>=.002 and np.linalg.norm(np.asarray(extra['extra_qvel'])[-1,:2])<=.025
            assert abs(extra['absolute_end_time']-c['created_time']-4.56)<=1e-8 and extra['no_future_observations_assumed']
            actuator=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');limit=np.asarray(actuator['limits']);rate=np.asarray(actuator['rate']);controls=np.vstack((c['prefix_command'],c['controls'],extra['extra_controls']));assert np.all(controls>=limit[:,0]-1e-12)and np.all(controls<=limit[:,1]+1e-12)and np.all(abs(np.diff(controls[::8],axis=0))<=rate+1e-12)
            tail=np.asarray(extra['extra_controls']);previous=np.asarray(c['controls'])[-1];target=np.r_[np.asarray(c['target'])[:2],0.,0.]if 'reference_following'not in c else np.r_[np.asarray(c['reference_following']['targets'])[-1,:2],0.,0.];expected=[]
            for tick in range(0,128,8):
                previous=np.clip(np.clip(target,limit[:,0],limit[:,1]),previous-rate,previous+rate);expected.extend([previous.copy()for _ in range(8)])
            assert np.max(abs(tail-np.asarray(expected)))<=1e-12
        assert np.max(abs(np.asarray(execution[s]['qpos_full'])-c['initial_qpos']))<=1e-8
        assert np.max(abs(np.asarray(execution[s]['qvel_full'])-c['initial_qvel']))<=1e-8 and np.array_equal(np.asarray(execution[s]['ctrl'])[ids],c['prefix_command'])
        end=min(s+verified['commit_native']//8,len(execution))
        for step in range(s+1,end):
            off=(step-s)*8;actual=execution[step];assert max(np.max(abs(np.asarray(actual['qpos_full'])-c['qpos'][off-1])),np.max(abs(np.asarray(actual['qvel_full'])-c['qvel'][off-1])))<=1e-8
            assert np.array_equal(np.asarray(actual['ctrl'])[ids],c['controls'][off-8]);assert ad[step]['status']=='RETAINED_REVERSE_BRAKE_CONTRACT'and ad[step]['retained_from_step']==s
        records.append(dict(step=s,**verified,actual_committed_public=end-s))
    latency=read(cell/'CONTROL_LATENCY.json');assert len(latency['records'])==len(execution)
    native_count=0;native_error=0.;stop_certificate=json.load(gzip.open(cell/'discovery_stop_certificate.json.gz','rt'))if(cell/'discovery_stop_certificate.json.gz').exists()else None
    for native in map(json.loads,gzip.open(cell/'dynamic_native.jsonl.gz','rt')):
        n=native['physics_step']-1;s=n//8;offset=n%8;gate=ad[s]
        if gate['status']=='DISCOVERY_BRAKE_CONTRACT':
            c=stop_certificate;i=gate['contract_native_cursor']+offset;q=c['qpos'][i];v=c['qvel'][i];ctrl=c['controls'][i]
        elif gate['status']=='RETAINED_REVERSE_BRAKE_CONTRACT':
            c=snapshots[gate['retained_from_step']];i=gate['contract_native_cursor']+offset;q=c['qpos'][i];v=c['qvel'][i];ctrl=c['controls'][i]
        else:
            assert gate['status']=='MODEL_SAFE_COMMAND'or gate.get('certified_backup_handover');c=snapshots[s];assert len(c['prefix_native_qpos'])==len(c['prefix_native_qvel'])==8;q=c['prefix_native_qpos'][offset];v=c['prefix_native_qvel'][offset];ctrl=c['prefix_command']
        error=max(float(np.max(abs(np.asarray(native['qpos_full'])-q))),float(np.max(abs(np.asarray(native['qvel_full'])-v))),float(np.max(abs(np.asarray(native['actual_ctrl'])[ids]-ctrl))));native_error=max(native_error,error);assert error<=1e-8;native_count+=1
    assert native_count==len(execution)*8
    out=dict(status='COMMON_MANEUVER_AND_ACTUAL_COMMITMENT_PASS',checks=dict(all_tracked_selections_have_common_proof=True,old_endpoint_and_state_join=True,actual_committed_controls_and_states=True,every_native_matches_full_saved_certificate=True,full328_retained=True,causal_references=True,latency_complete=True),records=records,native_certificate_matches=native_count,maximum_native_certificate_error=native_error,new_models=0,new_integrations=0,global_arrival_or_realtime_guarantee=False)
    (pair/'MANEUVER_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],tracked_certificates=len(records))))
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pair',type=Path);audit(p.parse_args().pair)
