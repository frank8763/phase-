"""Explicit software fixture only; no numerical/controller/model libraries."""
import hashlib,json,sys
from pathlib import Path
raw=sys.stdin.buffer.read(1024**2+1);assert len(raw)<=1024**2;frame=json.loads(raw)
assert frame.get('explicit_software_fixture')is True
for target in [Path(__file__).parent/'FORBIDDEN',Path(__file__).resolve().parents[2]/'runs/v2101_parallel_priest_vehicle/filter_output/FORBIDDEN']:
 try:target.write_text('forbidden')
 except OSError:pass
 else:raise AssertionError('NATIVE_PEER_WRITABLE_RUNS_OR_SOURCE')
print('PRIEST_EVENT '+json.dumps(dict(explicit_software_fixture=True,stage='INPUT_BOUND')),flush=True)
print('PRIEST_REPLY '+json.dumps(dict(passed=True,answer=dict(explicit_software_fixture=True,models=0,optimizer_queries=0),input_bytes=len(raw),input_byte_sha256=hashlib.sha256(raw).hexdigest())),flush=True)
print('PRIEST_CLOSED '+json.dumps(dict(explicit_software_fixture=True,models=0,optimizer_queries=0)),flush=True)
