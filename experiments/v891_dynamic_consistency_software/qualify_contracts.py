"""Regression seams: set propagation/raster and real async proxy error semantics."""
import asyncio,copy,gzip,json,math,sys,tempfile,types
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v891_dynamic_consistency_software'
sys.path.insert(0,str(R/'experiments/v887_exact_lidar_software'))
from exact_lidar import get_lidar_features
from support_envelope import SupportEnvelope,NORMALS,polygon,raster_support
from reproduce import pose
from dynamic_proxy import DynamicPlannerProxy

def main():
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    saved=json.loads(gzip.decompress((O/'inputs/MOTION_ENVELOPE.json.gz').read_bytes()))['observations']
    tracker=SupportEnvelope(known,get_lidar_features)
    first=next(i for i,p in enumerate(saved)if p['time']>=54.06)
    for packet in saved[:first+1]:tracker.update(packet)
    checks={};old=tracker.support.copy();blank=copy.deepcopy(saved[first]);blank['time']+=1.;blank['native_tick']+=100;blank['ranges']=[3.]*32
    tracker.update(blank);checks['missing_returns_expand_never_erase']=np.allclose(tracker.support,old+.08,atol=1e-12)and tracker.last_hit<blank['time']
    b=tracker.forecast(blank['time']);p=polygon(b);grid=raster_support(b)
    rng=np.random.default_rng(891);n=10000;weights=rng.random((n,len(p)));weights/=weights.sum(axis=1,keepdims=True);points=weights@p
    cells=np.floor((points+5.)/.01).astype(int);checks['10000_forecast_points_cells_retained']=bool(np.all(grid[cells[:,1],cells[:,0]]==100))
    # Boundary vertices test the conservative cell/halfspace rounding seam.
    cells=np.floor((p+5.)/.01).astype(int);checks['all_polygon_vertex_cells_retained']=bool(np.all(grid[cells[:,1],cells[:,0]]==100))
    clean=saved[0];truth=dict(clean,actor_xy=[999,999],raw_lidar=[-999]*32)
    a=SupportEnvelope(known,get_lidar_features);c=SupportEnvelope(known,get_lidar_features)
    checks['actor_raw_metadata_cannot_change_policy']=a.update(clean)==c.update(truth)
    negative=[]
    for label,mutate in [('nan_range',lambda p:p['ranges'].__setitem__(0,float('nan'))),('negative_range',lambda p:p['ranges'].__setitem__(0,-.1)),('missing_pose',lambda p:p.pop('xy')),('infinite_pose',lambda p:p['xy'].__setitem__(0,float('inf'))),('wrong_count',lambda p:p.update(ranges=[3.]*31))]:
        sample=copy.deepcopy(clean);mutate(sample)
        try:SupportEnvelope(known,get_lidar_features).update(sample);negative.append(False)
        except (ValueError,KeyError):negative.append(True)
        checks['reject_'+label]=negative[-1]
    try:a.update(clean);checks['reject_duplicate_time']=False
    except ValueError:checks['reject_duplicate_time']=True
    cfg=json.loads((R/'experiments/v892_dynamic_terminal_consistency/A_motion.yaml').read_text())
    vertices=json.loads(cfg['global_costmap']['global_costmap']['ros__parameters']['footprint'])
    support=json.loads((O/'SUPPORT_QUALIFICATION.json').read_text())['final_support']
    geometry=types.ModuleType('geometry_msgs');msg=types.ModuleType('geometry_msgs.msg');msg.PoseStamped=lambda:None;geometry.msg=msg
    sys.modules['geometry_msgs']=geometry;sys.modules['geometry_msgs.msg']=msg
    class Kind:
        class Result:
            error_code=0
        class Goal:pass
    class Handle:
        request=types.SimpleNamespace(goal=pose(4.,-2.),use_start=True,start=pose(.839734655392,-.819643845742,-.21558848),planner_id='GridBased')
        def abort(self):self.aborted=True
    class Client:
        def server_is_ready(self):return True
        async def send_goal_async(self,request):return self
        accepted=True
        async def get_result_async(self):return types.SimpleNamespace(status=6,result=types.SimpleNamespace(error_code=205))
    import time
    for forward in [False,True]:
        proxy=DynamicPlannerProxy.__new__(DynamicPlannerProxy);proxy.use_new=True;proxy.kind=Kind;proxy.rows=[];proxy.known=known;proxy.configured_footprint=vertices;proxy.force_forward=forward;proxy.latest=lambda:dict(sent_at=time.monotonic());proxy.deadline=time.time()+60;proxy.client=Client();proxy.out=O
        proxy.forecast=lambda:(polygon(support),dict(fixed_software_case=True))
        result=asyncio.run(proxy.execute(Handle()))
        checks['virtual_root205_wait208'if not forward else'actual_vehicle_root205_preserved']=result.error_code==(205 if forward else 208)
    result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,navigation=0,scope='Real support/raster/async proxy call sites under explicit fake ROS action dependencies; genuine installed Smac covered separately')
    (O/'CONTRACT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
if __name__=='__main__':main()
