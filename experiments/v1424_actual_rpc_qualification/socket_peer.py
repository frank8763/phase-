"""CPU3 software peer drives actual Unix datagrams, never ROS or a model."""
import json
import os
from pathlib import Path
import socket
import sys
import time
R=Path(__file__).resolve().parents[2]

def main():
 out=Path(sys.argv[1]);assert out.is_relative_to(R/'runs')and sorted(os.sched_getaffinity(0))==[3];os.chdir(R);sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str((out/'ros.sock').relative_to(R));target=str((out/'native.sock').relative_to(R));sock.bind(address);sock.settimeout(.02);sequence=0;last_request=-1;wires=[];replies=[];end=time.monotonic()+20
 try:
  (out/'PEER_READY.json').write_text(json.dumps(dict(pid=os.getpid(),cpu=[3],models=0,software_not_sensor=True)))
  while time.monotonic()<end:
   try:packet=json.loads(sock.recv(1024*1024));wires.append(packet['wire'])
   except socket.timeout:pass
   if(out/'PEER_STOP.json').exists():break
   path=out/'PEER_REQUEST.json'
   if not path.exists():continue
   request=json.loads(path.read_text())
   if request['index']<=last_request:continue
   if request['kind']=='arm':reply=dict(kind='arm',run_id='v1424_SOFTWARE_RPC_NOT_PLANT',issued_at=time.monotonic())
   else:
    wanted=request['native_tick'];available=[w for w in wires if w['native_tick']==wanted]
    if not available:continue
    wire=available[-1];now=time.monotonic();origin=dict(kind='NAV2_STAMPED',stamp_ns=1000000000,receipt_ros_ns=1000000000,receipt_monotonic=now,generated_monotonic=now,receipt_age_s=0.)
    reply=dict(kind='command',run_id=wire['run_id'],sequence=sequence,issued_at=now,v=.05,w=0.,command_source='CONTROLLER',origin=origin,observation_sequence=wire['sequence'],observation_native_tick=wire['native_tick'],observation_sampled_at=wire['sampled_at'])
    if request.get('tamper'):reply['observation_native_tick']+=1
    sequence+=1
   sock.sendto(json.dumps(reply).encode(),target);last_request=request['index'];replies.append(reply)
  (out/'PEER_RESULT.json').write_text(json.dumps(dict(closed=True,cpu=[3],models=0,physical_native=0,software_not_sensor=True,replies=replies,wires_received=len(wires)),indent=2)+'\n')
 finally:sock.close();Path(address).unlink(missing_ok=True)
if __name__=='__main__':main()
