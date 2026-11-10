"""Owned nonphysical subprocesses reproducing isolation parent-death behavior."""
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    mode, folder = sys.argv[1:3]
    out = Path(folder)
    if mode.startswith('wrapper'):
        child = subprocess.Popen([sys.executable, __file__, mode.replace('wrapper', 'native'), folder])
        (out/'CHILD.json').write_text(json.dumps({'pid': child.pid}))
        return child.wait()
    if mode.startswith('native'):
        parent = os.getppid()
        assert ctypes.CDLL(None).prctl(1, signal.SIGKILL, 0, 0, 0) == 0
        assert os.getppid() == parent
        (out/'READY').touch()
        if mode == 'native_hung':
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            while True:
                time.sleep(.01)
        while not (out/'PARENT_STOP_REQUEST.json').exists():
            time.sleep(.005)
        time.sleep(.15)  # Nonphysical stand-in for serialization.
        (out/'NATIVE_SAVED.json').write_text(json.dumps({'fixture': True, 'models': 0}))
        return 0
    if mode == 'ros_failure':
        return 7
    raise AssertionError('UNKNOWN_FIXTURE_MODE')


if __name__ == '__main__':
    sys.exit(main())
