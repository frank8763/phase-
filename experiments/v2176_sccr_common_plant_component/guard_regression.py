"""Actual original history guard, explicit synthetic files, no numerical imports."""
from pathlib import Path
import os,sys,json,hashlib,ast,types,time
from source_scope import SourceScope,sha,PROTECTED
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;S.mkdir(exist_ok=True)
assert os.sched_getaffinity(0)=={0}and not(S/'GUARD_REGRESSION.json').exists()
root=S/'software_guard';out=root/'allowed';old=root/'history';out.mkdir(parents=True,exist_ok=False);old.mkdir()
safe=out/'source_module.txt';safe.write_text('EXPLICIT SOFTWARE SOURCE FIXTURE, NO MODEL')
historical=old/'BODY_COMMANDS.json';historical.write_text('EXPLICIT SYNTHETIC HISTORICAL-NAME FIXTURE, NO CONTROLS')
files={str(p.relative_to(root)):sha(p)for p in [safe,historical]};binding=tuple(hashlib.sha256(x.encode()).hexdigest()for x in ['freeze','admission','task'])
instances=[SourceScope(root)for _ in range(5)]
for scope in instances:assert scope.verify(files,binding=binding,initialization_started=False)==files
original=R/'experiments/v1180_fresh_recovery_chain/chain_tools.py';code=compile(original.read_text(),str(original),'exec',dont_inherit=True);fns=[x for x in code.co_consts if isinstance(x,types.CodeType)and x.co_name=='history_guard'];assert len(fns)==1
fn=types.FunctionType(fns[0],dict(Path=Path,os=os,sys=sys),'history_guard');fn(out)
negative=[]
def refused(label,fn,wanted):
 try:fn()
 except AssertionError as e:assert wanted in str(e),(label,str(e));negative.append(dict(case=label,error=str(e)))
 else:raise AssertionError('SOURCE_STAGE_NEGATIVE_ACCEPTED:'+label)
refused('old_live_all_source_rehash',lambda:all(sha(root/n)==h for n,h in files.items()),'FRESH_HISTORY_READ_FORBIDDEN BODY_COMMANDS.json')
assert instances[0].verify(files,binding=binding,initialization_started=True)==files
refused('original_direct_history_read_still_forbidden',lambda:historical.read_bytes(),'FRESH_HISTORY_READ_FORBIDDEN BODY_COMMANDS.json')
refused('cold_bootstrap_after_initializer',lambda:SourceScope(root).verify(files,binding=binding,initialization_started=True),'SOURCE_BOOTSTRAP_AFTER_INITIALIZER_FORBIDDEN')
for i,name in enumerate(['freeze','admission','task']):
 changed=list(binding);changed[i]='f'*64;refused('changed_'+name+'_authority',lambda b=tuple(changed):instances[1].verify(files,binding=b,initialization_started=True),'SOURCE_BOOTSTRAP_AUTHORITY_CHANGED')
changed=dict(files);changed[next(iter(changed))]='a'*64;refused('changed_complete_manifest',lambda:instances[2].verify(changed,binding=binding,initialization_started=True),'SOURCE_BOOTSTRAP_MANIFEST_CHANGED')
safe.write_text('EXPLICIT CHANGED RUNTIME SOURCE FIXTURE')
refused('runtime_source_changed',lambda:instances[3].verify(files,binding=binding,initialization_started=True),'RUNTIME_READABLE_SOURCE_HASH_CHANGED')
try:instances[4]._files['new']='a'*64
except TypeError:negative.append(dict(case='immutable_cached_manifest',error='TypeError'))
else:raise AssertionError('CACHED_HASH_METADATA_MUTABLE')
assert 'torch'not in sys.modules and 'mujoco'not in sys.modules
v=dict(passed=True,closed=True,scope='ACTUAL_ORIGINAL_HISTORY_GUARD_SOURCE_STAGE_REGRESSION_SOFTWARE_ONLY',old_live_rehash_red=True,prebootstrap_runtime_source_metadata_green=True,original_guard_unchanged_and_direct_history_read_still_red=True,negative_cases=negative,cached_objects_only_path_SHA_strings=True,source_SHA256={str(p.relative_to(R)):sha(p)for p in [Path(__file__),C/'source_scope.py',original]},models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,old_scientific_qualification_reexecuted=False,source_once_claimed=False)
(S/'GUARD_REGRESSION.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:x for k,x in v.items()if k not in ['negative_cases','source_SHA256']}))
