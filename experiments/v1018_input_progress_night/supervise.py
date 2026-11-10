"""Cancel normal action, commit matching planned inputs, then resume original goal."""
import concurrent.futures,copy,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1003_causal_recovery_execution'))
s=importlib.util.spec_from_file_location('v1004_exact_causal_input_plan',R/'experiments/v1017_input_validated_progress/plan.py');planner=importlib.util.module_from_spec(s);s.loader.exec_module(planner)
sys.path.insert(0,str(C))
from watchdog import ReferenceWatchdog
from steering_continuity import stopped_ready
from handoff import release_with_zero
from journal import Journal
MAX_RECOVERY_SEGMENTS=8

def supervise(node,initial_goal,goal_until,deadline,spin,wait,require,check_servers):
    goal=[initial_goal.pose.pose.position.x,initial_goal.pose.pose.position.y];rows=[];pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
    path=node.motion.out/'RECOVERY_CORRIDORS.json';node.supervision_events=[];journal=Journal(path)
    def save():journal.submit(rows)
    def tick():
        journal.check();spin(node,timeout_sec=.005);check_servers();require(node.guard_failure is None,'COMMAND_CONTRACT_FAILURE '+str(node.guard_failure))
        require(time.monotonic()<goal_until and time.time()<deadline-25,'NAVIGATION_DEADLINE')
    def stopped():
        p,_=node.motion.decision_snapshot();return stopped_ready(p,time.monotonic())
    def normal():
        node.forward.resume(goal);g=copy.deepcopy(initial_goal);g.pose.header.stamp=node.get_clock().now().to_msg()
        future=node.action.send_goal_async(g);wait(node,future.done,min(goal_until,time.monotonic()+2.),'GOAL_ACCEPT_TIMEOUT')
        h=future.result();require(h.accepted,'GOAL_REJECTED');return h,h.get_result_async()
    def cancel(handle,future):
        f=handle.cancel_goal_async();wait(node,f.done,min(goal_until,time.monotonic()+2.),'NORMAL_CANCEL_TIMEOUT')
        wait(node,future.done,min(goal_until,time.monotonic()+2.),'NORMAL_QUIESCENCE_TIMEOUT');require(future.result().status in [5,6],'NORMAL_ACTION_NOT_QUIESCENT')
        end=min(goal_until,time.monotonic()+2.)
        while not stopped():tick();require(time.monotonic()<end,'RECOVERY_STOP_TIMEOUT')
    save()
    try:
        handle,future=normal();watchdog=ReferenceWatchdog(goal,node.planner_proxy.known)
        while not future.done():
            tick();packet,source=node.motion.decision_snapshot();now=time.monotonic()
            if node.forward.replan_requested:
                require(node.forward.replan_count<=3,'FORWARD_REPLAN_LIMIT');cancel(handle,future);handle,future=normal()
                watchdog=ReferenceWatchdog(goal,node.planner_proxy.known,len(node.planner_proxy.rows),len(node.tube_decisions));continue
            event=watchdog.poll(node.planner_proxy.rows,node.tube_decisions,packet,source,now)
            if event is None:continue
            require(len(rows)<MAX_RECOVERY_SEGMENTS,'RECOVERY_SEGMENT_LIMIT');cancel(handle,future)
            packet,source=node.motion.decision_snapshot();memory=copy.deepcopy(packet['controller_memory'])
            setup=json.loads((node.motion.out/'physics/SETUP.json').read_text())
            row=dict(trigger=event,search_packet=packet,search_source=source,passed=False,original_goal=goal);rows.append(row);save()
            pending=pool.submit(planner.construct,copy.deepcopy(packet),copy.deepcopy(source),goal,copy.deepcopy(node.planner_proxy.known),setup,memory['last_ctrl'],memory['integral'],time.time()+5.)
            until=min(goal_until,time.monotonic()+5.)
            while not pending.done():tick();require(time.monotonic()<until,'RECOVERY_BUILD_OVER_5S')
            plan=pending.result();row['proposal']=plan;save();require(plan['passed'],'NO_CAUSAL_PLANNED_INPUT_RECOVERY')
            require(goal_until-time.monotonic()>len(plan['planned_body_requests'])*.01+3.,'NO_COMPLETE_PROFILE_TIME_RESERVE')
            pid=len(rows);record=dict(plan=plan,packet=packet,source=source)
            filename=node.motion.out/('COMMITTED_PROFILE_'+str(pid)+'.json');raw=(json.dumps(record,separators=(',',':'))+'\n').encode();filename.write_bytes(raw)
            node.profile_owner=True;node.send(dict(kind='commit_profile',issued_at=time.monotonic(),profile_id=pid,path=str(filename),sha256=hashlib.sha256(raw).hexdigest()))
            until=min(goal_until,time.monotonic()+1.)
            while node.latest.get('profile_status',{}).get('profile_id')!=pid:tick();require(time.monotonic()<until,'PROFILE_COMMIT_ACK_MISSING')
            while node.latest['profile_status'].get('completed_id')!=pid:tick()
            require(stopped(),'PROFILE_TAIL_NOT_ACTUALLY_STOPPED')
            end_packet,end_source=node.motion.decision_snapshot()
            progress=((packet['body'][0]-goal[0])**2+(packet['body'][1]-goal[1])**2)**.5-((end_packet['body'][0]-goal[0])**2+(end_packet['body'][1]-goal[1])**2)**.5
            require(progress>=.4,'PROFILE_NO_ACTUAL_GOAL_PROGRESS')
            handoff=release_with_zero(node,pid,goal_until,tick,require)
            row.update(passed=True,profile_id=pid,profile_file=str(filename),actual_goal_progress_m=progress,end_packet=end_packet,end_source=end_source,atomic_handoff=handoff)
            node.supervision_events.append(row);save()
            handle,future=normal();watchdog=ReferenceWatchdog(goal,node.planner_proxy.known,len(node.planner_proxy.rows),len(node.tube_decisions))
        return future.result(),node.supervision_events
    except BaseException as e:
        node.send(dict(kind='stop',issued_at=time.monotonic(),reason='SUPERVISION_EXCEPTION'))
        (node.motion.out/'RECOVERY_FAULT.json').write_text(json.dumps(dict(error=repr(e),traceback=traceback.format_exc(),rows=rows),indent=2)+'\n');raise
    finally:
        node.send(dict(kind='stop',issued_at=time.monotonic(),reason='SUPERVISION_FINISHED'))
        pool.shutdown(wait=False,cancel_futures=True);save();journal.close()
