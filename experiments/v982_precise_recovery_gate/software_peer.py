"""Explicit nonphysical bicycle fixture in a separate interpreter, like native IO.

This is not a vehicle model, physical observation, control prediction or replay.
"""
import gzip,importlib.abc,json,math,socket,sys,time
from pathlib import Path
import numpy as np
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())

def main():
    task_path=Path(sys.argv[1]);out=task_path.parent;task=json.loads(task_path.read_text())
    assert task.get('software_only_fixture')is True,'NOT_A_SOFTWARE_FIXTURE'
    root=Path(__file__).resolve().parents[2]
    saved=json.loads((root/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
    initial=saved['rows'][task['fixed_state_index']]['search_packet']
    peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=out/'physics.sock';peer.bind(str(address.relative_to(root)));peer.setblocking(False)
    phase='WAITING';pose=np.asarray(initial['body'][:3],float);tick=initial['native_tick'];v=w=0.;last=0.;target=time.monotonic();last_sent=0.;held=initial['steering']['position']
    events=[];states=[];stamps=[];ticks=[];errors=[];closing=False;started=time.monotonic()
    (out/'PEER_READY').touch()
    try:
        while not closing:
            assert time.monotonic()-started<100,'SOFTWARE_PEER_OUTER_TIMEOUT'
            for _ in range(64):
                try:message=json.loads(peer.recv(65536));events.append(message)
                except BlockingIOError:break
                if message['kind']=='arm':phase='RUNNING';target=time.monotonic()
                elif message['kind']=='command':v,w=message['v'],message['w'];last=message['issued_at']
                elif message['kind']=='stop':closing=True;break
            if closing:break
            now=time.monotonic()
            if phase=='RUNNING'and now>=target:
                if now-last>.2:v=w=0.
                a=pose[2];b=a+w*.01
                if abs(w)<1e-10:pose[:2]+=v*.01*np.array([math.cos(a),math.sin(a)])
                else:pose[:2]+=[v/w*(math.sin(b)-math.sin(a)),-v/w*(math.cos(b)-math.cos(a))]
                pose[2]=b;tick+=1;target+=.01
            if abs(v)>=.005:
                k=w/v;held=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]
            packet=dict(kind='observation',run_id=task['run_id'],phase=phase,native_tick=tick,sim_time=tick*.01,
                sent_at=now,body_measured_at=now,scan_measured_at=now,initial_snapshot=phase=='WAITING',body=[*pose,v,w],
                steering=dict(native_tick=tick,measured_at=now,position=list(held),velocity=[0.,0.]),
                scan=dict(native_tick=tick,time=tick*.01,xy=pose[:2].tolist(),yaw=float(pose[2]),ranges=[3.]*32))
            if now-last_sent>=(.02 if phase=='WAITING'else .01):
                try:peer.sendto(json.dumps(packet).encode(),str((out/'ros.sock').relative_to(root)))
                except(FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass
                if phase=='RUNNING':states.append(packet['body'][:3]);stamps.append(now);ticks.append(tick)
                last_sent=now
            time.sleep(.001)
    except BaseException as error:errors.append(repr(error))
    finally:
        peer.close();address.unlink(missing_ok=True)
        np.savez_compressed(out/'PEER_TRACE.npz',body=np.asarray(states).reshape(-1,3),sent_at=stamps,native_tick=ticks)
        with gzip.open(out/'PEER_EVENTS.json.gz','wt')as f:json.dump(events,f)
        (out/'PEER_RESULT.json').write_text(json.dumps(dict(passed=not errors,errors=errors,models=0,integrations=0,
             separate_interpreter=True,maximum_send_gap_s=max(np.diff(stamps),default=0.),synthetic_peer=True),indent=2)+'\n')
    return 0 if not errors else 1
if __name__=='__main__':sys.exit(main())
