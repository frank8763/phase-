"""Real installed RPP plus actual ROS source cooperative close, zero models."""
import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from worker_monitor import monitor,terminate

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3,4,5})
    folder=R/'runs/v858_nav2_verified/v1357/close_fixture03';folder.mkdir(exist_ok=False)
    task=json.loads((C/'TASKS.json').read_text())[0]
    task.update(scope='SOFTWARE_ONLY_STATIONARY_PEER_NO_MODELS',task_id='software_close_fixture',run_id='v1357-software-close',output=str(folder))
    (folder/'TASK.json').write_text(json.dumps(task)+'\n')
    now,mono=time.time(),time.monotonic()
    (folder/'ROUND_WINDOW.json').write_text(json.dumps(dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+600,hard_stop_monotonic=mono+600,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()))+'\n')
    # Use the canonical initial physical scan from the passed static main,
    # never an actor/evaluator field. This fixture remains explicitly stationary.
    import gzip
    packets=json.load(gzip.open(R/'runs/v858_nav2_verified/v1354/rpp_fast_stamped_static_main/physics/SENSORS.json.gz','rt'))
    packet=packets[0];assert packet['native_tick']==0 and packet['xy']==[-4.,-2.]
    (folder/'SYNTHETIC_INPUT.json').write_text(json.dumps(dict(body=[-4.,-2.,0.,0.,0.],ranges_m=packet['ranges']))+'\n')
    spec=importlib.util.spec_from_file_location('ros_env',R/'experiments/v856_nav2_foundation/ros_environment.py')
    ros=importlib.util.module_from_spec(spec);spec.loader.exec_module(ros);env=ros.environment()
    install=R/'runs/v1340_overnight_preparation/install'
    env['AMENT_PREFIX_PATH']=str(install)+':'+env['AMENT_PREFIX_PATH'];env['LD_LIBRARY_PATH']=str(install/'lib')+':'+env['LD_LIBRARY_PATH']
    env.update(ROS_DOMAIN_ID='226',ROS_LOG_DIR=str(folder/'ros_logs'),CUDA_VISIBLE_DEVICES='')
    env.pop('LD_PRELOAD',None)
    jobs=[];logs=[]
    try:
        for label,command,runenv in [
            ('ros',ros.command(['/usr/bin/python3.12','-B',str(C/'ros_close_fixture.py'),str(folder/'TASK.json')]),env),
            ('synthetic_native',[sys.executable,'-B',str(C/'synthetic_peer.py'),str(folder)],dict(os.environ))]:
            log=(folder/(label+'.console')).open('x');logs.append(log)
            jobs.append(subprocess.Popen(command,cwd=R,env=runenv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
        result=monitor(jobs,folder,remaining=lambda:60-(time.monotonic()-mono),task_seconds=45)
    finally:
        for job in jobs:terminate(job)
        for log in logs:log.close()
    commands=json.loads((folder/'ROS_COMMANDS.json').read_text());closed=json.loads((folder/'ROS_RESULT.json').read_text())
    incremental=[json.loads(line) for line in (folder/'ROS_COMMANDS.jsonl').read_text().splitlines()]
    assert commands==incremental and len(commands)>=12
    assert closed['closed'] and closed['controller_server_exited'] and not closed['evidence_write_errors']
    assert closed['functional_stop']=='COOPERATIVE_PEER_CLOSED' and not closed.get('error')
    assert result['cooperative_ros_close_requested'] and jobs[0].returncode==1 and jobs[1].returncode==0
    proof=dict(passed=True,actual_installed_controller_started=True,actual_production_ROS_main_used=True,
        cooperative_peer_exit=True,full_and_incremental_commands_equal=True,commands=len(commands),
        controller_exited=True,monitor=result,models=0,physical_native=0,
        synthetic_stationary_packets_not_physics=True,no_physical_authority_bypassed=True)
    (O/'COOPERATIVE_PRODUCTION_ROS_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
