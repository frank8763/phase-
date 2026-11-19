"""No-model stationary observation transport; exits after12 actual ROS commands."""
import json
from pathlib import Path
import socket
import sys
import time

R=Path(__file__).resolve().parents[2]


def main():
    folder=Path(sys.argv[1]);task=json.loads((folder/'TASK.json').read_text())
    source=json.loads((folder/'SYNTHETIC_INPUT.json').read_text())
    address=str(folder.relative_to(R)/'native.sock');peer=str(folder.relative_to(R)/'ros.sock')
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);sock.bind(address);sock.settimeout(.02)
    end=time.monotonic()+35;sequence=0;commands=[]
    try:
        while time.monotonic()<end:
            packet=dict(schema=1,run_id=task['run_id'],sequence=sequence,sampled_at=time.monotonic(),
                body=source['body'],ranges_m=source['ranges_m'],native_tick=0,sim_time=0.)
            sequence+=1
            try:sock.sendto(json.dumps(packet).encode(),peer)
            except (FileNotFoundError,ConnectionRefusedError,socket.timeout,BlockingIOError):pass
            try:value=json.loads(sock.recv(65536))
            except socket.timeout:continue
            assert value['run_id']==task['run_id']
            if value['kind']=='command':commands.append(value)
            if len(commands)>=12:break
        assert len(commands)>=12,'ACTUAL_ROS_COMMANDS_MISSING'
    finally:
        (folder/'SYNTHETIC_PEER_RESULT.json').write_text(json.dumps(dict(models=0,physical_native=0,
            commands_received=len(commands),pose_never_integrated=True))+'\n')
        sock.close();Path(address).unlink(missing_ok=True)


if __name__=='__main__':main()
