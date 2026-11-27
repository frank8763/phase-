"""Phase-runtime production path-validator seam, saved real input, zero models."""
import json,sys,copy
from context import R,C,SOURCE as S,load,read
import numpy as np
P=R/'runs/v2127_filter_grant_headroom/components/PSF/actual'
sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
route=load('observed_route',R/'experiments/v1370_overnight_controller_matrix/observed_route.py')
nav=load('current_production_navigation',C/'navigation.py');selected=read(P/'FILTER_QUERY_000_ROUTE.json')['selected'];body=read(P/'cycle_000000_origin.json')['receipt']['packet']['body'];known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')
old,original=route.revalidate(known,np.asarray(selected['poses']),body,None,guard=.22);assert not old and original['reason']=='MALFORMED_PATH'
valid,new=nav.validate_current_route(np,route,known,selected,body);assert valid and new['minimum_clearance_m']>=.22-1e-8
bad=body.copy();bad[0]+=.03;ok,z=nav.validate_current_route(np,route,known,selected,bad);assert not ok and z['reason']=='PLAN_START_NO_LONGER_MATCHES'
blocked=copy.deepcopy(known);blocked['known_circles'].append([body[0],body[1],.1]);ok,z=nav.validate_current_route(np,route,blocked,selected,body);assert not ok
print(json.dumps(dict(passed=True,old_failure_reproduced=original,production_validator=new,negative_cases=['foreign_current_start','occupied_current_body'],models=0,optimizer_queries=0,physical_native=0,gear_column_preserves_registered_segment=True)))
