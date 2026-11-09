"""Zero-model readiness gate, not an executable navigation or safety certificate.

Reject nominal target choices incompatible with the unchanged supervisor. Search
only the original bounded .24m terminal region; a witness still needs real Smac,
actuator-safe tracking and independent closed-loop tests before model launch.
"""
import math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v907_recovery_corridor_memory'))
from refuge_logic import wait_ok
from snapshot_geometry import field
from exact_footprint import pose_values
OFFSETS=[(0.,0.)]+[(r*math.cos(a),r*math.sin(a))for r in [.08,.16,.24]for a in np.arange(16)*2*math.pi/16]

def terminal_witness(goal,known,snapshot):
    packet,source=snapshot
    assert source['source_native_tick']<=packet['native_tick'],'FUTURE_TERMINAL_SOURCE'
    age=source['source_age_s']
    assert 0.<=age<=.2,'STALE_TERMINAL_SOURCE'
    assert source['support_bounds']is not None,'UNTRACKED_DIAGNOSIS'
    poses=[[goal[0]+dx,goal[1]+dy,goal[2]]for dx,dy in OFFSETS]
    static=pose_values(field(known),poses);rows=[]
    for i,(p,c)in enumerate(zip(poses,static)):
        rows.append(dict(index=i,pose=p,static_margin_m=float(c),hold6=wait_ok(p,source['support_bounds'],age,6.),static_ok=float(c)>=.155))
    allowed=[r for r in rows if r['static_ok']and r['hold6']]
    selected=min(allowed,key=lambda r:math.hypot(r['pose'][0]-goal[0],r['pose'][1]-goal[1]))if allowed else None
    return dict(admitted=selected is not None,selected=selected,candidates=rows,source_native_tick=source['source_native_tick'],body_native_tick=packet['native_tick'],endpoint_radius_m=.24,controller_tolerance_m=.2,total_goal_budget_m=.44,
                reason='FINITE_TERMINAL_WITNESS_ONLY'if selected else'NO_COMMON_TERMINAL_WITNESS',executable_route_proven=False,vehicle_models=0)
