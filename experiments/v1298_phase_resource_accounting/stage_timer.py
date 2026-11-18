"""Per-stage CPU/wall accounting for future Phase callers; never scans processes.

Does not launch commands, initialize models, change affinity/priority or request
GPU access. Caller retains its own experiment authorization and write boundary.
RUSAGE_CHILDREN counts only children already reaped by this process. Concurrent
stages in one caller would overlap this aggregate: record them in separate owners.
"""
from contextlib import contextmanager
import os
import resource
import time


def snapshot():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(wall=time.monotonic(), own_user=own.ru_utime, own_system=own.ru_stime,
                reaped_child_user=children.ru_utime, reaped_child_system=children.ru_stime,
                own_max_rss_kib=own.ru_maxrss, reaped_child_max_rss_kib=children.ru_maxrss)


@contextmanager
def measure_stage(label, emit):
    """Emit a JSON-compatible record in finally, including on caller failure."""
    if not isinstance(label, str) or not label or not callable(emit):
        raise ValueError('EXPLICIT_STAGE_AND_WRITER_REQUIRED')
    start = snapshot()
    succeeded = False
    try:
        yield
        succeeded = True
    finally:
        stop = snapshot()
        wall = max(0., stop['wall'] - start['wall'])
        own_cpu = stop['own_user'] + stop['own_system'] - start['own_user'] - start['own_system']
        child_cpu = stop['reaped_child_user'] + stop['reaped_child_system'] - start['reaped_child_user'] - start['reaped_child_system']
        emit(dict(stage=label, caller_stage_succeeded=succeeded, wall_s=wall,
                  owner_cpu_s=max(0., own_cpu), reaped_child_cpu_s=max(0., child_cpu),
                  aggregate_cpu_s=max(0., own_cpu + child_cpu),
                  average_logical_cores_consumed=max(0., own_cpu + child_cpu) / wall if wall else None,
                  cpu_percent_one_core_basis=100 * max(0., own_cpu + child_cpu) / wall if wall else None,
                  owner_affinity=sorted(os.sched_getaffinity(0)),
                  owner_nice=os.getpriority(os.PRIO_PROCESS, 0),
                  owner_scheduler=os.sched_getscheduler(0),
                  owner_lifetime_peak_rss_kib=stop['own_max_rss_kib'],
                  reaped_child_lifetime_peak_rss_kib=stop['reaped_child_max_rss_kib'],
                  gpu_visibility_environment=os.environ.get('CUDA_VISIBLE_DEVICES'),
                  gpu_utilization_measured=False,
                  limitations='No live child CPU until reaped; lifetime RSS is not a stage delta; aggregate CPU may exceed one core. GPU environment is not utilization. No other jobs inspected.'))
