"""Rebase nominal control seed onto the actual safely stopped configuration.

The failed component stopped 145 moving ticks before its intended cut. Its
original cut12500 cannot be assumed executed. Projection is seed selection
only; full dynamics/geometry and every backup remain mandatory.
"""
from goal_probe import *

if __name__=='__main__':
    p=json.loads((R/'runs/v1145_observer_failure_review/SAVED_STOP_PACKET.json').read_text())
    nominal=np.load(R/'runs/v1136_route_clock_restore/dynamic_seed_v120/SELECTED_SOURCE.npz')['states']
    candidates=np.arange(11000,12501)
    yaw=np.arctan2(np.sin(nominal[candidates,2]-p['body'][2]),np.cos(nominal[candidates,2]-p['body'][2]))
    costs=np.linalg.norm(nominal[candidates,:2]-p['body'][:2],axis=1)**2+(.3*yaw)**2
    index=int(candidates[np.argmin(costs)])
    dump(O/'GOAL_REBASE_SELECTION.json',dict(selected_nominal_tick=index,actual_saved_tick=34715,old_assumed_nominal_tick=12500,projection_seed_only=True,no_actual_pose_rewrite=True,selection_cost=float(costs.min())))
    main('goal_rebased',index)
