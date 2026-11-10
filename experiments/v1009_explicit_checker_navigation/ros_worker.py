"""One-time operation entry; immutable V1004 scientific engine reused verbatim."""
import importlib.util,inspect,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v1004_planned_input_navigation'),str(R/'experiments/v945_rpccr_observation_liveness'),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v884_feasible_rpp'),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v883_observation_dispatch'),str(R/'experiments/v862_ready_static'),str(R/'experiments/v882_runtime_evidence_repair')]
from authority import authorized
assert Path(inspect.getsourcefile(authorized)).resolve()==C/'authority.py'
s=importlib.util.spec_from_file_location('v1006_frozen_engine',R/'experiments/v1004_planned_input_navigation/ros_bridge.py');engine=importlib.util.module_from_spec(s);s.loader.exec_module(engine)
engine.C=C;engine.authorized=authorized

sys.path.insert(0,str(C))
if __name__=='__main__':sys.exit(engine.main())
