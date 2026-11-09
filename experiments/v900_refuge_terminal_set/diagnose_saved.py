"""One immutable failed trajectory, no physics import: cause probes and predicate tests."""
import gzip, hashlib, json, math, sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v900_refuge_terminal_set'
sys.path.insert(0,str(C))
from terminal_set import membership
def main():
    p=R/'runs/v858_nav2_verified/v897/main_we'
    sources=['ROUTER_REQUESTS.json','REFUGE_SUPERVISION.json','MOTION_ENVELOPE.json.gz','physics/NATIVE_TRACE.npz','INDEPENDENT_AUDIT.json','COMMANDS.json']
    sha={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in sources}
    old=json.loads((p/'INDEPENDENT_AUDIT.json').read_text());assert old['functional_passed'] is False
    requests=[r for r in json.loads((p/'ROUTER_REQUESTS.json').read_text()) if r.get('navigation_role')=='REFUGE']
    gears=[]
    for i,r in enumerate(requests):
        a=np.array(r['refuge_returned_path']);delta=np.diff(a[:,:2],axis=0)
        signed=np.einsum('ij,ij->i',delta,np.c_[np.cos(a[:-1,2]),np.sin(a[:-1,2])])
        gears.append(dict(index=i,elapsed_s=r['started_monotonic']-requests[0]['started_monotonic'],starts_forward=bool(signed[0]>0),forward_segments=int(sum(signed>1e-5)),reverse_segments=int(sum(signed< -1e-5))))
    event=json.loads((p/'REFUGE_SUPERVISION.json').read_text())['events'][0]
    states=json.loads(gzip.decompress((p/'MOTION_ENVELOPE.json.gz').read_bytes()))['states']
    first=None
    with np.load(p/'physics/NATIVE_TRACE.npz') as z:
        for s in states:
            if s['native_tick']<=event['native_tick']:continue
            q=z['qpos'][s['native_tick']-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));b=[q[0],q[1],yaw]
            proof=membership(b,event['body'],event['selection']['goal'],s['support_bounds'],.1)
            if proof['passed']:
                first=dict(native_tick=s['native_tick'],sim_s=s['time'],body=b,support=s['support_bounds'],region=proof,old_point_distance_m=float(np.linalg.norm(q[:2]-event['selection']['goal'][:2])))
                break
    assert first and first['old_point_distance_m']>.2
    b=first['body'];start=event['body'];g=event['selection']['goal'];support=first['support']
    checks={'saved_functional_failure_preserved':True,'real_saved_region_admitted_without_point_arrival':first is not None,
            'zero_retreat_rejected':not membership(start,start,g,support,.1)['passed'],
            'stale_source_rejected':not membership(b,start,g,support,.201)['passed'],
            'missing_source_rejected':not membership(b,start,g,None,.1)['passed'],
            'unsafe_hold_rejected':not membership(b,start,g,np.ones(16)*100,.1)['passed'],
            'nonfinite_rejected':not membership([float('nan'),0,0],start,g,support,.1)['passed'],
            'sideways_motion_rejected':not membership([start[0]+.8*(g[1]-start[1]),start[1]-.8*(g[0]-start[0]),0],start,g,support,.1)['passed']}
    result=dict(passed=all(checks.values()),checks=checks,source_sha256=sha,model_initializations=0,integrations=0,
                first_saved_terminal_region=first,path_direction_probe=gears,
                conclusion='Old execution already entered a causally admissible region; point-target completion remained false and later replans start forward. Counterfactual arrival is not established without a new actual run.')
    (O/'SAVED_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],first_sim_s=first['sim_s'],point_distance_m=first['old_point_distance_m'],checks=checks)),flush=True)
    return 0 if result['passed'] else 1
if __name__=='__main__':sys.exit(main())
