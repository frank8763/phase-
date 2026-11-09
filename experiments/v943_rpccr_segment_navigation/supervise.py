"""Production-ready supervision seam; not imported by a live model in this stage.

The outer bridge retains responsibility for original command/native guards,
hard deadlines and durable finally teardown. Every source/callback fault raises
into that existing stop path. This module never emits actuator Twists.
"""
import concurrent.futures
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).parent),
               str(ROOT/'experiments/v938_rpccr_recovery_segments'),
               str(ROOT/'experiments/v939_rpccr_rpp_handoff')]
from watchdog import ReferenceWatchdog
from recovery import construct
from binding import FollowPathBinding

MAX_RECOVERY_SEGMENTS = 3


def supervise(node, initial_goal, goal_until, deadline, spin, wait, require, check_servers):
    goal_xy = [initial_goal.pose.pose.position.x, initial_goal.pose.pose.position.y]
    node.supervision_events = []
    evidence_path = node.motion.out/'RECOVERY_CORRIDORS.json'
    evidence = []
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def save():
        evidence_path.write_text(json.dumps(evidence, indent=2)+'\n')

    def tick():
        spin(node, timeout_sec=.005)
        check_servers()
        require(node.guard_failure is None, 'COMMAND_CONTRACT_FAILURE '+str(node.guard_failure))
        require(time.monotonic()<goal_until and time.time()<deadline-25, 'NAVIGATION_DEADLINE')

    def snapshot_stopped():
        packet, source = node.motion.decision_snapshot()
        return max(abs(packet['body'][3]), abs(packet['body'][4])) <= .03

    def normal_goal():
        goal = copy.deepcopy(initial_goal)
        goal.pose.header.stamp = node.get_clock().now().to_msg()
        accepted = node.action.send_goal_async(goal)
        wait(node, accepted.done, min(goal_until, time.monotonic()+2.), 'GOAL_ACCEPT_TIMEOUT')
        handle = accepted.result()
        require(handle.accepted, 'GOAL_REJECTED')
        return handle, handle.get_result_async()

    handle, future = normal_goal()
    watchdog = ReferenceWatchdog(goal_xy, node.planner_proxy.known)
    try:
        while not future.done():
            tick()
            packet, source = node.motion.decision_snapshot()
            event = watchdog.poll(node.planner_proxy.rows, node.tube_decisions,
                                  packet, source, time.monotonic())
            if event is None:
                continue
            require(len(evidence)<MAX_RECOVERY_SEGMENTS, 'RECOVERY_SEGMENT_LIMIT')
            transaction = watchdog.transaction
            row = dict(trigger=event, entry_packet=packet, entry_source=source,
                       passed=False, original_goal=goal_xy)
            evidence.append(row)
            save()
            cancel = handle.cancel_goal_async()
            wait(node, cancel.done, min(goal_until, time.monotonic()+2.), 'NORMAL_CANCEL_TIMEOUT')
            wait(node, future.done, min(goal_until, time.monotonic()+2.), 'NORMAL_QUIESCENCE_TIMEOUT')
            require(future.result().status in [5, 6], 'NORMAL_ACTION_NOT_QUIESCENT')
            transaction.canceled(True)
            until = min(goal_until, time.monotonic()+2.)
            while not snapshot_stopped():
                tick()
                require(time.monotonic()<until, 'RECOVERY_STOP_TIMEOUT')
            packet, source = node.motion.decision_snapshot()
            row.update(search_packet=packet, search_source=source)
            builder = executor.submit(construct, packet['body'][:3], goal_xy,
                                      copy.deepcopy(node.planner_proxy.known), source['periodic'])
            until = min(goal_until, time.monotonic()+5.)
            while not builder.done():
                tick()
                require(time.monotonic()<until, 'RECOVERY_GEOMETRY_BUILD_TIMEOUT')
            proposal = builder.result()
            row['proposal'] = proposal
            save()
            require(proposal['passed'], 'NO_CERTIFIED_RECOVERY_SEGMENT')
            packet, source = node.motion.decision_snapshot()
            effect = transaction.install(proposal, packet, source, time.monotonic())
            row.update(install_packet=packet, install_source=source, install_effect=effect)
            binding = FollowPathBinding(node)
            wait(node, binding.client.server_is_ready, min(goal_until, time.monotonic()+2.), 'FOLLOW_SERVER_TIMEOUT')
            accepted = binding.send(effect)
            wait(node, accepted.done, min(goal_until, time.monotonic()+2.), 'FOLLOW_ACCEPT_TIMEOUT')
            follow_handle = accepted.result()
            transaction.accepted(follow_handle.accepted)
            require(follow_handle.accepted, 'RECOVERY_FOLLOW_REJECTED')
            follow = follow_handle.get_result_async()
            save()
            while not follow.done():
                tick()
                packet, source = node.motion.decision_snapshot()
                transaction.monitor(packet, source, time.monotonic())
            transaction.follow_completed(follow.result().status)
            require(transaction.mode=='STOPPED_REPLAN', 'RECOVERY_FOLLOW_FAILED')
            until = min(goal_until, time.monotonic()+2.)
            while not snapshot_stopped():
                tick()
                require(time.monotonic()<until, 'RECOVERY_ENDPOINT_STOP_TIMEOUT')
            packet, source = node.motion.decision_snapshot()
            renewal = transaction.finish_segment(packet, source, time.monotonic())
            row.update(passed=True, end_packet=packet, end_source=source,
                       renewal=renewal, transaction_events=transaction.events,
                       follow_result_status=follow.result().status)
            node.supervision_events.append(row)
            save()
            handle, future = normal_goal()
            # Only new router/command events are eligible; original failures are not reused.
            watchdog = ReferenceWatchdog(goal_xy, node.planner_proxy.known,
                                         len(node.planner_proxy.rows), len(node.tube_decisions))
            watchdog.transaction.used_prior_tick = transaction.used_prior_tick
        return future.result(), node.supervision_events
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
        save()
