"""Actual unchanged RPP: mixed path versus a single reverse segment, no plant."""
from probe_fixture import *


def main():
    O = R/'runs/v1348_recoverable_tracking/premature_probe'
    O.mkdir(exist_ok=False)
    os.sched_setaffinity(0, {3, 4, 5})
    os.nice(max(0, 19-os.getpriority(os.PRIO_PROCESS, 0)))
    rclpy.init(); node = Fixture(); started = time.monotonic()
    case = json.loads((R/'experiments/v1348_recoverable_tracking/SAVED_PREMATURE_REVERSAL.json').read_text())
    server = None; cases = []; error = None
    log = (O/'controller.console').open('x')
    def wait(predicate, seconds):
        until = min(started+90, time.monotonic()+seconds)
        while time.monotonic() < until:
            rclpy.spin_once(node, timeout_sec=.005)
            assert server is None or server.poll() is None, 'SERVER_EXIT'
            if predicate(): return
        raise TimeoutError('PROBE_TIMEOUT')
    def settle(seconds):
        until = time.monotonic()+seconds
        wait(lambda: time.monotonic() >= until, seconds+1)
    try:
        params = R/'experiments/v1346_measured_gear_handoff/rpp_async_default_params.json'
        server = subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server', '--ros-args', '--params-file', str(params)], stdout=log, stderr=subprocess.STDOUT)
        wait(node.change.service_is_ready, 20)
        for transition in [1, 3]:
            req = ChangeState.Request(); req.transition.id = transition
            f = node.change.call_async(req); wait(f.done, 10); assert f.result().success
        wait(node.action.server_is_ready, 5)
        node.fixture = case['fixture']; settle(1.)
        for name in ['full', 'forward_only']:
            node.label = name; offset = len(node.rows)
            path = NavPath(); path.header.frame_id = 'odom'; path.header.stamp = node.get_clock().now().to_msg()
            for x, y, yaw in case[name]:
                p = PoseStamped(); p.header = path.header
                p.pose.position.x = x; p.pose.position.y = y
                p.pose.orientation.z = math.sin(yaw/2); p.pose.orientation.w = math.cos(yaw/2)
                path.poses.append(p)
            goal = FollowPath.Goal(); goal.path = path; goal.controller_id = 'RPP'
            goal.goal_checker_id = 'goal_checker'; goal.progress_checker_id = 'progress_checker'
            f = node.action.send_goal_async(goal); wait(f.done, 5); h = f.result(); assert h.accepted
            result = h.get_result_async(); wait(lambda: result.done() or len(node.rows)-offset >= 12, 5)
            if not result.done():
                cancel = h.cancel_goal_async(); wait(cancel.done, 3); wait(result.done, 3)
            settle(.15)
            rows = node.rows[offset:]
            moving = [row for row in rows if abs(row['v']) >= .005]
            cases.append(dict(name=name, raw_commands=rows,
                              moving_signs=sorted(set(1 if row['v'] > 0 else -1 for row in moving)),
                              action_status=result.result().status))
    except BaseException as exc:
        error = dict(error=repr(exc), traceback=traceback.format_exc())
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try: server.wait(timeout=4)
            except subprocess.TimeoutExpired: server.kill(); server.wait(timeout=2)
        proof = dict(cases=cases, error=error, models=0, physical_native=0,
                     saved_actual_pose_and_ranges=True, stationary_velocity_explicit=True,
                     wall_s=time.monotonic()-started)
        dump(O/'RESULT.json', proof); dump(O/'OBSERVATIONS.json', node.packets)
        log.close(); node.destroy_node(); rclpy.shutdown()
    print(json.dumps({**proof, 'cases':[{k:v for k,v in x.items() if k != 'raw_commands'} for x in cases]}))
    return 1 if error else 0


if __name__ == '__main__':
    raise SystemExit(main())
