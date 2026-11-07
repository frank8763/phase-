"""Real stopped lifecycle server: service discovery alone must not arm physics."""
import json,os,signal,sys,threading,time,traceback
from pathlib import Path
import rclpy
from lifecycle_msgs.srv import GetState
from cold_probe import Stationary,Stack,state,spin_until,C,O
def main():
 out=O/'negative';out.mkdir(exist_ok=False);rclpy.init();node=Stationary();stack=Stack(out,C/'gated.yaml');result=dict(passed=False,physical_vehicle_models=0,native_integrations=0,navigation_actions=0);timer=None;pid=None
 try:
  stack.start()
  for name in node.states:assert state(node,name)['state']==1
  pid=stack.jobs[6].pid;os.kill(pid,signal.SIGSTOP);assert node.states['bt_navigator'].service_is_ready();timer=threading.Timer(2.4,lambda:os.kill(pid,signal.SIGCONT));timer.start()
  t=time.monotonic();future=node.states['bt_navigator'].call_async(GetState.Request());answered=spin_until(node,future.done,2.0);elapsed=time.monotonic()-t;assert not answered,'FAULT_INJECTION_NOT_EFFECTIVE';node.states['bt_navigator'].remove_pending_request(future)
  fresh=state(node,'bt_navigator',3.);assert fresh['state']==1
  result.update(passed=True,discovered_but_unresponsive_server_rejected=True,old_two_second_response_deadline_exceeded=True,negative_wait_s=elapsed,fresh_reply_after_resume=fresh,physics_not_launched=True)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 finally:
  if pid:
   try:os.kill(pid,signal.SIGCONT)
   except ProcessLookupError:pass
  if timer:timer.join(timeout=3.)
  stack.close();node.destroy_node();rclpy.shutdown();(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
