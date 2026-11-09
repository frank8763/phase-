"""Pure goal-region containment and deterministic choice checks."""
import copy,json,math,sys
from pathlib import Path
from types import SimpleNamespace as NS
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v927_terminal_region_qualification'
sys.path[:0]=[str(C),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v864_diagnosis')]
from reference_terminal import terminal_goal,OFFSETS,ENDPOINT_RADIUS
known=json.load(open(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'));goal=NS(pose=NS(position=NS(x=4.,y=-2.),orientation=NS(z=0.,w=1.)))
a,p=terminal_goal(goal,known,None,None);b,p2=terminal_goal(goal,known,None,None)
def contained(shift,tolerance,radius):return math.isfinite(shift)and math.isfinite(tolerance)and 0<=shift and 0<=tolerance and shift+tolerance<=radius
checks=dict(all17_fixed_choices_contained=all(contained(math.hypot(x,y),.2,.45)for x,y in OFFSETS),exact_candidate_count=len(OFFSETS)==17,original_goal_not_mutated=goal.pose.position.x==4. and goal.pose.position.y==-2.,deterministic=p==p2,chosen_endpoint_within_bound=contained(math.hypot(a.pose.position.x-4,a.pose.position.y+2),.2,.45),worst_boundary_negative=not contained(.251,.2,.45),nan_negative=not contained(float('nan'),.2,.45),selected_static_clearance_over_global_margin=p['public_static_clearance_m']>.27)
r=dict(passed=all(checks.values()),checks=checks,selected=p,models=0,integrations=0);(O/'GOAL_REGION_QUALIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
