"""Explicit software transport peer: never import or execute a solver/model."""
import hashlib, json, sys

raw=sys.stdin.buffer.readline(1024**2+1)
assert len(raw)<=1024**2 and raw.endswith(b'\n')
frame=json.loads(raw)
assert frame['kind']=='EXPLICIT_SOFTWARE_NAMESPACE_FIXTURE'
for k in range(4):
    print('SVG_EVENT '+json.dumps(dict(sequence=k,stage='SOFTWARE_BOUNDARY_FIXTURE')),flush=True)
print('SVG_REPLY '+json.dumps(dict(passed=True,explicit_software_fixture=True,input_sha256=hashlib.sha256(raw).hexdigest())),flush=True)
print('SVG_CLOSED '+json.dumps(dict(explicit_software_fixture=True,models=0,optimizer_calls=0)),flush=True)
