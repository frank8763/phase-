"""No-model isolated peer used to verify cooperative close and real signals."""
import json
import os
from pathlib import Path
import signal
import sys
import time


def main():
    out=Path(sys.argv[1]);mode=sys.argv[2];out.mkdir(exist_ok=True)
    def stop(*args):raise InterruptedError('DIRECT_SIGNAL')
    signal.signal(signal.SIGTERM,stop)
    (out/'READY.json').write_text(json.dumps(dict(pid=os.getpid(),models=0))+'\n')
    try:
        while time.monotonic()<float(sys.argv[3]):
            if mode=='cooperative' and (out/'PEER_STOP_REQUEST.json').exists():break
            time.sleep(.01)
    except InterruptedError:pass
    finally:
        (out/'ROS_COMMANDS.json').write_text('[{"v":0.0,"w":0.0}]\n')
        (out/'ROS_RESULT.json').write_text(json.dumps(dict(passed=False,closed=True,models=0))+'\n')


if __name__=='__main__':main()
