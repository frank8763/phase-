"""One-time operation entry; immutable V1004 scientific engine reused verbatim."""
import importlib.util,inspect,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v1004_planned_input_navigation'),str(R/'experiments/v945_rpccr_observation_liveness'),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v884_feasible_rpp'),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v883_observation_dispatch'),str(R/'experiments/v862_ready_static'),str(R/'experiments/v882_runtime_evidence_repair')]
from authority import authorized
assert Path(inspect.getsourcefile(authorized)).resolve()==C/'authority.py'
s=importlib.util.spec_from_file_location('v1006_frozen_engine',R/'experiments/v1004_planned_input_navigation/native_loop.py');engine=importlib.util.module_from_spec(s);s.loader.exec_module(engine)
engine.C=C;engine.authorized=authorized
def load_exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
bound_packet=load_exact('v1018_exact_packet_contract',C/'packet_contract.py')
bound_native=load_exact('v1018_exact_atomic_receiver',C/'native_contract.py')
engine.policy_packet=bound_packet.policy_packet;engine.Startup=bound_native.Startup
sys.path.insert(0,str(C))
def binding_receipt():
    import hashlib
    receiver=Path(inspect.getsourcefile(engine.Startup.receive)).resolve();wanted=(C/'native_contract.py').resolve()
    assert receiver==wanted and engine.Startup is bound_native.Startup,'BACKEND_RECEIVER_NOT_EXACT_FROZEN_CANDIDATE'
    assert engine.policy_packet is bound_packet.policy_packet
    return dict(passed=True,receiver=str(receiver.relative_to(R)),receiver_sha256=hashlib.sha256(receiver.read_bytes()).hexdigest(),
        packet_source=str((C/'packet_contract.py').resolve().relative_to(R)),exact_path_binding=True,models_at_binding=0)
if __name__=='__main__':
    import json
    proof=binding_receipt();task=json.loads(Path(sys.argv[1]).read_text());out=Path(task['output'])
    assert out.resolve().is_relative_to(R/'runs/v858_nav2_verified/v1018')
    (out/'BACKEND_ENTRY_BINDING.json').write_text(json.dumps(proof,indent=2)+'\n')
    sys.exit(engine.main())
