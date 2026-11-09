"""Goal-region admission uses the same causal forecast as the costmap."""
import copy,json,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v881_timing_accounting_continuation'))
sys.path.insert(0,str(R/'experiments/v891_dynamic_consistency_software'))
from planner_proxy import PlannerProxy,yaw,flip,restore,request_direction,path_guard
from reference_terminal import terminal_goal,ENDPOINT_RADIUS

class DynamicPlannerProxy(PlannerProxy):
    def __init__(self,node,latest,out,deadline,forecast,configured_footprint):
        self.forecast=forecast;self.configured_footprint=configured_footprint;self.use_new=True;self.refuge_mode=False;self.refuge_selection=None
        super().__init__(node,latest,out,deadline)
        self.force_forward=True
    async def execute(self,handle):
        assert self.use_new and not self.refuge_mode, 'LEGACY_OR_REVERSE_REFUGE_DISABLED'
        from geometry_msgs.msg import PoseStamped
        result=self.kind.Result();row=dict(started_monotonic=time.monotonic(),passed=False,actual_vehicle_models=0)
        try:
            original=handle.request;nominal_goal=copy.deepcopy(original.goal)
            row['original_goal']=[nominal_goal.pose.position.x,nominal_goal.pose.position.y,yaw(nominal_goal)]
            dynamic,source,packet=self.forecast()
            goal,terminal=terminal_goal(nominal_goal,self.known,dynamic,self.configured_footprint)
            if self.refuge_mode:
                goal=copy.deepcopy(nominal_goal);terminal=dict(reason='EXACT_CAUSAL_BREADCRUMB_REFUGE',selected_xy=[goal.pose.position.x,goal.pose.position.y],selection=self.refuge_selection)
            row['navigation_role']='REFUGE'if self.refuge_mode else 'ORIGINAL'
            row.update(terminal_region_choice=terminal,causal_forecast_source={k:v for k,v in source.items()if k!='periodic'})
            if goal is None:
                # A temporarily blocked admissible region is a planning failure,
                # not Smac START_OCCUPIED at the actual vehicle. BT may wait.
                result.error_code=208;row['wait_reason']='DYNAMIC_TERMINAL_BLOCKED';handle.abort();return result
            assert packet is not None and time.monotonic()-packet['sent_at']<=.2,'STALE_ODOMETRY';assert time.time()<self.deadline-25
            if original.use_start:start=copy.deepcopy(original.start)
            else:
                start=PoseStamped();start.header=copy.deepcopy(goal.header);x,y,a,*_=packet['body'];start.pose.position.x=x;start.pose.position.y=y;start.pose.orientation.z=math.sin(a/2);start.pose.orientation.w=math.cos(a/2)
            if self.refuge_mode:
                from nav_msgs.msg import Path as NavPath
                from refuge_logic import retained_suffix,exit_path_ok
                points,tracking=retained_suffix(packet['body'],self.refuge_selection['reference_path'])
                path=NavPath();path.header=copy.deepcopy(goal.header)
                for x,y,a in points:
                    p=PoseStamped();p.header=copy.deepcopy(goal.header);p.pose.position.x=x;p.pose.position.y=y;p.pose.orientation.z=math.sin(a/2);p.pose.orientation.w=math.cos(a/2);path.poses.append(p)
                age=source['source_age_s']+time.monotonic()-row['started_monotonic']
                row.update(original_start=list(packet['body'][:3]),source_body_native_tick=packet['native_tick'],refuge_reference_kind='RETAINED_ACTUAL_HISTORY',refuge_tracking=tracking,refuge_returned_path=points,exit_contract_source_age_s=age)
                row['geometry_guard']=path_guard(path,start,goal,self.known)
                row['refuge_path_contract']=exit_path_ok(points,source['center_support_bounds'],age,self.known)
                if not row['refuge_path_contract']['passed']:result.error_code=208;handle.abort();return result
                result.path=path;result.error_code=0;row['endpoint_distance_to_original_goal_m']=float(np.linalg.norm(np.asarray(points[-1][:2])-[goal.pose.position.x,goal.pose.position.y]));row['passed']=True
                self.publisher.publish(result.path);handle.succeed();return result
            reverse,margins=request_direction(start,nominal_goal,self.known);reverse=False
            query=self.kind.Goal();query.planner_id=original.planner_id;query.use_start=True;query.start=flip(goal)if reverse else copy.deepcopy(start);query.goal=flip(start)if reverse else copy.deepcopy(goal)
            row.update(reverse_search=reverse,endpoint_full_bound_clearances_m=margins,original_start=[start.pose.position.x,start.pose.position.y,yaw(start)],original_goal=[nominal_goal.pose.position.x,nominal_goal.pose.position.y,yaw(nominal_goal)])
            assert self.client.server_is_ready(),'SMAC_ACTION_NOT_READY';begun=time.monotonic();accepted=await self.client.send_goal_async(query);assert accepted.accepted,'SMAC_REQUEST_REJECTED';response=await accepted.get_result_async()
            row.update(smac_action_status=response.status,smac_error_code=response.result.error_code,smac_wall_s=time.monotonic()-begun)
            if response.status!=4:
                result.error_code=response.result.error_code
                if reverse and result.error_code==205:
                    row['wait_reason']='VIRTUAL_TERMINAL_ROOT_OCCUPIED';row['returned_error_code']=208;result.error_code=208
                handle.abort();return result
            result.path=restore(response.result.path,reverse);row['geometry_guard']=path_guard(result.path,start,goal,self.known)
            points=[[p.pose.position.x,p.pose.position.y,yaw(p)]for p in result.path.poses]
            from polygon_geometry import route_check
            # Current atomic source only; this remains nominal route geometry.
            prior=source.get('periodic')
            assert prior is not None or source['center_support_bounds']is None,'MISSING_ROUTE_PERIODIC_SOURCE'
            from navigation_policy import require_forward_path
            row['direction_guard']=require_forward_path(points)
            row['returned_path']=points
            row['dynamic_geometry_guard']=dict(passed=True,lower_m=None)if prior is None else route_check(points,prior)
            if not row['dynamic_geometry_guard']['passed']:
                result.error_code=208;row['wait_reason']='UNCERTIFIED_DYNAMIC_PATH';handle.abort();return result
            end=result.path.poses[-1].pose.position;error=math.hypot(end.x-nominal_goal.pose.position.x,end.y-nominal_goal.pose.position.y)
            assert error<=ENDPOINT_RADIUS+1e-9,'ENDPOINT_OUTSIDE_ORIGINAL_ADMISSIBLE_REGION'
            row['endpoint_distance_to_original_goal_m']=error;result.planning_time=response.result.planning_time;result.error_code=0;row['passed']=True;self.publisher.publish(result.path);handle.succeed();return result
        except BaseException as e:
            row['error']=repr(e);result.error_code=208;handle.abort();return result
        finally:
            row['wall_s']=time.monotonic()-row['started_monotonic'];self.rows.append(row);(self.out/'ROUTER_REQUESTS.json').write_text(json.dumps(self.rows,indent=2)+'\n')
