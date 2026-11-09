"""Saved real failure -> actual production action callback, zero ROS/model steps."""
import asyncio, copy, importlib.abc, json, sys, time, types
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v905_reference_execution_separation'
sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname.split('.')[0] in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN')
sys.meta_path.insert(0,NoModel())
from refuge_logic import choose_refuge,retained_suffix,exit_path_ok
sys.path.insert(0,str(C))
from refuge_audit import verify_retained_row
sys.path.insert(0,str(C))
import dynamic_proxy
assert Path(dynamic_proxy.__file__).parent==C
from dynamic_proxy import DynamicPlannerProxy
def pose(x=0.,y=0.,a=0.):
    import math
    return types.SimpleNamespace(header=types.SimpleNamespace(frame_id='map'),pose=types.SimpleNamespace(position=types.SimpleNamespace(x=x,y=y),orientation=types.SimpleNamespace(x=0.,y=0.,z=math.sin(a/2),w=math.cos(a/2))))
sys.modules['geometry_msgs.msg']=types.SimpleNamespace(PoseStamped=pose)
sys.modules['nav_msgs.msg']=types.SimpleNamespace(Path=lambda:types.SimpleNamespace(header=None,poses=[]))
checks={};witnesses=[]
def invoke(e,p,known,selection,label):
    proxy=DynamicPlannerProxy.__new__(DynamicPlannerProxy)
    proxy.use_new=True;proxy.refuge_mode=True;proxy.refuge_selection=selection;proxy.known=known
    proxy.configured_footprint=[[-.63,-.565],[.63,-.565],[.63,.565],[-.63,.565]]
    source=copy.deepcopy(p['causal_forecast_source'])
    proxy.forecast=lambda:(None,source)
    proxy.latest=lambda:dict(body=p['original_start']+[0.,0.],sent_at=time.monotonic(),native_tick=e['native_tick'])
    proxy.deadline=time.time()+120
    proxy.kind=types.SimpleNamespace(Result=lambda:types.SimpleNamespace(error_code=None,path=None))
    published=[];proxy.publisher=types.SimpleNamespace(publish=published.append)
    proxy.rows=[];proxy.out=O/('qualification_'+label);proxy.out.mkdir(exist_ok=True)
    status=[]
    handle=types.SimpleNamespace(request=types.SimpleNamespace(goal=pose(*selection['goal']),use_start=False),abort=lambda:status.append('ABORT'),succeed=lambda:status.append('SUCCEED'))
    result=asyncio.run(proxy.execute(handle))
    return result,status,proxy.rows[-1]
for version in ['v897','v901']:
    out=R/'runs/v858_nav2_verified'/version/'main_we'
    e=next(x for x in json.loads((out/'REFUGE_SUPERVISION.json').read_text())['events']if x['event']=='REFUGE_REQUEST')
    p=next(x for x in json.loads((out/'ROUTER_REQUESTS.json').read_text())if x.get('navigation_role')=='REFUGE')
    known=json.loads((out/'physics/SETUP.json').read_text())['known']
    selected=choose_refuge(e['body'],e['breadcrumbs'],e['source']['support_bounds'],e['source']['source_age_s'],known)
    checks[version+'_actual_history_selected']=selected is not None
    result,status,row=invoke(e,p,known,selected,version)
    checks[version+'_production_returned_exact_retained_route']=status==['SUCCEED'] and row['passed'] and len(result.path.poses)==len(row['refuge_returned_path'])
    checks[version+'_independent_provenance']=verify_retained_row(row,selected,p['original_start'])
    for key in ['original_start','refuge_returned_path']:
        changed=copy.deepcopy(row)
        if key=='original_start':changed[key][0]+=.1
        else:changed[key][1][0]+=.1
        try:verify_retained_row(changed,selected,p['original_start'])
        except AssertionError:checks[version+'_reject_'+key]=True
        else:checks[version+'_reject_'+key]=False
    badp=copy.deepcopy(p);badp['original_start'][1]-=1.
    _,badstatus,badrow=invoke(e,badp,known,selected,version+'_off_path')
    checks[version+'_production_reject_actual_tracking_error']=badstatus==['ABORT'] and 'TRACKING_MARGIN' in badrow.get('error','')
    stale=copy.deepcopy(p);stale['causal_forecast_source']['source_age_s']=100.
    _,badstatus,badrow=invoke(e,stale,known,selected,version+'_old_observation')
    checks[version+'_production_reject_unbounded_prediction']=badstatus==['ABORT'] and not badrow['refuge_path_contract']['passed']
    witnesses.append(dict(source=version,old_smac_contract=p['refuge_path_contract'],retained_contract=row['refuge_path_contract'],same_actual_body=p['original_start'],models=0))
checks['v901_reproduces_original_rejection']=witnesses[1]['old_smac_contract']['passed'] is False
receipt=dict(passed=all(checks.values()),checks=checks,witnesses=witnesses,models=0,integrations=0,scope='Production route callback with saved actual poses/history/causal scans and message stubs. No new physical performance or closed-loop success claim.')
(O/'RETAINED_QUALIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
assert receipt['passed']
