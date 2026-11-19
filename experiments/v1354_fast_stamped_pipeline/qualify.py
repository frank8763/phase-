"""Actual pure worker and shared stamped boundary qualification, zero models."""
import importlib.util
import os
import subprocess
import sys
import time
from component_context import *
from planning_job import PlanningJob
from stamped_contract import origin_from_header,local_zero,validate_delivery,before_step


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    cases=[]
    for index in [1,4,8]:
        saved=read(R/('runs/v1350_bounded_complete_search/RESULT_%02d_MODE0.json'%index));request=saved['request']
        job=PlanningJob(O/('fast_worker_%02d'%index),worker=C/'route_worker.py',timeout_s=5.)
        job.start(request);begin=time.monotonic();polls=0
        try:
            while True:
                value=job.poll()
                if value is not None:break
                polls+=1;time.sleep(.005)
        finally:job.cancel()
        assert value['passed'] and not value.get('error') and value['path']==saved['path'],'FAST_WORKER_OR_EQUIVALENCE_FAILED'
        assert value['snapshot_dense_validation']['minimum_clearance_m']>=.22 and polls>=5
        cases.append(dict(saved_request=index,wall_s=time.monotonic()-begin,nonblocking_polls=polls,
                          exact_old_qualified_path=True,report=value['report'],snapshot_geometry=value['snapshot_dense_validation']))
    origin=origin_from_header(1000000000,1010000000,10.)
    packet=dict(v=.1,w=0.,origin=origin,observation_sequence=1,observation_native_tick=5,observation_sampled_at=9.99)
    delivery=validate_delivery(packet,10.01)
    assert before_step(.1,0.,delivery,10.02)[:2]==(.1,0.)
    v,w,proof=before_step(.1,.01,delivery,10.3);assert v==w==0. and not proof['fresh']
    negatives=0
    for fn in [lambda:origin_from_header(0,1,10.),lambda:origin_from_header(1000000000,1300000000,10.),
               lambda:origin_from_header(1000000000,900000000,10.),
               lambda:validate_delivery(dict(packet,origin=local_zero(10.)),10.01),
               lambda:validate_delivery(dict(packet,observation_sampled_at=9.),10.01),
               lambda:validate_delivery(dict(packet,origin=dict(origin,generated_monotonic=10.)),10.01)]:
        try:fn()
        except (AssertionError,KeyError):negatives+=1
        else:raise AssertionError('STAMP_NEGATIVE_NOT_REJECTED')
    zero=validate_delivery(dict(packet,v=0.,w=0.,origin=local_zero(10.)),10.01)
    assert before_step(0.,0.,zero,10.02)[:2]==(0.,0.)
    dump(O/'CHANGED_BOUNDARY_QUALIFICATION.json',dict(passed=True,actual_fast_worker_cli_cases=cases,
         expiry_zero_gate=True,stamped_negative_cases=negatives,local_nonzero_forbidden=True,models=0,physical_native=0))
    print(json.dumps(dict(passed=True,actual_fast_cases=3,negative_cases=negatives,models=0)))


if __name__=='__main__':main()
