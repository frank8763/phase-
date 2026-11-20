"""Cooperative wrapper-safe peer drain; no model starts or restarts."""
import os
from pathlib import Path
import signal
import time
from evidence_io import atomic


def terminate(job):
    if job.poll() is None:
        os.killpg(job.pid,signal.SIGTERM)
        try:job.wait(timeout=3)
        except Exception:
            if job.poll() is None:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=2)


def monitor(jobs,out,*,remaining,task_seconds=1600,drain_seconds=90,storage_check=lambda:True,poll_s=.15):
    out=Path(out);start=time.monotonic();deadline=start+task_seconds
    native_drain=None;ros_drain=None;cooperative_requested=False
    try:
        while any(job.poll() is None for job in jobs):
            assert remaining()>5,'ROOT_DEADLINE'
            assert time.monotonic()<deadline,'TASK_DEADLINE'
            assert storage_check(),'STORAGE_LIMIT'
            ros,native=[job.poll() for job in jobs]
            if ros is not None and native is None:
                if native_drain is None:
                    atomic(out/'STOP_AFTER_CURRENT_PREFIX.json',dict(reason='ROS_EXIT_DRAIN',ros_returncode=ros,no_additional_navigation=True))
                    native_drain=min(deadline,time.monotonic()+drain_seconds)
                assert time.monotonic()<native_drain,'NATIVE_DRAIN_TIMEOUT'
            if native is not None and ros is None:
                if ros_drain is None:
                    atomic(out/'PEER_STOP_REQUEST.json',dict(reason='NATIVE_EXIT_SAVE_ALL_ROS_EVIDENCE',native_returncode=native,no_additional_navigation=True))
                    ros_drain=min(deadline,time.monotonic()+15);cooperative_requested=True
                assert time.monotonic()<ros_drain,'ROS_COOPERATIVE_SAVE_TIMEOUT'
            time.sleep(poll_s)
        return dict(returncodes=[p.returncode for p in jobs],drain_requested=native_drain is not None,
            cooperative_ros_close_requested=cooperative_requested,wall_s=time.monotonic()-start)
    finally:
        for job in jobs:terminate(job)
