"""Zero-model tests of the changed task-count interface and acceptance stop gates."""
import ast
import json
import subprocess
import sys
from pathlib import Path
from evidence_rules import dump, main_gate, read

repo = Path(__file__).resolve().parents[2]
root = repo/'runs/dynamic_acceptance_20261105'
assert not (root/'ZERO_MODEL_QUALIFICATION.json').exists()
for name in ['dynamic_acceptance_20261105','v821_norm_route_development','v822_norm_dynamic_confirmation']:
    for p in (repo/'experiments'/name).glob('*.py'): ast.parse(p.read_text())
tasks = read(repo/'experiments/v822_norm_dynamic_confirmation/TASK_LIST.json')
assert len(tasks)==24 and len({x['seed'] for x in tasks})==24
assert [x['slot'] for x in tasks]==list(range(1,25))
assert sorted(x['seed'] for x in tasks)==list(range(10060001,10060025))
assert all(sum(x['case_id']==case for x in tasks)==8 for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST'])
assert all(sum(x['initial_axis_motion_direction']==direction for x in tasks)==12 for direction in ['POSITIVE_AXIS','NEGATIVE_AXIS'])
def records(failures=(),count=24):
    return [dict(role='MAIN',task=t,physical_passed=True,functional_passed=i not in failures) for i,t in enumerate(tasks[:count])]
assert main_gate(tasks,records(),True)['passed']
assert main_gate(tasks,records([1]),True)['passed']
assert not main_gate(tasks,records([1,2]),True)['passed']
assert not main_gate(tasks,records(count=23),True)['passed']
assert main_gate(tasks,records(count=23),True)['success_rate'] is None
permuted = records();permuted[0],permuted[1]=permuted[1],permuted[0]
assert not main_gate(tasks,permuted,True)['passed']
dev = read(repo/'experiments/v821_norm_route_development/TASK_LIST.json')
assert [x['seed'] for x in dev]==[10010002,10010003]
assert main_gate(dev,[dict(role='MAIN',task=t,physical_passed=True,functional_passed=True) for t in dev],False)['passed']
assert not main_gate(dev,[dict(role='MAIN',task=t,physical_passed=True,functional_passed=i==0) for i,t in enumerate(dev)],False)['passed']
# These are clearly labeled original persisted t0 records, never new preflights.
view = root/'old_t0_interface_view'
view.mkdir(exist_ok=False)
old = read(repo/'runs/v812_soft_global_reference/development01/PREFLIGHTS.json')
assert [x['task'] for x in old[1:]]==dev
dump(view/'PREFLIGHTS.json',old[1:])
dump(view/'VIEW_ONLY.json',dict(source='V812 persisted original two t0 records',new_task_initializations=0,not_new_preflights=True))
script = repo/'experiments/v821_norm_route_development/audit_field_preflight.py'
code = "import mujoco,runpy,sys\ndef denied(*a,**k):raise RuntimeError('MODEL_OR_INTEGRATION_FORBIDDEN_IN_QUALIFICATION')\nmujoco.MjModel.from_xml_path=denied\nmujoco.MjModel.from_binary_path=denied\nmujoco.MjModel.from_xml_string=denied\nmujoco.MjData=denied\nmujoco.mj_step=denied\nmujoco.mj_step1=denied\nmujoco.mj_step2=denied\nsys.argv=[sys.argv[1],sys.argv[2]]\nrunpy.run_path(sys.argv[0],run_name='__main__')\n"
p = subprocess.run([sys.executable,'-B','-c',code,str(script),str(view)],cwd=repo,capture_output=True,text=True,timeout=120)
(root/'zero_model_t0_interface.console').write_text(p.stdout+p.stderr)
assert p.returncode==0,(p.returncode,p.stderr[-2500:])
assert read(view/'PREFLIGHT_INDEPENDENT_AUDIT.json')['status']=='PASS'
result = dict(passed=True,status='ZERO_MODEL_BOUNDARY_AND_GATE_QUALIFICATION_PASS',old_t0_interfaces=2,
              new_confirmation_tasks_locked=24,new_confirmation_preflights=0,
              positive_and_negative_gate_cases=8,runner_only_namespace_changed=True,
              new_models=0,new_integrations=0,not_navigation_or_acceptance_success=True)
dump(root/'ZERO_MODEL_QUALIFICATION.json',result)
print(json.dumps(result))
