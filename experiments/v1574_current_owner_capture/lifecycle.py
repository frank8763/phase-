"""Canonical initialization seam, not a vehicle launcher or physical authority.

The old lifecycle must not be monkeypatched after imports: its V1449 owner,
plain200 reserve, modeled peer and eventstop are incompatible. A future bounded
actual CLI must call this explicit binding immediately after original t0 setup,
then use the new Pump. That actual lifecycle remains unqualified here.
"""
import importlib.util
import os
from pathlib import Path
_s=importlib.util.spec_from_file_location('v1574_lifecycle_io',Path(__file__).with_name('source_io.py'))
io=importlib.util.module_from_spec(_s);_s.loader.exec_module(io)


def bind_initialized_t0(vehicle,*,task,output,setup,prepared_sources,atomic,check_budget,quota,lock):
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(io.R)
    assert Path('/proc/self/fd/%d'%lock.fileno()).resolve()==io.R/'runs/v648_static_unknown/execution.lock'
    lock_rows=[line.split()for line in Path('/proc/self/fdinfo/%d'%lock.fileno()).read_text().splitlines()if line.startswith('lock:')]
    assert any('FLOCK'in row and 'WRITE'in row and str(os.getpid())in row for row in lock_rows),'CALLER_MUST_ALREADY_HOLD_SINGLE_EXECUTION_LOCK'
    assert vehicle.count==0 and float(vehicle.d.time)==0.
    for name in ['native_step.py']:
        path='experiments/v1567_epoch_scope_target/'+name
        import hashlib
        assert hashlib.sha256((io.R/path).read_bytes()).hexdigest()==prepared_sources[path]
    module=io.exact('v1574_explicit_canonical_source_owner',io.C/'canonical_owner.py')
    return module.CanonicalOwner(vehicle,task=task,output=output,setup=setup,prepared_sources=prepared_sources,
                                  atomic=atomic,check_budget=check_budget,quota=quota)


def run(*args,**kwargs):
    # Before factory imports, modeled peers, locks, physical construction or
    # route start. Source wiring is not a new integrated launch admission.
    raise RuntimeError('V1574_ACTUAL_LIFECYCLE_UNQUALIFIED_NO_CAPTURE_RUNTIME_AUTHORITY')
