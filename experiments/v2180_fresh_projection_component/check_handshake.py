"""Concrete one-query binding tests only; no worker, numerical library or plant."""
from pathlib import Path
import json,hashlib,copy,os,datetime
from handshake import bind,verify,digest
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={0}and not(S/'HANDSHAKE_SOFTWARE.json').exists()
a=dict(scope='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY',maximum_queries=1,models_authorized=False,run_id='SYNTHETIC_SOFTWARE_ONLY',query_nonce='SYNTHETIC_CURRENT_NONCE_NOT_ACTUAL',source_freeze_sha256='a'*64,worker_sha256='b'*64)
raw=(json.dumps(a,ensure_ascii=False,separators=(',',':'))+'\n').encode();f=dict(episode_id=a['run_id'],query_nonce=a['query_nonce'],source_freeze_sha256=a['source_freeze_sha256'],query_sequence=0,numerical_admission_sha256='unset',receipt=dict(native=0,body=[-4.,-2.,0.,0.,0.]))
f,c=bind(raw,f);assert verify(raw,c,f);assert f['numerical_admission_sha256']==hashlib.sha256(raw).hexdigest()and c['first_input_sha256']==digest(f)
negative=[]
for name,mutate in [
 ('admission_bytes_changed',lambda z,c,f:z.__setitem__('worker_sha256','c'*64)),
 ('query_changed',lambda z,c,f:f['receipt']['body'].__setitem__(0,-3.)),
 ('querynonce',lambda z,c,f:f.__setitem__('query_nonce','old-closed-query')),
 ('foreign_episode',lambda z,c,f:f.__setitem__('episode_id','old-closed-episode')),
 ('claim_admission_sha',lambda z,c,f:c.__setitem__('admission_sha256','f'*64)),
 ('claim_input_sha',lambda z,c,f:c.__setitem__('first_input_sha256','f'*64)),
 ('extra_queries',lambda z,c,f:c.__setitem__('maximum_queries',2)),
 ('cyclic_admission_design',lambda z,c,f:z.__setitem__('first_input_sha256','f'*64)),
]:
 z=copy.deepcopy(a);cc=copy.deepcopy(c);ff=copy.deepcopy(f);mutate(z,cc,ff);rr=(json.dumps(z,ensure_ascii=False,separators=(',',':'))+'\n').encode()
 try:verify(rr,cc,ff)
 except AssertionError as e:negative.append(dict(name=name,error=repr(e)))
 else:raise AssertionError('EXPECTED_BINDING_REFUSAL:'+name)
x=dict(passed=True,binding_graph=['immutable admission file bytes SHA','frame includes admission SHA','separate pre-spawn ONCE claim binds frame SHA'],self_referential_hash_cycle_removed_before_any_Source_or_worker=True,negative_cases=negative,negative_count=len(negative),synthetic_only=True,actual_worker_NLP_models_physics_Source=0,source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [C/'handshake.py',C/'check_handshake.py',C/'peer_guard.py',C/'peer_entry.py']},created_at=datetime.datetime.now().astimezone().isoformat());(S/'HANDSHAKE_SOFTWARE.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items()if k not in ['negative_cases','source_sha256']}))
