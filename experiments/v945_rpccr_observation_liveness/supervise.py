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
import traceback
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
    transaction = None
    row = None
    context = dict(stage='initial', exact_check_input=False)

    def write(path, data):
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, indent=2)+'\n')
        temporary.replace(path)

    def save():
        if row is not None and transaction is not None:
            row['transaction_events'] = copy.deepcopy(transaction.events)
        write(evidence_path, evidence)

    def tick():
        context.update(stage='spin_and_original_guards', exact_check_input=False)
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

    def observe(stage):
        context.update(stage=stage, exact_check_input=False)
        packet, source = node.motion.decision_snapshot()
        checked_at = time.monotonic()
        context.update(packet=copy.deepcopy(packet), source=copy.deepcopy(source),
                       checked_at=checked_at, exact_check_input=True,
                       body_age_s=checked_at-packet['body_measured_at'])
        return packet, source, checked_at

    try:
        handle, future = normal_goal()
        watchdog = ReferenceWatchdog(goal_xy, node.planner_proxy.known)
        while not future.done():
            tick()
            packet, source, checked_at = observe('reference_loss_entry')
            event = watchdog.poll(node.planner_proxy.rows, node.tube_decisions,
                                  packet, source, checked_at)
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
            packet, source, checked_at = observe('construct_input')
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
            packet, source, checked_at = observe('install')
            effect = transaction.install(proposal, packet, source, checked_at)
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
                packet, source, checked_at = observe('monitor')
                transaction.monitor(packet, source, checked_at)
            transaction.follow_completed(follow.result().status)
            require(transaction.mode=='STOPPED_REPLAN', 'RECOVERY_FOLLOW_FAILED')
            until = min(goal_until, time.monotonic()+2.)
            while not snapshot_stopped():
                tick()
                require(time.monotonic()<until, 'RECOVERY_ENDPOINT_STOP_TIMEOUT')
            packet, source, checked_at = observe('finish_segment')
            renewal = transaction.finish_segment(packet, source, checked_at)
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
    except BaseException as error:
        failure = dict(error=repr(error), traceback=traceback.format_exc(),
                       observed_at=time.monotonic(), input=copy.deepcopy(context),
                       guard_failure=node.guard_failure,
                       retained_proof=copy.deepcopy(getattr(node, 'retained_proof', None)),
                       transaction_mode=None if transaction is None else transaction.mode,
                       completed_segments=sum(item['passed'] for item in evidence))
        if row is not None:
            row['fault'] = failure
        write(node.motion.out/'RECOVERY_FAULT.json', failure)
        raise
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
        save()
