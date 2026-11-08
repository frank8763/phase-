"""Pin query symmetry, endpoint choice and fail-closed static geometry before ROS."""
import copy,hashlib,json,math,time
from pathlib import Path
from types import SimpleNamespace as N
from planner_proxy import flip,restore,request_direction,path_guard,yaw
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v873_unsmoothed_qualification'
def pose(x,y,a):return N(pose=N(position=N(x=x,y=y),orientation=N(z=math.sin(a/2),w=math.cos(a/2))))
def main():
 assert not(O/'ZERO_QUALIFICATION.json').exists();known=json.load(open(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'));cases=json.load(open(R/'experiments/v855_renewal_worker/SCENE_CASES.json'));rows=[]
 for case in cases:
  a=pose(*case['start_xy'],case['yaw']);b=pose(*case['goal_xy'],case['yaw']);reverse,clear=request_direction(a,b,known);assert reverse==(case['id']=='WEST_EAST');z=restore(N(poses=[flip(b),flip(a)]),True);assert abs(math.atan2(math.sin(yaw(z.poses[0])-yaw(a)),math.cos(yaw(z.poses[0])-yaw(a))))<1e-12;assert z.poses[0].pose.position.x==a.pose.position.x;rows.append(dict(case=case['id'],reverse=reverse,endpoint_full_bound_clearances_m=clear))
 rejected=False
 try:path_guard(N(poses=[pose(0,3.25,0),pose(.1,3.25,0)]),pose(0,3.25,0),pose(.1,3.25,0),known)
 except AssertionError:rejected=True
 assert rejected
 stack=(C/'routing_stack.py').read_text();proxy=(C/'planner_proxy.py').read_text();assert 'plan:=smac_search_plan' in stack and 'self.publisher.publish(result.path)' in proxy
 q=dict(passed=True,models=0,integrations=0,actuator_execution=0,endpoint_choices=rows,pi_restoration_max_error=1e-12,obstacle_path_rejected=True,scope='Pure interface/known geometry only; not a physical model check');(O/'ZERO_QUALIFICATION.json').write_text(json.dumps(q,indent=2)+'\n')
 fixtures=json.load(open(R/'runs/v869_geometry_software/FIXTURES.json'));fixtures={k:fixtures[k]for k in ['fine_we','fine_ns','fine_ew','fine_ns_checkpoint']};(O/'FIXTURES.json').write_text(json.dumps(fixtures,indent=2)+'\n');files=dict(json.load(open(R/'experiments/v867_margin_navigation/SOURCE_FREEZE.json'))['files'])
 for p in [*C.iterdir(),O/'FIXTURES.json',O/'ZERO_QUALIFICATION.json']:
  if p.is_file()and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 (C/'SOURCE_FREEZE.json').write_text(json.dumps(dict(models_authorized=False,files=files),indent=2)+'\n');now=time.time();(O/'SOFTWARE_WINDOW.json').write_text(json.dumps(dict(started_unix=now,deadline_unix=now+600,models_authorized=False,maximum_probes=4,task_names=list(fixtures)),indent=2)+'\n');print(json.dumps(q))
if __name__=='__main__':main()
