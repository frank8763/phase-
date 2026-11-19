"""Execute each registered worker mode on the original failed request4."""
import os
import subprocess
import sys
import time
from component_context import *
from planning_job import PlanningJob
from stamped_contract import origin_from_header,local_zero,validate_delivery,before_step


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    saved=read(O/'SAVED_PREDICTOR_QUALIFICATION.json');rows=[]
    original=read(R/'runs/v858_nav2_verified/v1354/rpp_fast_stamped_dynamic_main/planner_jobs/request04.json')
    for index,(model,mode) in enumerate([('EXCURSION',0),('PERIODIC',0),('PERIODIC',1)]):
        qualified=next(p for p in saved['rows'] if p['saved_request']==4 and p['model']==model and p['planner_mode']==mode)
        request=dict(original,ball=qualified['ball'],planner_mode=mode)
        job=PlanningJob(O/('worker_qualification_%02d'%index),worker=C/'route_worker.py',timeout_s=5.)
        begin=time.monotonic();job.start(request);polls=0
        try:
            while True:
                value=job.poll()
                if value is not None:break
                polls+=1;time.sleep(.005)
        finally:job.cancel()
        assert value['passed'] and not value.get('error') and value['path']==qualified['path'],'ACTUAL_WORKER_PATH_MISMATCH'
        assert value['snapshot_dense_validation']['minimum_clearance_m']>=.22
        rows.append(dict(model=model,mode=mode,passed=True,wall_s=time.monotonic()-begin,nonblocking_polls=polls,
                         exactly_matches_qualified_path=True,report=value['report']))
    # The actual CLI rejects unregistered modes, not an altered fake planner.
    source=O/'unregistered_mode_request.json';target=O/'unregistered_mode_result.json'
    dump(source,dict(original,planner_mode=2))
    call=subprocess.run([sys.executable,'-B',str(C/'route_worker.py'),str(source),str(target)],cwd=R,capture_output=True,text=True,timeout=5)
    value=read(target);assert not value['passed'] and 'UNREGISTERED_PLANNER_MODE' in value['error']
    origin=origin_from_header(1000000000,1010000000,10.)
    packet=dict(v=.1,w=0.,origin=origin,observation_sequence=1,observation_native_tick=5,observation_sampled_at=9.99)
    binding=validate_delivery(packet,10.01)
    assert before_step(.1,0.,binding,10.02)[:2]==(.1,0.)
    v,w,proof=before_step(.1,.01,binding,10.3);assert v==w==0. and not proof['fresh']
    negatives=0
    for fn in [lambda:origin_from_header(0,1,10.),lambda:origin_from_header(1000000000,1300000000,10.),
               lambda:origin_from_header(1000000000,900000000,10.),
               lambda:validate_delivery(dict(packet,origin=local_zero(10.)),10.01),
               lambda:validate_delivery(dict(packet,observation_sampled_at=9.),10.01),
               lambda:validate_delivery(dict(packet,origin=dict(origin,generated_monotonic=10.)),10.01)]:
        try:fn()
        except (AssertionError,KeyError):negatives+=1
        else:raise AssertionError('STAMP_NEGATIVE_NOT_REJECTED')
    proof=dict(passed=True,actual_worker_cases=rows,unregistered_mode_rejected=True,
               stamped_negative_cases=negatives,expired_request_zeroed=True,models=0,physical_native=0)
    dump(O/'ACTUAL_WORKER_QUALIFICATION.json',proof);dump(O/'CHANGED_BOUNDARY_QUALIFICATION.json',proof)
    print(json.dumps(dict(passed=True,actual_workers=3,negatives=negatives+1,models=0)))


if __name__=='__main__':main()
