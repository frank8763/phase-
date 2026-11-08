"""Serve a saved measurement to real Nav2, discarding every generated command."""
import fcntl,hashlib,json,os,signal,socket,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v883_observation_dispatch'
def main():
    key=sys.argv[1];mode=sys.argv[2];suffix=sys.argv[3]if len(sys.argv)>3 else'';assert not suffix or suffix.isalnum();name='checkpoint_'+key+'_'+mode+suffix;out=O/name;out.mkdir(exist_ok=False)
    lock=(O/'ros_software.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert mode in ['original','concurrent','feasible','originaldelay','concurrentdelay']
    fixture=json.loads((O/'FIXTURES.json').read_text())[key];task=dict(fixture['task'],run_id='v883-'+name,output=str(out),socket_dir=str(out.relative_to(R)),scope='RECORDED_STATE_SENSOR_PLAYBACK_NO_VEHICLE',wall_limit_s=10,fixture_key=key,concurrent_dispatch=not mode.startswith('original'),nav2_params=str(R/('experiments/v884_feasible_rpp/A_feasible.yaml'if mode=='feasible'else'experiments/v881_timing_accounting_continuation/A.yaml')))
    if mode.endswith('delay'):task['diagnostic_route_busy_s']=.35
    task['feasible_command_contract']=mode=='feasible'
    now=time.time();receipt=dict(models_authorized=False,software_diagnostic_only=True,run_id=task['run_id'],started_unix=now,deadline_unix=now+65)
    for n,j in [('TASK.json',task),('AUTHORIZATION.json',receipt)]:(out/n).write_text(json.dumps(j,indent=2)+'\n')
    os.chdir(R);sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str(out.relative_to(R)/'physics.sock');sock.bind(address);sock.setblocking(False);armed=False;stopped=False;discarded=0;p=None
    sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));from ros_environment import command,environment
    try:
        with(out/'ros.console').open('w')as f:
            env=environment()
            if mode=='feasible':env['AMENT_PREFIX_PATH']=str(R/'runs/v884_feasible_rpp/install')+':'+env['AMENT_PREFIX_PATH']
            p=subprocess.Popen(command(['/usr/bin/python3.12',str(C/'ros_probe_worker.py'),str(out/'TASK.json'),str(out/'AUTHORIZATION.json')]),cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            while p.poll()is None and time.time()<receipt['deadline_unix']-5:
                for _ in range(128):
                    try:q=json.loads(sock.recv(65536))
                    except BlockingIOError:break
                    assert q['run_id']==task['run_id']
                    if q['kind']=='arm':armed=True
                    elif q['kind']=='stop':stopped=True
                    elif q['kind']=='command':discarded+=1
                if not stopped:
                    stamp=time.monotonic();scan=fixture['scan'];packet=dict(kind='observation',run_id=task['run_id'],phase='RUNNING'if armed else'WAITING',native_tick=0,sim_time=0.,sent_at=stamp,body_measured_at=stamp,scan_measured_at=stamp,initial_snapshot=not armed,body=fixture['body'],scan=dict(native_tick=0,time=0.,ranges=scan['ranges']),source=fixture['source'])
                    try:sock.sendto(json.dumps(packet).encode(),str(out.relative_to(R)/'ros.sock'))
                    except(FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass
                time.sleep(.005)
            if p.poll()is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    finally:
        if p and p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
        sock.close();Path(address).unlink(missing_ok=True)
        result=dict(closed=True,software_only=True,source=fixture['source'],mode=mode,model_initializations=0,model_integrations=0,actuator_commands_executed=0,generated_commands_discarded=discarded,returncode=None if p is None else p.returncode,original_old_costmap_not_recorded=True)
        (out/'PLAYBACK_COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
