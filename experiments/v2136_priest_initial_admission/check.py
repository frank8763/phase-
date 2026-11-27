from pathlib import Path
import os,json,copy,hashlib,time
from gate import digest,inspect_request
assert os.sched_getaffinity(0)=={4}
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name
assert not(S/'RESULT.json').exists();p=R/'runs/v2122_priest_quiescent_handoff/vehicle/actual/PRIEST_OPTIMIZER_REQUEST.json';raw=p.read_bytes();r=json.loads(raw);author=r['port_identity']['author_sha256'];old=inspect_request(r,expected_sha256=digest(r),expected_author_sha256=author);assert old['disposition']=='ADAPTER_INITIAL_BOUNDARY_INCOMPATIBLE'and len(old['initial_obstacle_violations'])==50
new=copy.deepcopy(r);new['initial_state']=[0.,0.,0.,0.,0.,0.];new['static_points_world']=[[4.+i*.01,4.]for i in range(50)];new.pop('request_sha256');new['request_sha256']=digest(new);open_result=inspect_request(new,expected_sha256=digest(new),expected_author_sha256=author);assert open_result['mathematical_initial_boundary_compatible']and not open_result['optimizer_launch_authorized']
negative=[]
for name,fn in [('foreign_request',lambda:inspect_request(r,expected_sha256='0'*64,expected_author_sha256=author)),('foreign_author',lambda:inspect_request(r,expected_sha256=digest(r),expected_author_sha256='0'*64))]:
 try:fn()
 except AssertionError:negative.append(name)
 else:raise AssertionError(name)
assert hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
v=dict(passed=True,closed=True,software_only=True,models=0,optimizer_calls=0,physics=0,replay=0,new_formal_claims=0,original_real_request=old,synthetic_open_positive=open_result,negative_cases=negative,original_input_sha256=hashlib.sha256(raw).hexdigest(),production_guard_still_requires_future_owner_integration=True,unix=time.time());out=json.dumps(v,indent=2)+'\n';assert len(out.encode())<128*1024;(S/'RESULT.json').write_text(out);print(out)
