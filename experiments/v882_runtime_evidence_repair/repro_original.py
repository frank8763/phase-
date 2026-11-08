"""Fresh deterministic red reproduction of exact original100Hz backend, no real model/ROS."""
import importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];O=R/'runs/v882_runtime_evidence_repair'
def main():
 spec=importlib.util.spec_from_file_location('old_loop_fixture',R/'experiments/v862_backend_qualification/loop_fixture.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
 class LagClock(q.Clock):
  def __init__(self):super().__init__();self.injected=False
  def sleep(self,seconds):
   super().sleep(seconds)
   if not self.injected and self.mono-self.start>=.05:self.mono+=.12;self.injected=True
 with patch.object(q,'Clock',LagClock):result,v,wire,clock=q.fixture('normal')
 assert result['status']=='PHYSICAL_OR_EVIDENCE_EXCEPTION'and'PHYSICS_WALL_LAG_OVER_100MS'in result['error'];assert result['actual_native']>0 and result['replay_native']is None
 out=dict(red_reproduced=True,original_error=result['error'],actual_fake_executor_calls=v.count,original_replay_native=result['replay_native'],detailed_overrun_saved='timing' in result,actual_models=0,actual_integrations=0,actual_ros_servers=0,deterministic_injected_delay_s=.12,scope='Actual frozen production loop with fake clock/vehicle only; not a measured replay of the old host stall');(O/'ORIGINAL_RED.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));return 1
if __name__=='__main__':sys.exit(main())
