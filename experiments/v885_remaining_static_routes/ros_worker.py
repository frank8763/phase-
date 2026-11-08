"""Same frozen V884 ROS engine, new remaining-route authority binding only."""
import importlib.util,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v884_feasible_rpp'),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v883_observation_dispatch'),str(R/'experiments/v862_ready_static')]
from authority import authorized
spec=importlib.util.spec_from_file_location('v885_ros_engine',R/'experiments/v884_feasible_rpp/ros_bridge.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.C=C;engine.authorized=authorized
if __name__=='__main__':sys.exit(engine.main())
