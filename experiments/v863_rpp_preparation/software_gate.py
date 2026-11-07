"""Genuine RPP plugin configuration/activation; synthetic stationary messages, no vehicle."""
import json,os,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v863_rpp_preparation'
sys.path.insert(0,str(R/'experiments/v861_startup_gate'));sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
from cold_probe import Stationary,Stack,state,spin_until
from nav2_msgs.srv import ManageLifecycleNodes
import rclpy
def main():
 out=O/(sys.argv[1]if len(sys.argv)>1 else'software01');out.mkdir(exist_ok=False);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:3]));rclpy.init();node=Stationary();stack=Stack(out,C/'nav2_params.yaml');start=time.monotonic();result=dict(passed=False,vehicle_models=0,native_integrations=0,navigation_actions=0,synthetic_stationary_messages_only=True,plugin='official Nav2 RegulatedPurePursuitController1.3.13')
 try:
  stack.start();before={name:state(node,name)for name in node.states};assert all(v['state']==1 for v in before.values());assert spin_until(node,node.manager.service_is_ready,3.)
  request=ManageLifecycleNodes.Request();request.command=0;future=node.manager.call_async(request);assert spin_until(node,future.done,20.);assert future.result().success
  after={name:state(node,name)for name in node.states};assert all(v['state']==3 for v in after.values());result.update(passed=True,all_seven_active=after,wall_s=time.monotonic()-start)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc(),wall_s=time.monotonic()-start)
 finally:
  stack.close();node.destroy_node();rclpy.shutdown();(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
