"""Send a single quota-managed input file through a read-only child stream."""
from pathlib import Path
import json, subprocess

def launch(argv,frame,*,input_path,cwd,env):
    raw=json.dumps(frame,allow_nan=False).encode()+b'\n'
    assert len(raw)<=1024**2,'SVG_INPUT_BYTE_CAP'
    path=Path(input_path)
    # The existing OutputBoundary charges both this open and the exact bytes.
    # It also rejects escapes and symlinks. No raw-writer bypass is introduced.
    with path.open('xb')as stream:
        stream.write(raw)
    stream=path.open('rb')
    try:
        peer=subprocess.Popen(argv,cwd=cwd,env=env,stdin=stream,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    except BaseException:
        stream.close()
        raise
    return peer,stream
