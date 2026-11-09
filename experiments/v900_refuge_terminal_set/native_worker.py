"""Reuse unchanged V882 runtime/evidence engine; authority before model import."""
import importlib.util,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static'),str(R/'experiments/v882_runtime_evidence_repair')]
from authority import authorized
spec=importlib.util.spec_from_file_location('v900_native_engine',R/'experiments/v882_runtime_evidence_repair/native_loop.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.C=C;engine.authorized=authorized
from packet_contract import policy_packet
engine.policy_packet=policy_packet
sys.path.insert(0,str(C))  # Select the declared dynamic adapter at the lazy import seam.
if __name__=='__main__':sys.exit(engine.main())
