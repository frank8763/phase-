"""Explicit process-local translation of historical CPU2 pins to CPU6.

Actual affinity queries remain unchanged. Only own threads may be changed;
CPU4 is permitted solely for the existing pure-geometry frontend thread.
"""
from pathlib import Path
import importlib.util, os, sys
C=Path(__file__).resolve().parent
_original=os.sched_setaffinity
_scheduler=os.sched_setscheduler
_installed=False
_remapped=0
def own(pid):
 assert isinstance(pid,int) and (pid==0 or str(pid) in {p.name for p in Path('/proc/self/task').iterdir()}),'FOREIGN_PROCESS_RESOURCE_MUTATION_REFUSED'
def affinity(pid,mask):
 global _remapped
 own(pid);mask=set(mask)
 if mask=={2}:mask={6};_remapped+=1
 assert mask in ({6},{4}),'UNDECLARED_PHASE_CPU_REFUSED'
 return _original(pid,mask)
def scheduler(pid,policy,param):
 own(pid);assert policy==os.SCHED_IDLE,'NONIDLE_PHASE_SCHEDULER_REFUSED'
 return _scheduler(pid,policy,param)
def install():
 global _installed
 assert not _installed and os.sched_getaffinity(0)=={6}
 os.sched_setaffinity=affinity;os.sched_setscheduler=scheduler
 spec=importlib.util.spec_from_file_location('resource_policy',C/'resource_policy.py')
 module=importlib.util.module_from_spec(spec);sys.modules['resource_policy']=module;spec.loader.exec_module(module)
 module.apply();_installed=True
 return report()
def report():
 threads={p.name:sorted(os.sched_getaffinity(int(p.name))) for p in Path('/proc/self/task').iterdir()}
 assert all(set(v)<= {4,6} for v in threads.values())
 return dict(actual_thread_affinities=threads,historical_CPU2_pin_requests_translated_to_6=_remapped,affinity_queries_are_actual=True,foreign_process_resource_mutation_forbidden=True,Stage_reserved_cores_untouched=True,physics_CPU=6,pure_geometry_CPU=4)
