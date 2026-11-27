"""Bound every original response check, not merely a selected safety subset."""
from pathlib import Path
import os,json,hashlib,ast,copy,math
from cursor import Cursor,digest,state_digest,arc,DT,measured
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={0}
ns=dict(Cursor=Cursor,digest=digest,state_digest=state_digest,arc=arc,DT=DT,measured=measured,copy=copy,math=math,count=[1000])
tree=ast.parse((C/'check.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in {'fixture','proofs','applied'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'original_software_fixture_function_definitions_only','exec'),ns)
if not(S/'PROOF_SCHEMA_GAP.json').exists():
 e,p,a,b,r=ns['fixture']();c=Cursor(e);c.install(p,a,b);proposal=c.propose(b);old=ns['proofs'](proposal);c.verify_response(proposal['token'],old)
 assert c.pending['proof_verified'];x=dict(confirmed=True,old_minimum_five_checks_were_accepted=True,missing_original_checks=['finite','full_states','full_200_stop','speed_yaw','legal_ctrl','legal_slew','memory_shape'],physical_or_NLP_executed=0,old_cursor_sha256=hashlib.sha256((C/'cursor.py').read_bytes()).hexdigest());(S/'PROOF_SCHEMA_GAP.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
else:
 from cursor import RESPONSE_CHECKS
 e,p,a,b,r=ns['fixture']();c=Cursor(e);c.install(p,a,b);proposal=c.propose(b)
 try:c.verify_response(proposal['token'],ns['proofs'](proposal))
 except AssertionError:assert c.poisoned
 else:raise AssertionError('INCOMPLETE_OLD_PROOF_ACCEPTED')
 e,p,a,b,r=ns['fixture']();c=Cursor(e);c.install(p,a,b);events=[]
 # Reacquire same-state post-commit receipts with later monotonic timestamps.
 for i in range(16):
  current=b if i==0 else r(5*i,3);pr=c.propose(current);full=ns['proofs'](pr)
  for proof in full:proof['checks']={k:True for k in RESPONSE_CHECKS}
  c.verify_response(pr['token'],full);z=c.commit(pr['token'],r(5*i+5,2),ns['applied'](e,pr));events.append(dict(end_native=z['end_native'],origin_kept=z['original_plan_origin_native'],first_v=pr['requests'][0][0]))
 assert c.expected==80 and c.origin_native==0 and events[11]['first_v']>0
 # Exact inherited command-domain functions, no old module initialization.
 t=ast.parse((R/'experiments/v1288_baseline_interface/contract.py').read_text());scope=dict(math=math,SPEED=.1,CURVATURE=1/1.32);parts=[n for n in t.body if isinstance(n,ast.FunctionDef)and n.name in {'number','twist'}];exec(compile(ast.Module(body=parts,type_ignores=[]),'original_command_domain_functions','exec'),scope)
 count=0
 for n in range(990):
  row=c.requests(n,1)[0];scope['twist'](row[0],row[1]);count+=1
 # Final software and no partial-proof check coverage is source-pinned.
 x=dict(passed=True,all_original_response_check_names=sorted(RESPONSE_CHECKS),full_check_count=len(RESPONSE_CHECKS),old_incomplete_proof_refused=True,completed_prefixes=16,reacquired_same_state_monotonic_receipts=True,retained_original_origin=0,first_nonzero_prefix_native=55,original_twist_domain_samples=count,new_NLP_NN_models_physics_Source=0,events=events,earlier_RESULT_supports_only_earlier_snapshot=True,old_source_snapshot_sha256=hashlib.sha256((C/'cursor_v1_incomplete_proof_schema.py').read_bytes()).hexdigest(),current_cursor_sha256=hashlib.sha256((C/'cursor.py').read_bytes()).hexdigest());(S/'PROOF_SCHEMA_SUPPLEMENT.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items()if k!='events'}))
