"""Standalone explicit ROS source bindings; imports remain model-free."""
import sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v883_observation_dispatch'),str(R/'experiments/v862_ready_static')]
import ros_bridge as engine
if __name__=='__main__':sys.exit(engine.main())
