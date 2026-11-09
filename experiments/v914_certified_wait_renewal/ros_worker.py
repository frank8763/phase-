"""V884 nominal bridge plus declared causal-map publisher and measured costmap evidence."""
import importlib.util,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v884_feasible_rpp'),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v883_observation_dispatch'),str(R/'experiments/v862_ready_static')]
from authority import authorized
spec=importlib.util.spec_from_file_location('v914_ros_engine',C/'ros_bridge.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.C=C;engine.authorized=authorized
if __name__=='__main__':sys.exit(engine.main())
