"""Actual old selector plus saved final forecast and installed full footprint."""
import json,math,sys
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v881_timing_accounting_continuation'))
from planner_proxy import terminal_goal
def pose(x,y,a=0.):return S(pose=S(position=S(x=x,y=y),orientation=S(z=math.sin(a/2),w=math.cos(a/2))))
def intersects(a,b):
    for p in [a,b]:
        edges=np.roll(p,-1,axis=0)-p
        for n in np.c_[-edges[:,1],edges[:,0]]:
            x=a@n;y=b@n
            if x.max()<y.min()-1e-10 or y.max()<x.min()-1e-10:return False
    return True
def footprint(p,vertices):
    a=2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)
    c,s=math.cos(a),math.sin(a)
    return np.asarray(vertices)@np.asarray([[c,s],[-s,c]])+[p.pose.position.x,p.pose.position.y]
def main():
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    failure=json.loads((R/'records/nav2_v890_20261108/FAILURE_ANALYSIS.json').read_text())
    cfg=json.loads((R/'experiments/v890_motion_envelope_dynamic/A_motion.yaml').read_text())
    vertices=json.loads(cfg['global_costmap']['global_costmap']['ros__parameters']['footprint'])
    goal,choice=terminal_goal(pose(4.,-2.),known)
    x0,y0,x1,y1=failure['last_published_envelope']['rectangle']
    rect=np.asarray([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])
    occupied=intersects(footprint(goal,vertices),rect)
    proof=dict(old_static_selector_chooses_forecast_occupied_terminal=occupied,selected=choice,reverse_search_root_is_this_terminal=True,models=0,integrations=0)
    O=R/'runs/v891_dynamic_consistency_software';O.mkdir(exist_ok=True)
    (O/'REPRODUCTION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof));assert occupied,'ORIGINAL_FAILURE_NOT_REPRODUCED'
    if '--require-free' in sys.argv:assert not occupied,'TERMINAL_FORECAST_OCCUPIED: original exact bug reproduced'
if __name__=='__main__':main()
