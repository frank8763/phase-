"""Execute the actual factory write guard without importing or creating its model."""
import ast,json,os,sys
from pathlib import Path
OPS=Path(__file__).resolve().parent;R=OPS.parents[1];O=R/'runs/v909_output_continuation';BASE=R/'experiments/v909_timed_command_contract';OLD=R/'runs/v909_timed_command_contract';WRITABLE=R/'runs/v858_nav2_verified/v909/continuation_status'
tree=ast.parse((R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py').read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='write_guard')
scope=dict(Path=Path,os=os,OUT=R/'runs/v858_nav2_verified')
exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_factory_write_guard','exec'),scope);guard=scope['write_guard'];checks={}
try:guard('open',(str(OLD/'RESPONSE_00_RESULT.json'),None,os.O_WRONLY|os.O_CREAT))
except PermissionError:checks['exact_old_summary_path_reproduces_failure']=True
else:checks['exact_old_summary_path_reproduces_failure']=False
for name in ['RESPONSE_01_CLAIM.json','RESPONSE_01_RESULT.json','PLATFORM_PROGRESS.json']:
    guard('open',(str(WRITABLE/name),None,os.O_WRONLY|os.O_CREAT));checks[name+'_inside_factory_write_root']=True
guard('os.mkdir',(str(WRITABLE),0o755,-1));checks['status_directory_inside_factory_root']=True
old=ast.parse((BASE/'qualify_response.py').read_text())
checks['response_loop_unchanged_one_fixed_index']='for case in [tasks[index]]:'in(BASE/'qualify_response.py').read_text()
checks['first_case_fully_passed']=json.loads((R/'runs/v858_nav2_verified/v909/platform_00/QUALIFICATION.json').read_text())['passed']
checks['original_closed_failure_retained']=json.loads((OLD/'COMPLETION.json').read_text())['status']=='NOT_PASSED'
sys.path.insert(0,str(OPS));import entry
checks['same_frozen_response_only_output_binding']='m.O=WRITABLE' in(OPS/'entry.py').read_text() and 'm.C=' not in(OPS/'entry.py').read_text()
checks['all_operational_sources_parse']=all(ast.parse(p.read_text())is not None for p in OPS.glob('*.py'))
checks['no_executed_first_case_retry_gate']="1<=index<18"in(OPS/'entry.py').read_text()
proof=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,actual_write_guard_ast_used=True)
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof));assert proof['passed']
