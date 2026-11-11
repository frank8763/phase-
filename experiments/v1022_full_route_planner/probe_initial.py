"""Complete known-static initial reference, before dynamic evidence; no authority."""
import importlib.abc,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';sys.path.insert(0,str(C));import full_route as m
route=sys.argv[1];pref=R/'runs/v858_nav2_verified/v1020/PREFLIGHTS'/route;p=json.loads((pref/'PREFLIGHT.json').read_text());known=json.loads((pref/'SETUP.json').read_text())['known'];task=next(t for t in json.loads((R/'experiments/v1020_terminal_two_route_development/TASKS.json').read_text())if t['route']==route)
# Isolated diagnostic reference construction, explicitly static and not a
# dynamic certificate. Avoid pretending a future actor observation existed at t0.
body=p['body'];q=p['steering'][:2];z=np.tan(q);delta=np.arctan(.6*np.mean([z[0]/(.6+.27*z[0]),z[1]/(.6-.27*z[1])]))
packet=dict(body=body,native_tick=0,sim_time=0.,body_measured_at=0.)
original=m.ref.snapshot_state;m.ref.snapshot_state=lambda *_:np.r_[body[:3],delta]
result=m.construct(packet,dict(source_native_tick=0,periodic=None),task['goal_xy'],known,time.time()+30.)
m.ref.snapshot_state=original;result.update(pre_detection_static_reference_only=True,physical_ready=False,models=0,integrations=0)
(O/(route+'_initial.static_geometry.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['path','state_path','edge_targets','heuristic']}))
