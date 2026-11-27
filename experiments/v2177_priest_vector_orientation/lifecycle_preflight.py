"""Real owner and launch refuse missing Source; no actual Popen/numerical work."""
from context import R,C,ROOT,O,put
import subprocess,os,json,ast
assert os.sched_getaffinity(0)=={5}and not(ROOT/'SOURCE_ONCE.json').exists()and not(ROOT/'LIFECYCLE_SOFTWARE_PROOF.json').exists()
rows=[]
for n in ['owner.py','launch.py']:
 q=subprocess.run(['taskset','-c','5','python3','-B',str(C/n)],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=15)
 assert q.returncode!=0 and 'POST_SOURCE_STORAGE_BARRIER.json'in q.stderr and not(ROOT/'LAUNCH_ONCE.json').exists()and not(O/'OWNER_ONCE.json').exists();rows.append(dict(entry=n,returncode=q.returncode,stderr=q.stderr))
for n in ['owner.lock','launch.lock']:assert(ROOT/n).is_file()
for p in C.glob('*.py'):ast.parse(p.read_text())
put(ROOT/'LIFECYCLE_SOFTWARE_PROOF.json',dict(passed=True,real_cli_refusals=rows,all_source_AST=True,locks_precreated=True,actual_owner_spawns=0,actual_NLP_models=0));print(json.dumps(dict(passed=True,real_CLI_refusals=2,actual_NLP_models=0)))
