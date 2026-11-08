"""Original recorded stopped-pose seam and synthetic geometry boundary cases."""
import json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v895_wait_viability_software';REC=R/'records/nav2_v895_20261108'
sys.path[:0]=[str(R/'experiments/v891_dynamic_consistency_software')]
from stationary_certificate import stationary_wait_certificate
from support_envelope import NORMALS
from reproduce import pose,footprint
def main():
    source=json.loads((R/'records/nav2_v894_20261108/STOPPED_ACTOR_ANALYSIS.json').read_text())
    cfg=json.loads((R/'experiments/v894_wait_map_validation/A_motion.yaml').read_text())
    vertices=json.loads(cfg['local_costmap']['local_costmap']['ros__parameters']['footprint']);rows=[]
    for row in source['wait_pose_geometry_witnesses']:
        b=np.asarray(row['causal_center_support'])
        body=footprint(pose(*row['vehicle_xy'],row['yaw']),vertices)
        proof=stationary_wait_certificate(body,b,row['source_age_s'],1.5,1.)
        rows.append(dict(sim_time=row['sim_time'],actual_measured_speed_m_s=row['actual_speed_m_s'],certificate=proof))
    checks={};last=next(x for x in rows if abs(x['sim_time']-126.)<.02)
    checks['original126s_almost_stopped_wait_rejected']=last['actual_measured_speed_m_s']<=.03 and not last['certificate']['passed']
    checks['original100s_fixed_pose_finite_geometry_positive']=next(x for x in rows if abs(x['sim_time']-100.)<.02)['certificate']['passed']
    square=np.asarray([[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]])
    actor=np.asarray([[1.,-.05],[1.1,-.05],[1.1,.05],[1.,.05]]);bounds=np.max(NORMALS@actor.T,axis=1)
    results=[stationary_wait_certificate(square,bounds,0.,h,0.)['passed']for h in [0.,1.,2.,4.,8.]]
    checks['longer_wait_never_revives_failed_fixed_pose']=all(not results[i]or all(results[:i])for i in range(len(results)))
    checks['short_wait_clear_long_wait_rejected']=results[0]and not results[-1]
    contact=np.max(NORMALS@np.asarray([[.6,0.]]).T,axis=1)
    checks['forecast_boundary_contact_rejected']=not stationary_wait_certificate(square,contact,0.,0.,0.)['passed']
    for name,args in [('negative_wait',(square,bounds,0.,-1.,0.)),('nan_age',(square,bounds,float('nan'),1.,0.)),('wrong_support',(square,bounds[:8],0.,1.,0.))]:
        try:stationary_wait_certificate(*args);checks['reject_'+name]=False
        except ValueError:checks['reject_'+name]=True
    result=dict(passed=all(checks.values()),checks=checks,saved_cases=rows,models=0,integrations=0,commands=0,vehicle_policy_implemented=False,scope='Fixed-pose finite geometric component only; executable braking/exit/observation-renewal controller remains unimplemented')
    O.mkdir(exist_ok=True);REC.mkdir(exist_ok=True)
    for p in [O/'QUALIFICATION.json',REC/'QUALIFICATION.json']:p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks)),flush=True);assert result['passed']
if __name__=='__main__':main()
