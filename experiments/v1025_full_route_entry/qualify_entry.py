"""Exercise the exact corrected Popen argument expression with guard closed."""
import ast,hashlib,json,subprocess,sys
from pathlib import Path
N=Path(__file__).resolve().parent;R=N.parents[1];C=R/'experiments/v1024_full_route_execution';O=R/'runs/v1025_full_route_entry'
source=(N/'campaign.py').read_text();tree=ast.parse(source);node=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='Popen')
task=json.loads((C/'TASKS.json').read_text())[0];rp=O/'never_authorized.json';args=eval(compile(ast.Expression(node.args[0]),str(N/'campaign.py'),'eval'),dict(str=str,R=R,C=C,task=task,rp=rp))
assert args[2]==str(C/'TASKS_static_we.json')and Path(args[2]).is_file()
assert (R/'REVIEW_PENDING').exists();p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=5)
assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr,'GUARD_NOT_BEFORE_MODELS'
original=ast.parse((C/'campaign.py').read_text());old=next(n for n in ast.walk(original)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='Popen')
try:eval(compile(ast.Expression(old.args[0]),str(C/'campaign.py'),'eval'),dict(str=str,R=R,C=C,task=task,rp=rp))
except TypeError:original_red=True
else:raise AssertionError('ORIGINAL_ERROR_NOT_REPRODUCED')
old_freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(hashlib.sha256((R/path).read_bytes()).hexdigest()==sha for path,sha in old_freeze['files'].items())
assert (O/'ROUND_WINDOW.json').read_bytes()==(R/'runs/v1024_full_route_execution/ROUND_WINDOW.json').read_bytes()
assert not (R/'runs/v858_nav2_verified/v1024').exists()
out=dict(passed=True,original_exact_command_expression_red=original_red,new_exact_command_expression_green=True,production_run_phase_guard_checked_before_model=True,old_all_scientific_and_worker_sources_byte_identical=True,window_original_bytes_unchanged=True,old_failure_preserved=True,new_models=0,integrations=0)
(O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
