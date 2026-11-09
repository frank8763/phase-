"""One original goal. Each command is admitted separately by the bridge/native seam."""
import time
def supervise(node,initial_goal,goal_until,deadline,spin,wait,require,check_servers):
    node.supervision_events=[]
    accepted=node.action.send_goal_async(initial_goal)
    wait(node,accepted.done,min(goal_until,time.monotonic()+2.),'GOAL_ACCEPT_TIMEOUT')
    handle=accepted.result();require(handle.accepted,'GOAL_REJECTED')
    future=handle.get_result_async()
    while not future.done():
        spin(node,timeout_sec=.005);check_servers()
        require(node.guard_failure is None,'COMMAND_CONTRACT_FAILURE '+str(node.guard_failure))
        require(time.monotonic()<goal_until and time.time()<deadline-25,'NAVIGATION_DEADLINE')
        node.motion.decision_snapshot()
    require(node.guard_failure is None,'COMMAND_CONTRACT_FAILURE')
    return future.result(),node.supervision_events
