"""Choose the tighter static endpoint as Smac's search root; retain original task direction."""
import copy,json,math,time,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v864_diagnosis'),str(R/'experiments/v791_coherent_global_reference')]
from snapshot_geometry import field,dense
from exact_footprint import pose_values

def yaw(p):return 2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)
def flip(p):
 p=copy.deepcopy(p);a=yaw(p)+math.pi;p.pose.orientation.z=math.sin(a/2);p.pose.orientation.w=math.cos(a/2);return p

def restore(path,reverse):
 result=copy.deepcopy(path)
 if reverse:result.poses=[flip(p)for p in reversed(result.poses)]
 return result

def request_direction(start,goal,known):
 f=field(known);separation=pose_values(f,[[start.pose.position.x,start.pose.position.y,yaw(start)],[goal.pose.position.x,goal.pose.position.y,yaw(goal)]])
 return bool(separation[1]<separation[0]-1e-6),separation.tolist()

def path_guard(path,start,goal,known):
 points=[[p.pose.position.x,p.pose.position.y,yaw(p)]for p in path.poses]
 assert len(points)>=2 and np.isfinite(points).all(),'INVALID_PATH'
 start_error=float(np.linalg.norm(np.asarray(points[0][:2])-[start.pose.position.x,start.pose.position.y]));goal_error=float(np.linalg.norm(np.asarray(points[-1][:2])-[goal.pose.position.x,goal.pose.position.y]));assert start_error<=.10 and goal_error<=.25,'ENDPOINT_CHANGED'
 # Sampling bound for midpoint of each interpolated SE(2) interval, same full physical bound.
 samples=dense(points);minimum=float(np.min(pose_values(field(known),samples)));rho=math.hypot(.44,.375);gap=.005+rho*.005;assert minimum-gap>=.15,'CONTINUOUS_KNOWN_STATIC_CLEARANCE'
 return dict(passed=True,minimum_full_bound_sample_clearance_m=minimum,between_sample_error_bound_m=gap,continuous_static_lower_bound_m=minimum-gap,start_error_m=start_error,goal_error_m=goal_error,samples=len(samples),scope='Known-static full bound only; current unknown cells checked by Smac, no future dynamic guarantee')

def terminal_goal(goal,known):
 candidates=[(0.,0.)]+[(.08*math.cos(a),.08*math.sin(a))for a in np.arange(16)*2*math.pi/16]
 poses=[[goal.pose.position.x+dx,goal.pose.position.y+dy,yaw(goal)]for dx,dy in candidates];clear=pose_values(field(known),poses);best=max(range(len(candidates)),key=lambda i:(float(clear[i]),-math.hypot(*candidates[i]),-i));out=copy.deepcopy(goal);out.pose.position.x=poses[best][0];out.pose.position.y=poses[best][1];return out,dict(displacement_m=math.hypot(*candidates[best]),selected_xy=poses[best][:2],public_static_clearance_m=float(clear[best]),original_xy=[goal.pose.position.x,goal.pose.position.y],candidate_count=len(candidates))

class PlannerProxy:
 def __init__(self,node,latest,out,deadline):
  from rclpy.action import ActionClient,ActionServer
  from rclpy.callback_groups import ReentrantCallbackGroup
  from nav2_msgs.action import ComputePathToPose
  from nav_msgs.msg import Path as NavPath
  self.publisher=node.create_publisher(NavPath,'plan',10)
  self.force_forward=False;self.node=node;self.latest=latest;self.out=out;self.deadline=deadline;self.rows=[];self.known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());self.kind=ComputePathToPose
  group=ReentrantCallbackGroup();self.client=ActionClient(node,ComputePathToPose,'smac_compute_path_to_pose',callback_group=group);self.server=ActionServer(node,ComputePathToPose,'compute_path_to_pose',self.execute,callback_group=group)
 async def execute(self,handle):
  from geometry_msgs.msg import PoseStamped
  result=self.kind.Result();row=dict(started_monotonic=time.monotonic(),passed=False,actual_vehicle_models=0)
  try:
   original=handle.request;nominal_goal=copy.deepcopy(original.goal);goal,terminal=terminal_goal(nominal_goal,self.known);row["terminal_region_choice"]=terminal;packet=self.latest();assert packet is not None and time.monotonic()-packet['sent_at']<=.2,'STALE_ODOMETRY';assert time.time()<self.deadline-25
   if original.use_start:start=copy.deepcopy(original.start)
   else:
    start=PoseStamped();start.header=copy.deepcopy(goal.header);x,y,a,*_=packet['body'];start.pose.position.x=x;start.pose.position.y=y;start.pose.orientation.z=math.sin(a/2);start.pose.orientation.w=math.cos(a/2)
   reverse,margins=request_direction(start,nominal_goal,self.known);reverse=reverse and not self.force_forward;query=self.kind.Goal();query.planner_id=original.planner_id;query.use_start=True;query.start=flip(goal)if reverse else copy.deepcopy(start);query.goal=flip(start)if reverse else copy.deepcopy(goal);row.update(reverse_search=reverse,endpoint_full_bound_clearances_m=margins,original_start=[start.pose.position.x,start.pose.position.y,yaw(start)],original_goal=[nominal_goal.pose.position.x,nominal_goal.pose.position.y,yaw(nominal_goal)])
   assert self.client.server_is_ready(),'SMAC_ACTION_NOT_READY';search_start=time.monotonic();accepted=await self.client.send_goal_async(query);assert accepted.accepted,'SMAC_REQUEST_REJECTED';response=await accepted.get_result_async();row.update(smac_action_status=response.status,smac_error_code=response.result.error_code,smac_wall_s=time.monotonic()-search_start)
   if response.status!=4:result.error_code=response.result.error_code;handle.abort();return result
   result.path=restore(response.result.path,reverse);row['geometry_guard']=path_guard(result.path,start,goal,self.known);endpoint=result.path.poses[-1].pose.position;terminal_error=math.hypot(endpoint.x-nominal_goal.pose.position.x,endpoint.y-nominal_goal.pose.position.y);assert terminal_error<=.10,'TERMINAL_REGION_ENDPOINT_OUTSIDE_INNER_BALL';row['endpoint_distance_to_original_goal_m']=terminal_error;result.planning_time=response.result.planning_time;result.error_code=0;row['passed']=True;self.publisher.publish(result.path);handle.succeed();return result
  except BaseException as e:
   row['error']=repr(e);result.error_code=208;handle.abort();return result
  finally:
   row['wall_s']=time.monotonic()-row['started_monotonic'];self.rows.append(row);(self.out/'ROUTER_REQUESTS.json').write_text(json.dumps(self.rows,indent=2)+'\n')
