"""Reproduce exact lexical bug without importing Torch or executing old numerical tail."""
from common import *
import ast,copy,importlib.abc,types,traceback,symtable
assert os.sched_getaffinity(0)=={0}and not(S/'PRELUDE_BINDING_PROOF.json').exists()
old=R/'experiments/v2165_sccr_dual_actor_component/worker.py';new=C/'worker.py';cases=[]
for label,p in [('original',old),('corrected',new)]:
 tree=ast.parse(p.read_text());fn=copy.deepcopy(next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main'))
 index=next(i for i,x in enumerate(fn.body)if isinstance(x,ast.ClassDef)and x.name=='Ban')
 # Keep ALL original tail AST unreachable: its local symbol bindings still
 # affect the genuine prelude. Truncating the tail would hide the originalbug.
 fn.body.insert(index+1,ast.Return(value=ast.Constant(value='PRE_NETWORK_PRELUDE_COMPLETE')))
 calls=[];space=dict(authority=lambda:({},{}),O=S/'software_not_a_worker',dump=lambda p,v:calls.append(dict(path=str(p),value=v)),os=os,time=time,importlib=importlib)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(p),'exec'),space)
 failure=None;value=None
 try:value=space['main']()
 except BaseException as e:failure=type(e).__name__+':'+str(e)
 if label=='original':assert failure and failure.startswith('UnboundLocalError:')and'importlib'in failure
 else:assert failure is None and value=='PRE_NETWORK_PRELUDE_COMPLETE'
 assert len(calls)==1 and 'torch'not in sys.modules
 symbols=symtable.symtable(p.read_text(),str(p),'exec');main=next(x for x in symbols.get_children()if x.get_name()=='main');binding=main.lookup('importlib')
 cases.append(dict(case=label,source_sha256=sha(p),error=failure,returned=value,importlib_is_local=binding.is_local(),importlib_is_global=binding.is_global(),unreachable_original_tail_retained=True))
assert cases[0]['importlib_is_local']and cases[1]['importlib_is_global']
expected=old.read_text().replace('import numpy as np,torch,importlib.metadata','import numpy as np,torch\n from importlib.metadata import version as package_version').replace("importlib.metadata.version('stable-baselines3')","package_version('stable-baselines3')")
assert expected==new.read_text()
v=dict(passed=True,closed=True,red_old_and_green_corrected=True,cases=cases,only_two_import_spelling_changes=True,Torch_imports=0,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,physics=0,replay=0,old_failed_source_not_edited_or_reexecuted=True);dump(S/'PRELUDE_BINDING_PROOF.json',v);print(json.dumps(v))
