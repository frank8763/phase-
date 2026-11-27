"""Readonly software transport: replay saved reply shape, NEVER run numerical methods."""
import sys,json,os
from context import R,read,sha
from peer_contract import decode
from serialization import dumps
assert os.sched_getaffinity(0)=={6}
paths=sorted((R/'runs/v2156_pcbf_pinned_scipy_entry/components/MATH').glob('CASE_*_RESULT.json'))
# Choose the actual widest recorded conditioned reply, not a narrowed mock.
fixtures=[(len(dumps(read(p))),p,read(p))for p in paths]
_,path,fixture=max(fixtures,key=lambda x:x[0])
calls=0;run_id=None;method=None
for raw in iter(lambda:sys.stdin.buffer.readline(1024**2+1),b''):
 frame=json.loads(raw);assert frame['explicit_software_fixture']
 if run_id is None:run_id=frame['current']['run_id'];method=frame['current']['method']
 _,ack=decode(raw,calls,method,run_id);calls+=1
 answer=dict(explicit_software_fixture=True,models=0,optimizer_queries=0,numerical=fixture['answer'],returns=fixture['returns'],coordinate_transforms=fixture['transforms'],work_accounting=dict(optimizer_call_attempts=0,optimizer_calls=0,NLP_returns=0,inflight_unknown=False,internal_optimizer_work=None,models=0,wall_s=0.),proposal=dict(raw_request=fixture['answer']['commands'][0],actual_execution_permitted=False),saved_fixture_path=str(path.relative_to(R)),saved_fixture_sha256=sha(path))
 print('FILTER_REPLY '+dumps(dict(passed=True,transport_ack=ack,answer=answer)),flush=True)
print('FILTER_CLOSED '+dumps(dict(optimizer_calls=calls,NLP_returns=0,inflight_unknown=False,all_source_SHA_after=True,models=0,optimizer_queries=0,explicit_software_fixture=True)),flush=True)
