"""Real datagram fault peer in the isolated producer runtime; zero controller goals."""
import argparse
import importlib.abc
import os
import socket
import sys
import traceback
from component_context import *
from evidence_io import Journal
from frames import CORE,validate_wire
from stamped_contract import local_zero
from transport import send_latest

class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory'}:
            raise AssertionError('PEER_MODELS_FORBIDDEN '+name)

sys.meta_path.insert(0,NoPhysical())

def command(wire,sequence,now):
    return dict(kind='command',run_id=wire['run_id'],sequence=sequence,issued_at=now,v=0.,w=0.,
        origin=local_zero(now),observation_sequence=wire['sequence'],
        observation_native_tick=wire['native_tick'],observation_sampled_at=wire['sampled_at'])

def run(task):
    from stamped_contract import _contract
    out=Path(task['output']);sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    address=str(out.relative_to(R)/'ros.sock');peer=str(out.relative_to(R)/'native.sock')
    sock.bind(address);sock.settimeout(.1);commands=[];frames=[];result=dict(passed=False,models=0,controller_goals=0)
    log=Journal(out/'ROS_COMMANDS.jsonl');frame_log=Journal(out/'PEER_OBSERVATIONS.jsonl')
    end=time.monotonic()+60
    def receive(target):
        while time.monotonic()<end:
            assert not (out/'PEER_STOP_REQUEST.json').exists(),'NATIVE_EXITED'
            try:wire=json.loads(sock.recv(65536))
            except socket.timeout:continue
            validate_wire(wire)
            # Genuine old frames can be intentionally retained only by this fault injector.
            assert wire['run_id']==task['run_id']
            frame_log.append(wire);frames.append(wire)
            if wire['native_tick']==target:
                _contract.observation({k:wire[k] for k in CORE},run_id=task['run_id'],now=time.monotonic())
                return wire
            assert wire['native_tick']<target,'FAULT_PEER_OVERSHOOT'
        raise TimeoutError('FAULT_PEER_TIMEOUT')
    def send(value):
        assert send_latest(sock,json.dumps(value).encode(),peer),'FAULT_TRANSPORT_DROP'
    try:
        initial=receive(task['origin_native_tick'])
        send(dict(kind='arm',run_id=task['run_id'],issued_at=time.monotonic()))
        # Wait while no integration occurs; use this genuine expired observation four times.
        delay=initial['sampled_at']+.21-time.monotonic()
        if delay>0:time.sleep(delay)
        for sequence in range(4):
            packet=command(initial,sequence,time.monotonic());log.append(packet);commands.append(packet);send(packet)
        fresh=receive(task['origin_native_tick']+20)
        packet=command(fresh,4,time.monotonic());log.append(packet);commands.append(packet);send(packet)
        final=receive(task['origin_native_tick']+25)
        result.update(passed=True,initial_observation=initial['sequence'],fresh_observation=fresh['sequence'],
            final_observation=final['sequence'],fault='four genuine expired observations, fresh zero recovery',
            deliberately_stale_packets=4,fresh_packets=1,no_physical_modules_loaded=True)
        # Persist the receipt before stop so cooperative wrapper drain sees a closed peer.
        result.update(closed=True);dump(out/'ROS_COMMANDS.json',commands);dump(out/'ROS_RESULT.json',result)
        send(dict(kind='stop',run_id=task['run_id'],issued_at=time.monotonic(),passed=True))
    except BaseException as exc:
        result.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
    finally:
        log.close();frame_log.close();sock.close();Path(address).unlink(missing_ok=True)
        result.update(closed=True,no_physical_modules_loaded=not any(x in sys.modules for x in ['mujoco','vehicle','torch']))
        dump(out/'ROS_COMMANDS.json',commands);dump(out/'ROS_RESULT.json',result)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('task');parser.add_argument('--entry-check',action='store_true');a=parser.parse_args()
    task=read(a.task);task_check(task)
    # Import actual producer-runtime data libraries, never instantiate a ROS controller/model.
    import numpy
    if a.entry_check:
        print(json.dumps(dict(passed=True,models=0,physical_native=0,python=sys.version,numpy=numpy.__version__)));return 0
    authorize(task,read(O/'ROUND_WINDOW.json'))
    return 0 if run(task)['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
