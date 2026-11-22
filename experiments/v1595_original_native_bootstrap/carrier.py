"""Original Python/CPP dynamics with own carried state and canonical gear.

Guard phase names distinguish proposal, complete generation, independent audit
and live current reserve. No imports or construction without that capability.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]


def exact(name,relative,guard):
    guard.check();path=R/relative
    assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[relative]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def create(*,kind,stage,defs,setup,origin,gear_memory,method,guard,engine=None):
    assert kind in ('CPP','PYTHON')
    guard.require_carrier(kind=kind,stage=stage,method=method)
    original=exact('v1595_original_carried_response','experiments/v1550_canonical_observer_policy/trajectory.py',guard)
    base=original.CPPTrajectory if kind=='CPP'else original.PythonTrajectory
    class Carrier(base):pass
    Carrier.stage=stage
    if kind=='CPP':
        assert engine is not None
        numerical=Carrier(defs,engine,copy.deepcopy(origin),copy.deepcopy(gear_memory),method,guard)
        batch=exact('v1595_original_cpp_zero_batch','experiments/v1571_complete_batch_comparison/batch_backend.py',guard)
        class Batched(batch.BatchCarrier):pass
        Batched.stage=stage
        return Batched(numerical)
    assert engine is None
    return Carrier(defs,setup,copy.deepcopy(origin),copy.deepcopy(gear_memory),method,guard)


def fill_stop(carrier,branch,*,kind):
    if kind=='CPP':return carrier.fill_complete_stop(branch)
    for _ in range(2200):branch.advance(carrier,(0.,0.,0))
    return dict(complete_stop_native=2200,physical_native=0)
