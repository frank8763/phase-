"""Independent causal and actual-native audit of new recovery references."""
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'experiments/v938_rpccr_recovery_segments'),
               str(ROOT/'experiments/v934_rpccr_certified_recovery')]
from independent_geometry import audit as geometry_audit
from periodic_support import PeriodicSupport


def body_rows(trace):
    q, v = trace['qpos'], trace['qvel']
    yaw = np.arctan2(2*(q[:, 3]*q[:, 6]+q[:, 4]*q[:, 5]),
                     1-2*(q[:, 5]**2+q[:, 6]**2))
    return np.c_[q[:, :2], yaw, v[:, 0]*np.cos(yaw)+v[:, 1]*np.sin(yaw), v[:, 5]]


def check_source(packet, source, recorded, states, priors):
    tick = packet['native_tick']
    assert 1 <= tick <= len(recorded), 'UNRECORDED_RECOVERY_BODY'
    assert np.max(abs(np.asarray(packet['body'])-recorded[tick-1])) <= 1e-8, 'RECOVERY_BODY_NOT_ACTUAL'
    stamp = source['source_native_tick']
    assert stamp <= tick and stamp in states, 'NONCAUSAL_RECOVERY_SOURCE'
    assert source['support_bounds'] == states[stamp]['support_bounds'], 'RECOVERY_SUPPORT_NOT_ORIGINAL'
    expected = priors[stamp]
    actual = source['periodic']
    assert expected is not None and actual is not None
    assert all(actual[k] == expected[k] for k in ['source_tick', 'omega', 'amplitude', 'last']), 'RECOVERY_PERIODIC_METADATA'
    assert all(np.asarray(a).shape == np.asarray(b).shape and
               np.allclose(a, b, rtol=0., atol=1e-9)
               for a,b in zip(actual['vertices'], expected['vertices'])), 'RECOVERY_PERIODIC_NOT_CAUSAL'
    assert 0 <= source['source_age_s'] <= .2


def tracking(path, actual):
    # Independent exact circular interpolation, no online search/admission import.
    dense = [np.asarray(path[0])]
    for aa, bb in zip(path, path[1:]):
        a,b = np.asarray(aa),np.asarray(bb)
        direction = 1 if (b[:2]-a[:2]) @ [math.cos(a[2]),math.sin(a[2])] >= 0 else -1
        turn = math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]))
        k = turn/(direction*.1)
        s = np.arange(1,201)*.0005*direction
        angle = a[2]+k*s
        if abs(k)<1e-10:
            x=a[0]+s*math.cos(a[2]);y=a[1]+s*math.sin(a[2])
        else:
            x=a[0]+(np.sin(angle)-math.sin(a[2]))/k
            y=a[1]-(np.cos(angle)-math.cos(a[2]))/k
        dense.extend(np.c_[x,y,angle])
    reference=np.asarray(dense);distance=0.;heading=0.
    for start in range(0,len(actual),128):
        block=actual[start:start+128]
        d=np.linalg.norm(block[:,None,:2]-reference[None,:,:2],axis=2)
        index=np.argmin(d,axis=1)
        distance=max(distance,float(d[np.arange(len(block)),index].max()))
        delta=block[:,2]-reference[index,2]
        heading=max(heading,float(abs(np.arctan2(np.sin(delta),np.cos(delta))).max()))
    return dict(passed=distance<=.04 and heading+.758770385*.00025<=.035,
                maximum_reference_position_error_m=distance,
                maximum_reference_heading_error_rad=heading,
                heading_sampling_allowance_rad=.758770385*.00025,
                actual_native_samples=len(actual))


def audit(out):
    out=Path(out)
    rows=json.loads((out/'RECOVERY_CORRIDORS.json').read_text())
    journal=json.loads(gzip.decompress((out/'MOTION_ENVELOPE.json.gz').read_bytes()))
    states={r['native_tick']:r for r in journal['states']}
    priors={};periodic=PeriodicSupport()
    for row in journal['states']:
        periodic.update(row['time'],row['native_tick'],row['support_bounds'])
        priors[row['native_tick']]=None if periodic.last is None else periodic.snapshot()
    setup=json.loads((out/'physics/SETUP.json').read_text())
    task=json.loads((out/'TASK.json').read_text())
    with np.load(out/'physics/NATIVE_TRACE.npz') as trace:
        recorded=body_rows(trace);vel=trace['qvel'].copy()
    goal=np.asarray(task['goal_xy']);completed=0;reports=[]
    for row in rows:
        for prefix in ['entry','search','install','end']:
            if prefix+'_packet' in row:
                check_source(row[prefix+'_packet'],row[prefix+'_source'],recorded,states,priors)
        trigger=row['trigger']['trigger'];entry=row['entry_packet']
        assert trigger['body_native_tick']==entry['native_tick']
        assert trigger['failed_reference_count']>=3 and trigger['observed_stall_s']>=1.5-1e-8
        assert trigger['observed_motion_m']<.02 and max(abs(entry['body'][3]),abs(entry['body'][4]))<=.03
        proposal=row.get('proposal');proof=None
        if proposal and proposal['passed']:
            assert proposal['status']=='RECOVERY_SEGMENT' and proposal['original_goal']==task['goal_xy']
            proof=geometry_audit(proposal['path'],setup['known'],row['search_source']['periodic'])
            assert proof['passed'],'UNQUALIFIED_SEARCH_CORRIDOR'
            assert np.max(abs(np.asarray(proposal['path'][0])-row['search_packet']['body'][:3]))<=1e-8
        actual=None
        if row['passed']:
            assert proposal and proof['passed']
            installed=geometry_audit(proposal['path'],setup['known'],row['install_source']['periodic'])
            assert installed['passed'],'CURRENT_CAUSAL_CORRIDOR_REVALIDATION_FAILED'
            assert row['install_effect']['path']==proposal['path']
            assert row['follow_result_status']==4 and row['renewal']['goal']==task['goal_xy']
            events=[e['action'] for e in row['transaction_events']]
            assert events[:3]==['CANCEL_NORMAL_NAVIGATION','WAIT_FRESH_STOPPED_BODY','SEND_FOLLOW_PATH_ONCE']
            assert events.count('SEND_FOLLOW_PATH_ONCE')==1 and events[-1]=='PLAN_TO_ORIGINAL_GOAL'
            start=row['install_packet']['native_tick'];end=row['end_packet']['native_tick']
            assert end>start
            endbody=recorded[end-1]
            progress=float(np.linalg.norm(np.asarray(entry['body'][:2])-goal)-np.linalg.norm(endbody[:2]-goal))
            assert progress>=.4 and np.linalg.norm(endbody[:2]-proposal['path'][-1][:2])<=.2
            assert np.linalg.norm(vel[end-1,:2])<=.03
            actual=tracking(proposal['path'],recorded[start-1:end])
            assert actual['passed'],'ACTUAL_REFERENCE_TRACKING_ENVELOPE_FAILED'
            completed+=1
        reports.append(dict(entry_tick=entry['native_tick'],completed=bool(row['passed']),
                            independent_geometry=proof,actual_tracking=actual))
    result=dict(passed=True,evidence_passed=True,completed_certified_segments=completed,
                attempted_recovery_segments=len(rows),segments=reports,models=0,integrations=0,
                functionally_exercised=completed>=1,
                scope='Saved causal reference, independent whole-body geometry, exact native body and measured segment execution; no private model.')
    (out/'CORRIDOR_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
