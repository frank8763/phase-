"""Actual production peer on explicitly labeled saved sensor playback only."""
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
io=load('qualification_io',C/'evidence_io.py');env=load('qualification_ros_domain',C/'peer_environment.py');peer=load('qualification_actual_peer',C/'rpp_peer.py')
def main():
    os.chdir(R);os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    out=O/'peer_qualification';out.mkdir(exist_ok=False);task=json.loads((C/'ENTRY.json').read_text());io.atomic(out/'TASK.json',task)
    raw=Path(task['prior_raw']);final=json.loads((raw/'FINAL_PACKET.json').read_text())
    with gzip.open(raw/'physics/SENSORS.json.gz','rt') as stream:sensors=json.load(stream)
    scan=next(x for x in reversed(sensors) if x['native_tick']==10775);assert max(abs(x-y) for x,y in zip(scan['xy'],final['body'][:2]))<=1e-8
    run_id='v1394-saved-frame-interface-only';sequence=0;sent={}
    def packet():
        nonlocal sequence
        now=time.monotonic();wire=dict(schema=1,run_id=run_id,sequence=sequence,sampled_at=now,body=final['body'],ranges_m=scan['ranges'],native_tick=10775,sim_time=scan['time'],sensor_frame=dict(native_tick=10775,time=scan['time'],xy=scan['xy'],yaw=scan['yaw'],sampled_at=now))
        value=dict(kind='ACTUAL_FRAME',run_id=run_id,sequence=sequence,native_tick=10775,body=final['body'],wire=wire);sent[sequence]=value;sequence+=1;return value
    first=packet();peer.validate_request(first,run_id,-1);negative=[]
    for label,change in [('wrong_kind',dict(kind='MODELED_BODY_CAUSAL_MAP_NOT_SENSOR')),('changed_tick',dict(native_tick=10776)),('changed_body',dict(body=[0.,0.,0.,0.,0.]))]:
        try:peer.validate_request(dict(first,**change),run_id,-1)
        except AssertionError:negative.append(label)
        else:raise AssertionError('SOURCE_CHANGE_ACCEPTED')
    for label,mutate in [('stale',lambda w:w.update(sampled_at=time.monotonic()-.3)),('scan_tick',lambda w:w['sensor_frame'].update(native_tick=10776)),('ranges',lambda w:w['ranges_m'].__setitem__(0,4.))]:
        value=json.loads(json.dumps(packet()));mutate(value['wire'])
        try:peer.validate_request(value,run_id,-1)
        except AssertionError:negative.append(label)
        else:raise AssertionError('BAD_ACTUAL_FRAME_ACCEPTED')
    ros,environment=env.environment(out);job=None;result=dict(passed=False,models=0,physical_native=0,analytical_native=0,saved_sensor_playback_only=True,not_new_sensor_acquisition=True,physical_admission=False)
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str((out/'owner.sock').relative_to(R));sock.bind(address);sock.settimeout(.01);log=(out/'peer.console').open('x')
    try:
        command=ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'rpp_peer.py'),str(out),run_id,'--entry-check']);p=subprocess.run(command,cwd=R,env=environment,capture_output=True,text=True,timeout=30);(out/'entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-1000:]
        command=ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'rpp_peer.py'),str(out),run_id]);job=subprocess.Popen(command,cwd=R,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        target=str((out/'peer.sock').relative_to(R));until=time.monotonic()+10
        while not Path(target).exists():assert job.poll() is None and time.monotonic()<until;time.sleep(.02)
        replies=[];until=time.monotonic()+55;next_send=0.
        while len(replies)<2:
            assert job.poll() is None and time.monotonic()<until,'SAVED_SCAN_RPP_CALLBACK_TIMEOUT'
            if time.monotonic()>=next_send:sock.sendto(json.dumps(packet(),allow_nan=False).encode(),target);next_send=time.monotonic()+.05
            try:reply=json.loads(sock.recv(65536))
            except socket.timeout:continue
            assert reply['kind']=='ORIGINAL_RPP_ACTUAL_COMMAND' and reply['sequence'] in sent and reply['actual_frame_bound']
            source=sent[reply['sequence']]['wire'];assert reply['body']==source['body'] and reply['observation_sampled_at']==source['sampled_at'] and reply['observation_native_tick']==source['native_tick']
            assert reply['command_ros_ns']>=reply['first_tf_ros_ns'] and 0<=time.monotonic()-reply['origin']['generated_monotonic']<=.2
            replies.append(reply)
        sock.sendto(json.dumps(dict(kind='STOP',run_id=run_id)).encode(),target);job.wait(timeout=10);proof=json.loads((out/'PEER_RESULT.json').read_text());assert job.returncode==0 and proof['passed'] and proof['actual_sensor_messages']>0 and proof['synthetic_scan_messages']==0 and proof['controller_exited']
        result.update(passed=True,negative_cases=negative,source_saved_scan_native=10775,source_scan_file=str((raw/'physics/SENSORS.json.gz').relative_to(R)),actual_plugin_loaded=True,production_frame_to_scan_binding=True,replies=replies,bootstrap_refreshed_playback_frames=len(sent))
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
