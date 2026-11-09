"""One bounded original NavigateToPose with admitted temporary breadcrumb goals."""
import copy,math,time
import numpy as np
from refuge_logic import wait_ok,choose_refuge
from terminal_set import membership
def supervise(node,initial_goal,goal_until,deadline,spin,wait,require,check_servers):
    events=[];mode='ORIGINAL';recoveries=0;checked_at=0.;refuge_started=None;arrived_at=None;arrival_scan=None;refuge_start_body=None;braking_started=None;selected_goal=None;arrived_tick=None
    def live():
        p=node.latest;require(p is not None and time.monotonic()-p['sent_at']<=.2,'STALE_REFUGE_ODOMETRY')
        with node.motion.lock:
            t=node.motion.tracker;support=None if t.support is None else t.support.copy();age=max(0.,time.monotonic()-node.motion.scan_monotonic);source=dict(source_native_tick=t.latest['native_tick'],source_scan_sim_time=t.when,source_age_s=age,support_bounds=None if support is None else support.tolist(),last_hit_time=t.last_hit)
        return p,support,age,source
    def issue(goal,role):
        node.planner_proxy.refuge_mode=role=='REFUGE'
        future=node.action.send_goal_async(goal);wait(node,future.done,min(goal_until,time.monotonic()+2.),'REFUGE_GOAL_ACCEPT_TIMEOUT');handle=future.result();require(handle.accepted,'REFUGE_GOAL_REJECTED')
        return handle,handle.get_result_async()
    handle,future=issue(initial_goal,'ORIGINAL');node.supervision_events=events
    while True:
        spin(node,timeout_sec=.005);check_servers()
        require(time.monotonic()<goal_until and time.time()<deadline-25,'NAVIGATION_DEADLINE')
        p,support,age,source=live();body=p['body'];now=time.monotonic()
        if future is not None and future.done():
            response=future.result()
            if mode=='ORIGINAL':return response,events
            require(response.status==4,'REFUGE_ACTION_FUNCTIONAL_FAILURE')
            require(wait_ok(body,support,age,hold=4.),'ACTUAL_REFUGE_TERMINAL_HOLD_NOT_ADMITTED')
            mode='BRAKING';future=None;braking_started=now
            events.append(dict(event='REFUGE_ACTION_REACHED',native_tick=p['native_tick'],body=list(body),source=source))
        if now-checked_at<.1:continue
        checked_at=now
        if mode=='ORIGINAL'and support is not None and not wait_ok(body,support,age,hold=6.):
            require(recoveries<3,'MAXIMUM_THREE_ADMITTED_REFUGES_EXHAUSTED')
            selection=choose_refuge(body,node.breadcrumbs,support,age,node.planner_proxy.known)
            events.append(dict(event='REFUGE_REQUEST',native_tick=p['native_tick'],body=body,source=source,selection=selection,breadcrumbs=list(node.breadcrumbs)))
            require(selection is not None,'NO_CAUSAL_ADMITTED_REFUGE')
            cancel=handle.cancel_goal_async();wait(node,cancel.done,min(goal_until,now+1.),'CANCEL_ORIGINAL_TIMEOUT');require(bool(cancel.result().goals_canceling),'ORIGINAL_CANCEL_REJECTED')
            wait(node,future.done,min(goal_until,time.monotonic()+1.),'ORIGINAL_CANCEL_COMPLETION_TIMEOUT')
            goal=copy.deepcopy(initial_goal);x,y,a=selection['goal'];goal.pose.header.stamp=node.get_clock().now().to_msg();goal.pose.pose.position.x=x;goal.pose.pose.position.y=y;goal.pose.pose.orientation.z=math.sin(a/2);goal.pose.pose.orientation.w=math.cos(a/2)
            node.planner_proxy.refuge_selection=selection;handle,future=issue(goal,'REFUGE');mode='REFUGE';recoveries+=1;refuge_started=now
            refuge_start_body=list(body);selected_goal=list(selection['goal'])
        elif mode=='REFUGE':
            require(wait_ok(body,support,age,hold=1.),'REFUGE_TRANSIT_LOST_SHORT_HOLD_MARGIN')
            require(now-refuge_started<=25.,'REFUGE_EXECUTION25S_LIMIT')
            entry=membership(body,refuge_start_body,selected_goal,support,age)
            if entry['passed']:
                events.append(dict(event='REFUGE_SET_ENTERED',native_tick=p['native_tick'],body=list(body),source=source,region=entry,start_body=refuge_start_body,selected_goal=selected_goal))
                cancel=handle.cancel_goal_async();wait(node,cancel.done,min(goal_until,now+1.),'REFUGE_SET_CANCEL_TIMEOUT')
                require(bool(cancel.result().goals_canceling),'REFUGE_SET_CANCEL_REJECTED')
                wait(node,future.done,min(goal_until,time.monotonic()+1.),'REFUGE_SET_CANCEL_COMPLETION_TIMEOUT')
                require(future.result().status==5,'REFUGE_SET_ACTION_NOT_CANCELED')
                future=None;mode='BRAKING';braking_started=now
        elif mode=='BRAKING':
            require(wait_ok(body,support,age,hold=1.),'REFUGE_BRAKING_HOLD_MARGIN_LOST')
            require(now-braking_started<=2.,'REFUGE_SET_BRAKING_TWO_SECONDS_LIMIT')
            # Odometry speed and yaw rate must both settle; no success from a cancel ACK.
            if abs(body[3])<=.03 and abs(body[4])<=.03:
                require(wait_ok(body,support,age,hold=4.),'ACTUAL_REFUGE_TERMINAL_HOLD_NOT_ADMITTED')
                events.append(dict(event='REFUGE_STOP_CONFIRMED',native_tick=p['native_tick'],body=list(body),source=source,brake_elapsed_s=now-braking_started))
                mode='HOLD';arrived_at=now;arrival_scan=source['source_scan_sim_time'];arrived_tick=p['native_tick']
        elif mode=='HOLD':
            require(wait_ok(body,support,age,hold=1.),'REFUGE_HOLD_MARGIN_LOST')
            # Resume only after an actual new positive return, not a predicted sighting.
            renewed=source['last_hit_time']is not None and source['last_hit_time']>arrival_scan
            if now-arrived_at>=1. and p['native_tick']-arrived_tick>=100 and renewed and wait_ok(body,support,age,hold=6.):
                events.append(dict(event='ORIGINAL_GOAL_RESUMED',native_tick=p['native_tick'],body=body,source=source))
                handle,future=issue(initial_goal,'ORIGINAL');mode='ORIGINAL'
