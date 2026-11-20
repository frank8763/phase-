"""One real RPP RPC boundary on saved body, no model steps or fake scans."""
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
io=load('peer_qualification_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')

def environment(out):
    ros=load('peer_qualification_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();install=R/'runs/v1340_overnight_preparation/install'
    env['AMENT_PREFIX_PATH']=str(install)+':'+env['AMENT_PREFIX_PATH'];env['LD_LIBRARY_PATH']=str(install/'lib')+':'+env['LD_LIBRARY_PATH'];env.update(ROS_DOMAIN_ID='233',ROS_LOG_DIR=str(out/'ros_logs'),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    return ros,env

def main():
    os.chdir(R);os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    out=O/'peer_qualification01';out.mkdir(exist_ok=False);run_id='v1393-peer-qualification01';ros,env=environment(out)
    result=dict(passed=False,models=0,analytical_native=0,physical_native=0,actual_moving_response_qualified=False,physical_admission=False,saved_constant_fixture_only=True)
    peer=load('qualified_request_contract',C/'rpp_peer.py');saved=json.loads((O/'FIXED_INPUTS.json').read_text());packet=dict(kind='MODELED_BODY_CAUSAL_MAP_NOT_SENSOR',run_id=run_id,sequence=0,native_tick=10775,body=saved['observed_packet']['body'],sent_monotonic=time.monotonic())
    rejected=[]
    for label,mutation,previous in [('wrong_kind',dict(kind='MEASURED_FUTURE_SCAN'),-1),('foreign_id',dict(run_id='wrong'),-1),('replay',{},0),('nonfinite',dict(body=[math.nan,0.,0.,0.,0.]),-1),('old_delivery',dict(sent_monotonic=time.monotonic()-3),-1)]:
        try:peer.validate_request(dict(packet,**mutation),run_id,previous)
        except AssertionError:rejected.append(label)
        else:raise AssertionError('BAD_RPC_INPUT_ACCEPTED')
    job=None;sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str(out.relative_to(R)/'owner.sock');sock.bind(address);sock.settimeout(.1);log=(out/'peer.console').open('x')
    try:
        command=ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'rpp_peer.py'),str(out),run_id,'--entry-check'])
        p=subprocess.run(command,cwd=R,env=env,capture_output=True,text=True,timeout=30);(out/'entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-2000:];assert json.loads(p.stdout.strip().splitlines()[-1])['passed']
        command=ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'rpp_peer.py'),str(out),run_id])
        job=subprocess.Popen(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);io.atomic(out/'OWN_PEER.json',dict(pid=job.pid,models=0))
        target=str(out.relative_to(R)/'peer.sock');until=time.monotonic()+10
        while not Path(target).exists():
            assert job.poll() is None and time.monotonic()<until,'PEER_SOCKET_ENTRY';time.sleep(.05)
        replies=[]
        for sequence in range(2):
            request=dict(packet,sequence=sequence,sent_monotonic=time.monotonic());sock.sendto(json.dumps(request,allow_nan=False).encode(),target);until=time.monotonic()+(55 if sequence==0 else 3)
            while True:
                assert job.poll() is None and time.monotonic()<until,'PEER_CALLBACK_TIMEOUT'
                try:reply=json.loads(sock.recv(65536));break
                except socket.timeout:pass
            assert reply['kind']=='ORIGINAL_RPP_MODELED_COMMAND' and reply['sequence']==sequence and reply['body']==request['body']
            assert reply['command_ros_ns']>=reply['first_tf_ros_ns'] and reply['origin']['receipt_age_s']<=.2
            assert reply['v']>=.005 and reply['not_measured_response'];replies.append(reply)
        sock.sendto(json.dumps(dict(kind='STOP',run_id=run_id)).encode(),target);job.wait(timeout=10)
        proof=json.loads((out/'PEER_RESULT.json').read_text());assert job.returncode==0 and proof['passed'] and proof['synthetic_scan_messages']==0 and proof['controller_exited']
        result.update(passed=True,negative_cases=rejected,replies=replies,real_original_plugin_loaded=True,no_synthetic_scan_messages=True,controller_exited=True,tested_peer_sha256=peer.data.sha(C/'rpp_peer.py'))
    except BaseException as exc:
        import traceback
        result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if job is not None and job.poll() is None:
            os.killpg(job.pid,15)
            try:job.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(job.pid,9);job.wait(timeout=3)
        sock.close();Path(address).unlink(missing_ok=True);log.close();io.atomic(out/'QUALIFICATION.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['replies','traceback']}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
