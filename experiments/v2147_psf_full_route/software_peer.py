"""Explicit readonly persistent software-only peer, no numerical imports."""
import sys,json,os
from peer_contract import decode
assert os.sched_getaffinity(0)=={6}
calls=0;run_id=None;method=None;last_native=None
for raw in iter(lambda:sys.stdin.buffer.readline(1024**2+1),b''):
 frame=json.loads(raw);assert frame['explicit_software_fixture']
 if run_id is None:run_id=frame['current']['run_id'];method=frame['current']['method']
 _,ack=decode(raw,calls,method,run_id,last_native=last_native);last_native=frame['current']['native'];calls+=1
 print('FILTER_REPLY '+json.dumps(dict(passed=True,transport_ack=ack,answer=dict(explicit_software_fixture=True,models=0,optimizer_queries=0,proposal=dict(raw_request=[.08,0.,False],actual_execution_permitted=False)))),flush=True)
print('FILTER_CLOSED '+json.dumps(dict(optimizer_calls=calls,NLP_returns=0,inflight_unknown=False,all_source_SHA_after=True,models=0,optimizer_queries=0,explicit_software_fixture=True)),flush=True)
