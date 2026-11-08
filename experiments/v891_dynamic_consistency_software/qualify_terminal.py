"""Old failure seam and fixed region selector; no model or ROS required."""
import json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v891_dynamic_consistency_software'
from reproduce import pose,footprint,intersects
from terminal_region import terminal_goal,ENDPOINT_RADIUS,CONTROLLER_TOLERANCE
from support_envelope import polygon

def main():
    cfg=json.loads((R/'experiments/v890_motion_envelope_dynamic/A_motion.yaml').read_text())
    vertices=json.loads(cfg['global_costmap']['global_costmap']['ros__parameters']['footprint'])
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    failure=json.loads((R/'records/nav2_v890_20261108/FAILURE_ANALYSIS.json').read_text())
    x0,y0,x1,y1=failure['last_published_envelope']['rectangle'];old=np.asarray([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])
    support=json.loads((O/'SUPPORT_QUALIFICATION.json').read_text())
    checks={};rows={}
    for name,poly in [('old_rectangle',old),('new_support_polygon',polygon(support['final_support'])),('no_dynamic',None),('all_blocked',np.asarray([[-5.,-5.],[5.,-5.],[5.,5.],[-5.,5.]]))]:
        goal,proof=terminal_goal(pose(4.,-2.),known,poly,vertices);rows[name]=proof
        checks[name+'_expected_admissibility']=(goal is None)if name=='all_blocked'else(goal is not None)
        if goal is not None:
            checks[name+'_goal_region_bound']=proof['displacement_m']+CONTROLLER_TOLERANCE<.45
            checks[name+'_whole_padded_footprint_clear']=poly is None or not intersects(footprint(goal,vertices),poly)
    result=dict(passed=all(checks.values()),checks=checks,cases=rows,models=0,integrations=0,scope='Full configured padded footprint versus dynamic forecast and original static lower bound; actual Smac route and physical arrival unvalidated')
    (O/'TERMINAL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,selected={k:v.get('selected_xy',v['reason'])for k,v in rows.items()})))
    assert result['passed']
if __name__=='__main__':main()
