"""One real installed RPP action from the restored causal state, all original gates."""
import concurrent.futures,copy,json,sys,time
from pathlib import Path
from types import SimpleNamespace
C=Path(__file__).parent;R=C.resolve().parents[1]
def run(node,until,deadline,spin,wait,require,check_servers):
    sys.path.insert(0,str(C))
    from state_reference import construct
    from transaction import TrackingGuard,fingerprint
    from binding import FollowPathBinding
    from steering_continuity import stopped_ready
    task=json.loads((node.motion.out/'TASK.json').read_text());rows=[]
    def tick():
        spin(node,timeout_sec=.005);check_servers();require(node.guard_failure is None,'COMMAND_CONTRACT_FAILURE '+str(node.guard_failure))
        require(time.monotonic()<until and time.time()<deadline-25,'COMPONENT_DEADLINE')
    node.renew_wait()
    packet,source=node.motion.decision_snapshot();begun=time.monotonic()
    # Match the qualified full-navigation supervisor: geometry runs off the
    # observation executor, which must keep receiving fresh body/encoder data.
    pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        pending=pool.submit(construct,copy.deepcopy(packet),copy.deepcopy(source),task['goal_xy'],copy.deepcopy(node.planner_proxy.known),begun)
        while not pending.done():tick();require(time.monotonic()-begun<5.,'REFERENCE_BUILD_OVER_5S')
        plan=pending.result()
    finally:pool.shutdown(wait=False,cancel_futures=True)
    (node.motion.out/'COMPONENT_REFERENCE.json').write_text(json.dumps(dict(proposal=plan,packet=packet,source=source),indent=2)+'\n')
    require(plan['passed'],'COMPONENT_REFERENCE_NOT_CERTIFIED')
    require(time.monotonic()-begun<5.,'REFERENCE_BUILD_OVER_5S')
    current,_=node.motion.decision_snapshot();require(stopped_ready(current,time.monotonic()),'COMPONENT_NOT_STOPPED_AT_INSTALL')
    node.forward.reference(plan['path']);node.committed_recovery=TrackingGuard(plan)
    effect=dict(action='SEND_FOLLOW_PATH_ONCE',path=plan['path'],path_sha256=fingerprint(plan['path']),controller_id='RecoveryFollowPath',goal_checker_id='recovery_goal_checker')
    binding=FollowPathBinding(node);wait(node,binding.client.server_is_ready,min(until,time.monotonic()+2.),'FOLLOW_SERVER_TIMEOUT')
    future=binding.send(effect);wait(node,future.done,min(until,time.monotonic()+2.),'FOLLOW_ACCEPT_TIMEOUT')
    handle=future.result();require(handle.accepted,'COMPONENT_FOLLOW_REJECTED');result=handle.get_result_async()
    node.committed_recovery.mode='FOLLOW_RECOVERY';start=copy.deepcopy(current)
    while not result.done():tick()
    status=result.result().status;require(status==4,'COMPONENT_FOLLOW_FAILED')
    node.committed_recovery.mode='STOPPED_REPLAN';settled=None
    while True:
        tick();p,s=node.motion.decision_snapshot();now=time.monotonic()
        if stopped_ready(p,now):
            settled=now if settled is None else settled
            if now-settled>=.5:break
        else:settled=None
    rows.append(dict(label='FIXED_STATE_CONTINUOUS_RECOVERY',path=plan['path'],proposal=plan,
                     start_packet=start,start_source=source,end_packet=p,end_source=s,follow_status=status,
                     actual_controller='RecoveryFollowPath',normal_action_sent=False))
    (node.motion.out/'CLOSED_HANDOFF.json').write_text(json.dumps(dict(stages=rows),indent=2)+'\n')
    return SimpleNamespace(status=status,result=SimpleNamespace(error_code=0)),rows
