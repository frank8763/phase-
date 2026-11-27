"""Actual queue and complete generated recovery-path software tests."""
from pathlib import Path
import ast,hashlib,json,os,subprocess,sys,time,types,traceback
import evidence as e
R=e.R;C=e.C;S=e.ROOT
def main():
 assert os.sched_getaffinity(0)=={4};F=S/'software_02';F.mkdir(exist_ok=False)
 result=dict(passed=False,closed=False,models=0,DLLs=0,solvers=0,physics=0,replay=0)
 try:
  generated=[]
  # Exercise the actual deliver transformation for normal and both recovery episodes.
  original_scope=e.scope
  for episode in [0,1,2]:
   folder=F/('transport_'+str(episode));folder.mkdir();fake=folder/'archive_scope';fake.mkdir()
   if episode:
    previous=fake/('remote_delivery'if episode==1 else'remote_delivery_retry_1');(previous/'http_receipts').mkdir(parents=True)
    (previous/'RESULT.json').write_text('{"closed":true,"passed":false}')
    for i in range(6):(previous/'http_receipts'/(str(i)+'.json')).write_text('{"call":1,"method":"GET","passed":false}')
   e.scope=lambda rid:(folder,fake)
   text=e.deliver('common_08__SVGMPPI',episode=episode,preview=True);tree=ast.parse(text);compile(tree,'<actual-generated-transport>','exec')
   assert "\\n        if not alias.exists():"not in text
   generated.append(dict(episode=episode,complete_module_compiles=True,sha256=hashlib.sha256(text.encode()).hexdigest()))
   # Execute the actual generated alias line and conditional, with exact and corrupt aliases.
   fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main')
   statements=next(n.body for n in ast.walk(fn)if isinstance(n,ast.Try)and any(isinstance(x,ast.Assign)and isinstance(x.targets[0],ast.Name)and x.targets[0].id=='alias'for x in n.body))
   start=next(i for i,n in enumerate(statements)if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='alias')
   block=ast.Module(body=statements[start:start+3],type_ignores=[]);assert isinstance(block.body[1],ast.Assert)and isinstance(block.body[2],ast.If)
   (fake/'ARCHIVE_INDEX.json').write_text('{"same":"bytes"}')
   scope=dict(D=fake,rid='common_08__SVGMPPI',runtime=True,sha=e.sha);code=compile(block,'<actual-alias-branch>','exec')
   exec(code,scope);exec(code,scope);scope['alias'].write_text('CORRUPT')
   try:exec(code,scope);raise RuntimeError('CORRUPT_ALIAS_NOT_REJECTED')
   except AssertionError:pass
  e.scope=original_scope
  tests=[]
  for label,technical,cutoff,transport_failure in [('functional_continues',False,False,False),('technical_stops',True,False,False),('budget_stops_next',False,True,False),('transport_stops_without_duplicate_owner',False,False,True)]:
   root=F/label;root.mkdir();(root/'owner.lock').touch();(root/'POST_SOURCE_STORAGE_BARRIER.json').write_text('{"passed":true}');(root/'SOURCE_FREEZE.json').write_text('{"files":{}}');study=root/'study';(study/'rounds').mkdir(parents=True)
   (root/'AUTHORIZATION.json').write_text(json.dumps(dict(absolute_end_unix=time.time()+20000,maximum_campaign_s=20000,finite_formal_assignments=['common_08__SVGMPPI','common_09__SVGMPPI'])))
   camp=e.load('queue_fixture_'+label,C/'campaign.py');camp.S=root;camp.STUDY=study;elapsed=[0.];real=time.time
   camp.time=types.SimpleNamespace(time=lambda:real()+elapsed[0],monotonic=lambda:time.monotonic()+elapsed[0],sleep=lambda _:None)
   camp.e=types.SimpleNamespace(read=lambda p:json.loads(Path(p).read_text()),put=lambda p,v:Path(p).write_text(json.dumps(v)),sha=e.sha)
   ran=[];closed=[];summaries=[]
   def process(label,argv,cap,env=None,cpu=5,rid=None):
    ran.append(rid);o=study/'rounds'/rid;o.mkdir();(o/'COMPLETION.json').write_text('{"closed":true}')
    if cutoff:elapsed[0]=13000.
    return 1
   def close(rid):
    if transport_failure:raise AssertionError('RUNTIME_FULL_REMOTE_BARRIER_FAILED')
    closed.append(rid);return dict(round_id=rid,qualified_success=False,valid_finite_method_refusal=not technical,technical_censor=technical)
   camp.run_process=process;camp.close_case=close;camp.checkpoint=lambda *a:None;camp.summary=lambda rows,why:summaries.append((rows,why));camp.main()
   assert len(ran)==(2 if label=='functional_continues'else 1)and len(summaries)==1
   tests.append(dict(name=label,actual_campaign_main=True,owners=len(ran),closed=len(closed),stop_reason=summaries[0][1]))
  # Actual close_case retry loop, with recorded first-GET failures and no remote mutations.
  root=F/'retry_loop';root.mkdir();study=root/'study';o=study/'rounds/common_08__SVGMPPI';o.mkdir(parents=True);(o/'COMPLETION.json').write_text('{"closed":true,"passed":false}')
  camp=e.load('actual_three_episode_loop',C/'campaign.py');camp.S=root;camp.STUDY=study;calls=[];waits=[]
  def process(label,args,cap,env=None,**kw):
   if '_remote_'in label:
    ep=int(env['PHASE_TRANSFER_EPISODE']);calls.append(ep);t=root/'runtime_archives/common_08__SVGMPPI'/('remote_delivery'if ep==0 else'remote_delivery_retry_'+str(ep));(t/'http_receipts').mkdir(parents=True)
    (t/'RESULT.json').write_text('{"closed":true,"passed":false}')
    for i in range(6):(t/'http_receipts'/(str(i)+'.json')).write_text('{"call":1,"method":"GET","passed":false}')
    return 1
   return 0
  camp.run_process=process;camp.backoff=lambda delay,rid:waits.append(delay)
  try:camp.close_case('common_08__SVGMPPI');raise RuntimeError('EXPECTED_BOUNDED_STOP')
  except AssertionError as x:assert str(x)=='RUNTIME_FULL_REMOTE_BARRIER_FAILED'
  assert calls==[0,1,2]and waits==[30,120]
  bad=root/'runtime_archives/common_08__SVGMPPI/remote_delivery/http_receipts/0.json';bad.write_text('{"call":2,"method":"POST","passed":false}');assert not camp.premutation_failed(bad.parent.parent)
  same=[];old=R/'experiments/v2099_svg_direct_array_scope';excluded={'context.py','pilot_entry.py','run_phase.py','queue_storage.py','reserved_census.py','reservation.py','evidence.py','software_checks.py','qualify_source.py','owner.py'}
  for p in old.glob('*.py'):
   if p.name not in excluded and(C/p.name).exists():assert(C/p.name).read_bytes()==p.read_bytes();same.append(p.name)
  assert(C/'owner.py').read_bytes()==(old/'owner.py').read_bytes()
  for script in ['pilot_entry.py','run_phase.py']:
   p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/script)],cwd=R,env=dict(os.environ,PHASE_COMMON_ASSIGNMENT='common_08__SVGMPPI',PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'NOT_ADMITTED'in p.stderr
  for p in C.glob('*.py'):ast.parse(p.read_text())
  result.update(passed=True,complete_generated_transport_tests=generated,actual_queue_tests=tests,three_premutation_only_episodes_verified=True,uncertain_write_retry_rejected=True,exact_alias_reused_corrupt_alias_rejected=True,unchanged_numerical_modules=same,original_owner_byte_exact=True,unadmitted_model_entries_refused=True)
 except BaseException as x:result.update(first_error=repr(x),traceback=traceback.format_exc())
 finally:result['closed']=True;e.put(S/'SOFTWARE_CHECK_PROOF.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
