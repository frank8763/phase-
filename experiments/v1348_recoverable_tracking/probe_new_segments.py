"""Actual pinned RPP on new conservative path segments; no physical models."""
from probe_fixture import *
from segments import split


def main():
    out=R/'runs/v1348_recoverable_tracking/aligned_controller_probe';out.mkdir(exist_ok=False)
    os.sched_setaffinity(0,{3,4,5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    rclpy.init();node=Fixture();started=time.monotonic();server=None;cases=[];error=None
    log=(out/'controller.console').open('x')
    def wait(predicate,seconds):
        until=min(started+90,time.monotonic()+seconds)
        while time.monotonic()<until:
            rclpy.spin_once(node,timeout_sec=.005)
            assert server is None or server.poll() is None,'SERVER_EXIT'
            if predicate():return
        raise TimeoutError('NEW_SEGMENT_SOFTWARE_TIMEOUT')
    def settle(seconds):
        until=time.monotonic()+seconds;wait(lambda:time.monotonic()>=until,seconds+1)
    try:
        params=R/'experiments/v1348_recoverable_tracking/rpp_async_default_params.json'
        server=subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server','--ros-args','--params-file',str(params)],stdout=log,stderr=subprocess.STDOUT)
        wait(node.change.service_is_ready,20)
        for transition in [1,3]:
            req=ChangeState.Request();req.transition.id=transition;f=node.change.call_async(req);wait(f.done,10);assert f.result().success
        wait(node.action.server_is_ready,5)
        for index in [4,5]:
            fixture=json.loads((R/'experiments/v1348_recoverable_tracking'/('NEW_FIXTURE%02d.json'%index)).read_text())
            node.fixture=fixture['fixture'];node.label=str(index);settle(.8);offset=len(node.rows)
            result=json.loads((R/'runs/v1348_recoverable_tracking'/('CURVATURE_PROBE%02d.json'%index)).read_text())
            segment=split(result['path'])[0];path=NavPath();path.header.frame_id='odom';path.header.stamp=node.get_clock().now().to_msg()
            for x,y,yaw in segment['poses']:
                p=PoseStamped();p.header=path.header;p.pose.position.x=x;p.pose.position.y=y
                p.pose.orientation.z=math.sin(yaw/2);p.pose.orientation.w=math.cos(yaw/2);path.poses.append(p)
            goal=FollowPath.Goal();goal.path=path;goal.controller_id='RPP';goal.goal_checker_id='goal_checker';goal.progress_checker_id='progress_checker'
            f=node.action.send_goal_async(goal);wait(f.done,5);h=f.result();assert h.accepted;done=h.get_result_async()
            wait(lambda:done.done() or len(node.rows)-offset>=16,5)
            if not done.done():
                cancel=h.cancel_goal_async();wait(cancel.done,3);wait(done.done,3)
            settle(.15);rows=node.rows[offset:];moving=[x for x in rows if abs(x['v'])>=.005]
            passed=bool(moving and all(x['contract_error'] is None for x in rows) and all(x['v']*segment['gear']>0 for x in moving))
            cases.append(dict(saved_request=index,passed=passed,expected_gear=segment['gear'],commands=len(rows),moving_signs=sorted(set(1 if x['v']>0 else -1 for x in moving)),action_status=done.result().status))
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:server.wait(timeout=4)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        proof=dict(passed=error is None and len(cases)==2 and all(x['passed'] for x in cases),cases=cases,error=error,models=0,physical_native=0,stationary_saved_pose_ranges_software_only=True,wall_s=time.monotonic()-started)
        dump(out/'RESULT.json',proof);dump(out/'RAW_COMMANDS.json',node.rows)
        log.close();node.destroy_node();rclpy.shutdown()
    print(json.dumps(proof));return 0 if proof['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
