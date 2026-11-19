"""Production local peer drain. Never starts or restarts model workers."""
import json
import os
from pathlib import Path
import signal
import time


def atomic(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value)+'\n');temporary.replace(path)


def terminate(job):
    if job.poll() is None:
        os.killpg(job.pid,signal.SIGTERM)
        try:job.wait(timeout=3)
        except Exception:
            if job.poll() is None:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=2)


def monitor(jobs,out,*,remaining,task_seconds=1600,drain_seconds=90,storage_check=lambda:True,poll_s=.15):
    """On ROS exit request no-new-navigation stop, allow bounded native save.

    A nonzero exit is classified after evidence is complete. This function
    does not convert it to success, authorize another branch, or reset timers.
    """
    start=time.monotonic();deadline=start+task_seconds;drain_until=None
    try:
        while any(job.poll() is None for job in jobs):
            assert remaining()>5,'ROOT_DEADLINE'
            assert time.monotonic()<deadline,'TASK_DEADLINE'
            assert storage_check(),'STORAGE_LIMIT'
            ros,native=[job.poll() for job in jobs]
            if ros is not None and native is None:
                if drain_until is None:
                    atomic(out/'STOP_AFTER_CURRENT_PREFIX.json',dict(reason='ROS_EXIT_DRAIN',ros_returncode=ros,no_additional_navigation=True))
                    drain_until=min(deadline,time.monotonic()+drain_seconds)
                assert time.monotonic()<drain_until,'NATIVE_DRAIN_TIMEOUT'
            if native is not None and ros is None:
                terminate(jobs[0])
            time.sleep(poll_s)
        return dict(returncodes=[job.returncode for job in jobs],drain_requested=drain_until is not None,wall_s=time.monotonic()-start)
    finally:
        for job in jobs:terminate(job)
