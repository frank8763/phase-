"""Explicit zero-optimizer peer for the real charged-client software test only."""
import sys,json,hashlib,os
assert os.sched_getaffinity(0)=={6}
raw=sys.stdin.buffer.readline(1024**2+1);frame=json.loads(raw);assert frame['explicit_software_fixture']and len(raw)<=1024**2
value=dict(passed=True,input_bytes=len(raw),input_byte_sha256=hashlib.sha256(raw).hexdigest(),answer=dict(explicit_software_fixture=True,models=0,optimizer_queries=0,proposal=dict(raw_request=[.08,0.,False],actual_execution_permitted=False)))
print('FILTER_REPLY '+json.dumps(value),flush=True);print('FILTER_CLOSED '+json.dumps(dict(explicit_software_fixture=True,models=0,optimizer_queries=0)),flush=True)
