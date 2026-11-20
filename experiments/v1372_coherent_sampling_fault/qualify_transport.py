"""Actual fault peer over UNIX datagrams; metadata cursor only, no physical import."""
import importlib.abc
import socket
import subprocess
import sys
from types import SimpleNamespace
from component_context import *
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('TRANSPORT_MODELS_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
from frames import SampleCache,wire_packet,validate_binding
from stamped_contract import assess_delivery
from transport import send_latest

def main():
    out=O/'transport_fixture'
    if '--peer' in sys.argv:
        from fault_peer import run
        return 0 if run(read(out/'TASK.json'))['passed'] else 1
    out.mkdir(exist_ok=False);task=read(C/'TASKS.json')[0];task['output']=str(out);dump(out/'TASK.json',task)
    class Cursor:
        count=41390;d=SimpleNamespace(time=413.9)
        def body(self):return task['origin_body']
        def scan(self):return dict(native_tick=self.count,time=self.d.time,xy=self.body()[:2],yaw=self.body()[2],ranges=[3.]*32)
    cursor=Cursor();cache=SampleCache();sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    address=str(out.relative_to(R)/'native.sock');sock.bind(address);sock.settimeout(.02)
    peer=None;sent={};events=[];sequence=0;accepted=-1;armed=False;deadline=time.monotonic()+10
    try:
        peer=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--peer'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        while time.monotonic()<deadline:
            wire=wire_packet(cache,cursor,task['run_id'],sequence);sent[sequence]=wire;sequence+=1
            send_latest(sock,json.dumps(wire).encode(),str(out.relative_to(R)/'ros.sock'))
            try:c=json.loads(sock.recv(65536))
            except socket.timeout:continue
            if c['kind']=='arm':assert cursor.count==41390;armed=True;continue
            if c['kind']=='stop':assert c['passed'] and cursor.count==41415;break
            assert armed;validate_binding(c,sent);d=assess_delivery(c,time.monotonic(),run_id=task['run_id'],previous_sequence=accepted)
            accepted=c['sequence'];events.append(dict(before=cursor.count,reason=d['reason']));cursor.count+=5;cursor.d.time=cursor.count*.01
        else:raise TimeoutError('METADATA_TRANSPORT_TIMEOUT')
        stdout,stderr=peer.communicate(timeout=3);assert peer.returncode==0,stderr
        assert [e['reason'] for e in events]==['OBSERVATION_EXPIRED']*4+[None]
        dump(O/'TRANSPORT_QUALIFICATION.json',dict(passed=True,events=events,actual_production_peer=True,actual_datagram_transport=True,
            synthetic_cursor_not_integrated=True,models=0,physical_native=0,controller_goals=0,source_hashes={str(p.relative_to(R)):sha(p) for p in C.glob('*.py')}))
        print(json.dumps(dict(passed=True,datagrams=len(events),models=0)))
    finally:
        if peer is not None and peer.poll() is None:peer.kill();peer.wait(timeout=2)
        sock.close();Path(address).unlink(missing_ok=True)
if __name__=='__main__':raise SystemExit(main())
