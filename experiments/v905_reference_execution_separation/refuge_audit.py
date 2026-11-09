"""Independent saved-state reconstruction. No model initialization or stepping."""
import gzip, json, math
from pathlib import Path
import numpy as np
from refuge_logic import choose_refuge,retained_suffix

NORMALS=np.c_[np.cos(np.arange(16)*2*np.pi/16),np.sin(np.arange(16)*2*np.pi/16)]
def hold(body,support,age,seconds):
    f=np.asarray([math.cos(body[2]),math.sin(body[2])]); l=np.asarray([-f[1],f[0]])
    robot=NORMALS@np.asarray(body[:2])-.63*abs(NORMALS@f)-.565*abs(NORMALS@l)
    return bool(np.max(robot-np.asarray(support)-.1-.08*(max(0.,age)+seconds+1.))>1e-8)

def audit_refuge(out):
    out=Path(out); saved=json.loads((out/'REFUGE_SUPERVISION.json').read_text())
    motion=json.loads(gzip.decompress((out/'MOTION_ENVELOPE.json.gz').read_bytes()))
    states={s['native_tick']:s for s in motion['states']}
    known=json.loads((out/'physics/SETUP.json').read_text())['known']
    with np.load(out/'physics/NATIVE_TRACE.npz') as z:
        native={round(float(t)*100):(q.copy(),v.copy()) for t,q,v in zip(z['time'],z['qpos'],z['qvel'])}
    requests=entries=stops=resumes=0; request=None; mode='ORIGINAL'; stop_scan=None
    for e in saved['events']:
        source=e['source']; s=states[source['source_native_tick']]
        assert source['source_scan_sim_time']==s['time'] and s['native_tick']<=e['native_tick'],'FUTURE_SOURCE'
        assert np.allclose(source['support_bounds'],s['support_bounds'],rtol=0,atol=1e-10),'SOURCE_CHANGED'
        q,v=native[e['native_tick']]; yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
        body=[q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]]
        assert np.allclose(body,e['body'],rtol=0,atol=1e-8),'EVENT_NOT_ACTUAL_STATE'
        support=s['support_bounds']; age=source['source_age_s']; kind=e['event']
        if kind=='REFUGE_REQUEST':
            assert mode=='ORIGINAL' and not hold(body,support,age,6.)
            for h in e['breadcrumbs']:
                assert h['native_tick']<=e['native_tick']
                if h['native_tick']:assert np.allclose(native[h['native_tick']][0][:2],h['body'][:2],rtol=0,atol=1e-8)
            chosen=choose_refuge(body,e['breadcrumbs'],support,age,known)
            assert chosen is not None and chosen['breadcrumb_native_tick']==e['selection']['breadcrumb_native_tick']
            assert np.allclose(chosen['goal'],e['selection']['goal'],rtol=0,atol=1e-10)
            assert np.allclose(chosen['reference_path'],e['selection']['reference_path'],rtol=0,atol=1e-10),'RETAINED_REFERENCE_NOT_ACTUAL_HISTORY'
            request=e; requests+=1; mode='REFUGE'
        elif kind=='REFUGE_SET_ENTERED':
            assert mode=='REFUGE' and 0<=age<=.2
            direction=np.asarray(request['selection']['goal'][:2])-request['body'][:2]
            progress=float((np.asarray(body[:2])-request['body'][:2])@direction/np.linalg.norm(direction))
            assert progress>=.75 and abs(progress-e['region']['projected_retreat_m'])<=1e-10 and hold(body,support,age,6.)
            assert np.allclose(e['start_body'],request['body'],rtol=0,atol=1e-10)
            mode='BRAKING'; entries+=1
        elif kind=='REFUGE_ACTION_REACHED':
            assert mode=='REFUGE' and hold(body,support,age,4.); mode='BRAKING'
        elif kind=='REFUGE_STOP_CONFIRMED':
            assert mode=='BRAKING' and 0<=e['brake_elapsed_s']<=2.
            assert np.linalg.norm(v[:2])<=.03 and abs(v[5])<=.03 and hold(body,support,age,4.),'NOT_ACTUALLY_STOPPED_IN_FINITE_REFUGE'
            mode='HOLD'; stops+=1; stop_scan=source['source_scan_sim_time']; stop_tick=e['native_tick']
        elif kind=='ORIGINAL_GOAL_RESUMED':
            assert mode=='HOLD' and hold(body,support,age,6.) and source['last_hit_time']>stop_scan
            assert e['native_tick']-stop_tick>=100,'NO_ACTUAL_HOLD_INTERVAL'
            mode='ORIGINAL'; resumes+=1
        else: raise AssertionError('UNRECOGNIZED_REFUGE_EVENT')
    route_count=0
    for row in json.loads((out/'ROUTER_REQUESTS.json').read_text()):
        if row.get('navigation_role')!='REFUGE' or not row.get('passed'):continue
        selection=row['terminal_region_choice']['selection']
        matches=[e for e in saved['events'] if e['event']=='REFUGE_REQUEST' and e['selection']==selection]
        assert len(matches)==1,'RETAINED_SELECTION_NOT_CAUSAL_REQUEST'
        q,v=native[row['source_body_native_tick']]
        yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
        actual_body=[q[0],q[1],yaw]
        verify_retained_row(row,selection,actual_body)
        route_count+=1
    result=dict(passed=not saved['actor_truth_used'] and requests<=3,causal_refuge_requests=requests,
                retained_route_provenance_checks=route_count,terminal_region_entries=entries,actual_stops=stops,resumes=resumes,total_events=len(saved['events']),
                terminal_mode=mode,models=0,integrations=0,
                scope='Saved actual pose/velocity, causal source, region admission and real braking; function independently evaluated')
    (out/'REFUGE_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n'); return result


def verify_retained_row(row,selection,actual_body):
    assert row['refuge_reference_kind']=='RETAINED_ACTUAL_HISTORY'
    assert np.allclose(row['original_start'],actual_body,rtol=0,atol=1e-8),'RETURNED_START_NOT_ACTUAL'
    expected,tracking=retained_suffix(actual_body,selection['reference_path'])
    assert np.asarray(expected).shape==np.asarray(row['refuge_returned_path']).shape and np.allclose(expected,row['refuge_returned_path'],rtol=0,atol=1e-8),'RETURNED_REFERENCE_CHANGED'
    assert tracking['nearest_history_index']==row['refuge_tracking']['nearest_history_index']
    assert abs(tracking['measured_reference_distance_m']-row['refuge_tracking']['measured_reference_distance_m'])<=1e-8,'TRACKING_DISTANCE_CHANGED'
    return True
