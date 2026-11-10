"""Actual saved t0 bodies and public map: reject uncertifiable initial STOP."""
import importlib.util,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1020_terminal_two_route_development';sys.path.insert(0,str(C))
from command_tube import admit
rows=[]
for route,version,wanted in [('we','v1020',True),('ns','v1020',True),('ew','v1018',False)]:
 out=R/'runs/v858_nav2_verified'/version/'PREFLIGHTS'/route
 p=json.loads((out/'PREFLIGHT.json').read_text());setup=json.loads((out/'SETUP.json').read_text());enc=p['steering']
 packet=dict(body=p['body'],native_tick=0,sim_time=0.,body_measured_at=0.,sent_at=0.,steering=dict(position=enc[:2],velocity=enc[2:],native_tick=0,measured_at=0.))
 source=dict(source_native_tick=0,source_age_s=.001,decision_at=.05,support_bounds=None,periodic=None)
 proof=admit(packet,source,0.,0.,setup['known'],.05);assert proof['passed']is wanted,(route,proof)
 rows.append(dict(route=route,passed=proof['passed'],static_lower_m=proof['static_lower_m'],threshold_m=.155,models=0))
result=dict(passed=True,models=0,integrations=0,legal_registered_routes=['we','ns'],unqualified_EW_not_launched=True,rows=rows)
(O/'INITIAL_ZERO_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
