"""Reuse exact frozen V881 Nav2 bridge/routing; change authority and manifest only."""
import importlib.util,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];OLD=R/'experiments/v881_timing_accounting_continuation'
sys.path[:0]=[str(C),str(OLD),str(R/'experiments/v862_ready_static')]
from authority import authorized
spec=importlib.util.spec_from_file_location('v882_frozen_ros_bridge',OLD/'ros_bridge.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.C=C;engine.authorized=authorized
if __name__=='__main__':sys.exit(engine.main())
