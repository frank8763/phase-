"""Deterministic GIL-stall seam: threaded vs separate producer, zero models."""
import json,subprocess,sys,threading,time
from pathlib import Path
C=Path(__file__).parent;R=C.resolve().parents[1];O=R/'runs/v991_coordinated_components'
def producer(path):
    stamps=[];end=time.monotonic()+.65
    while time.monotonic()<end:
        stamps.append(time.monotonic());time.sleep(.005)
    Path(path).write_text(json.dumps(stamps))
def main():
    threaded=O/'threaded_producer_stamps.json';isolated=O/'separate_producer_stamps.json'
    child=subprocess.Popen([sys.executable,'-B',str(C/'qualify_peer_isolation.py'),'--producer',str(isolated)])
    thread=threading.Thread(target=producer,args=(threaded,));thread.start()
    time.sleep(.15)
    old=sys.getswitchinterval()
    try:
        sys.setswitchinterval(.5)
        end=time.monotonic()+.25
        while time.monotonic()<end:pass
    finally:sys.setswitchinterval(old)
    thread.join();child.wait(timeout=2)
    a=json.loads(threaded.read_text());b=json.loads(isolated.read_text())
    gap=lambda rows:max(y-x for x,y in zip(rows,rows[1:]))
    result=dict(passed=gap(a)>.2 and gap(b)<.1,old_thread_producer_maximum_gap_s=gap(a),separate_producer_maximum_gap_s=gap(b),
                unchanged_observation_limit_s=.2,models=0,integrations=0,
                scope='Controlled .25s same-interpreter GIL stall distinguishes fixture architecture; not unique attribution of the original .2028s failure')
    (O/'PEER_ISOLATION_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
if __name__=='__main__':
    if '--producer'in sys.argv:producer(sys.argv[-1])
    else:main()
