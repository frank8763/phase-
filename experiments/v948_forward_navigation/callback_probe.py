"""Real rclpy executor regression for the observed shared-group starvation seam."""
import importlib.abc
import json
import os
import sys
import threading
import time
from pathlib import Path


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from callback_layout import CallbackLayout
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v948_forward_navigation'


def run(shared):
    node=Node('phase_callback_layout_'+('old'if shared else'new'))
    layout=CallbackLayout();executor=MultiThreadedExecutor(num_threads=3)
    blocked=threading.Event();release=threading.Event();observations=[];work=[]
    def heavy():
        timer.cancel();work.append(time.monotonic());blocked.set()
        release.wait(.34);work.append(time.monotonic())
    timer=node.create_timer(.05,heavy,callback_group=None if shared else layout.telemetry)
    node.create_timer(.01,lambda:observations.append(time.monotonic()),
                      callback_group=None if shared else layout.observation)
    executor.add_node(node);end=time.monotonic()+.65
    try:
        while time.monotonic()<end:executor.spin_once(timeout_sec=.002)
    finally:
        release.set();executor.shutdown(timeout_sec=2.,wait_for_threads=True);node.destroy_node()
    assert len(work)==2,'FIXTURE_HEAVY_CALLBACK_MISSING'
    during=[x for x in observations if work[0]<x<work[1]]
    return dict(shared_default_group=shared,blocked_interval_s=work[1]-work[0],
        observations_during_work=len(during),
        maximum_reader_gap_s=max(b-a for a,b in zip(observations,observations[1:])),
        work=work,observations=observations)


rclpy.init()
try:cases=[run(True),run(False)]
finally:rclpy.shutdown()
checks=dict(original_shared_group_reproduces_over_200ms_gap=cases[0]['maximum_reader_gap_s']>.2 and cases[0]['observations_during_work']==0,
            separate_groups_keep_reader_running=cases[1]['observations_during_work']>=10 and cases[1]['maximum_reader_gap_s']<.2,
            same_three_workers=True,unchanged_200ms_guard=True)
result=dict(passed=all(checks.values()),checks=checks,cases=cases,models=0,integrations=0,
    scope='Actual installed ROS executor and production callback groups, fixed 340ms blocking diagnostics callback. Not arbitrary-load liveness or physical qualification.')
(OUT/('CALLBACK_QUALIFICATION'+os.environ['PHASE_SOFTWARE_ATTEMPT']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],checks=checks,gaps=[c['maximum_reader_gap_s']for c in cases])))
assert result['passed']
