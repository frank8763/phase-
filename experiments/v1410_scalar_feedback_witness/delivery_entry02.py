"""Exact new output binding; entry01 failed before any sync/remote request."""
import importlib.util
import os
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
spec=importlib.util.spec_from_file_location('v1410_archived_original_transport',C/'deliver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.O=O;m.h.O=O/'remote_delivery';m.h.W=m.h.O
assert m.TAG=='phase-v1410-scalar-feedback-json-failure-20261121'
if __name__=='__main__':
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    if '--sync'in sys.argv:m.sync()
    else:m.deliver()
