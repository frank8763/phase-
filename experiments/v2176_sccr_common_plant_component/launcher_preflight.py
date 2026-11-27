"""Actual launcher main with an explicit fake Popen and isolated fixture roots."""
from context import R,C,SOURCE as S,read,put,load,sha
from pathlib import Path
import os,sys,time,json,types,copy
assert os.sched_getaffinity(0)=={5}and not(S/'LAUNCHER_PREFLIGHT.json').exists()
original=load('live_union_production_launcher_unadmitted',C/'launch.py')
try:original.check()
except AssertionError as e:assert str(e)=='SOURCE_REMOTE_RECOVERY_NOT_READY'
else:raise AssertionError('UNRECOVERED_SOURCE_LAUNCH_ACCEPTED')
root=S/'launcher_software';root.mkdir(exist_ok=False);fakeR=root/'repo';fakeS=fakeR/'runs/fixture';fakeO=fakeS/'components/SCCR';fakeO.mkdir(parents=True)
for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
 p=fakeR/n;p.parent.mkdir(parents=True,exist_ok=True);p.touch()
(fakeS/'dispatch.lock').touch();(fakeR/'REVIEW_PENDING').write_text('EXPLICIT SOFTWARE FIXTURE')
for n,x in [('POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True)),('CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(all_frozen_members_remote_chain_covered=True,source_commit='EXPLICIT_SOFTWARE_FIXTURE_NOT_GIT')),('SOURCE_FREEZE.json',dict(files={}))]:put(fakeS/n,x)
auth=dict(scope='SCCR_CP_SHARED_ROUTE_NONZERO_COMPONENT',absolute_deadline_unix=time.time()+9000,hard_stop_monotonic=time.monotonic()+9000,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
put(fakeS/'AUTHORIZATION.json',auth)
launcher=load('live_union_launcher_explicit_fixture',C/'launch.py');launcher.R=fakeR;launcher.S=fakeS;launcher.O=fakeO;launcher.C=C;launcher.predecessors_closed=lambda:True
realsha=launcher.sha;launcher.sha=lambda p:'4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'if p==fakeR/'REVIEW_PENDING'else realsha(p)
from reserved_census import admission
budget=admission();old=sys.modules.get('reserved_census');sys.modules['reserved_census']=types.SimpleNamespace(admission=lambda:budget)
calls=[]
def popen(argv,**kwargs):
 assert argv[-1]==str(C/'owner.py')and kwargs['start_new_session']and kwargs['env']['PHASE_FILTER_METHOD']=='SCCR'
 assert(fakeS/'DISPATCH_ONCE.json').exists();calls.append(dict(argv=argv,detached=True,explicit_stub_process=True));return types.SimpleNamespace(pid=os.getpid())
launcher.subprocess=types.SimpleNamespace(Popen=popen,DEVNULL=-3,STDOUT=-2)
def refuse(label,fn):
 before=len(calls)
 try:fn()
 except AssertionError:return dict(case=label,refused_before_Popen=len(calls)==before)
 raise AssertionError('LAUNCHER_NEGATIVE_ACCEPTED:'+label)
try:
 # Execute the real check/main body; only predecessor, filesystem, budget and
 # process boundary are explicit fixtures. No actual owner can be spawned.
 launcher.main();assert len(calls)==1 and read(fakeS/'LAUNCH_IDENTITY.json')['source_commit']=='EXPLICIT_SOFTWARE_FIXTURE_NOT_GIT'
 negatives=[refuse('duplicate_dispatch_once',launcher.main)]
 (fakeS/'DISPATCH_ONCE.json').unlink();(fakeS/'LAUNCH_IDENTITY.json').unlink()
 late=dict(auth,absolute_deadline_unix=time.time()+6800);put(fakeS/'AUTHORIZATION.json',late);negatives.append(refuse('wall_clock_reserve_exhausted',launcher.main))
 late=dict(auth,hard_stop_monotonic=time.monotonic()+6800);put(fakeS/'AUTHORIZATION.json',late);negatives.append(refuse('monotonic_reserve_exhausted',launcher.main))
 late=dict(auth,boot_id='EXPLICIT_WRONG_BOOT');put(fakeS/'AUTHORIZATION.json',late);negatives.append(refuse('wrong_boot',launcher.main))
 put(fakeS/'AUTHORIZATION.json',auth);put(fakeO/'COMPLETION.json',dict(closed=True));negatives.append(refuse('already_closed_component',launcher.main))
 assert len(calls)==1 and all(n['refused_before_Popen']for n in negatives)
 result=dict(passed=True,closed=True,scope='ACTUAL_LAUNCHER_BODY_WITH_EXPLICIT_SOFTWARE_FILESYSTEM_AND_POPEN_FIXTURE',production_missing_source_refused=True,cases=negatives,detached_stub_spawns=1,actual_process_spawns=0,models=0,NN_inference=0,renderer_constructors=0,physics=0,source_once_claimed=False,source_SHA256={str(p.relative_to(R)):sha(p)for p in [C/'launch.py',C/'owner.py',Path(__file__)]})
 put(S/'LAUNCHER_PREFLIGHT.json',result);print(json.dumps({k:v for k,v in result.items()if k!='source_SHA256'}))
finally:
 if old is None:sys.modules.pop('reserved_census',None)
 else:sys.modules['reserved_census']=old
