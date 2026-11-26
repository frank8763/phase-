"""Explicit software peer; validates frames, never imports an optimizer/model."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from peer_contract import decode
count=0
for line in sys.stdin.buffer:
 frame,ack=decode(line,sequence=count,run_id=json.loads(line)['request']['run_id'])
 for k in range(2):print('SVG_EVENT '+json.dumps(dict(sequence=2*count+k,stage='SOFTWARE_PERSISTENT_FIXTURE')),flush=True)
 print('SVG_REPLY '+json.dumps(dict(passed=True,explicit_software_fixture=True,transport_ack=ack,solver_calls=0)),flush=True);count+=1
assert count==2
print('SVG_CLOSED '+json.dumps(dict(explicit_software_fixture=True,frames=count,models=0,optimizer_calls=0)),flush=True)
