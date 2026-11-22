"""Exact inherited writer proof; only disclosed route/provider changes."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tree=lambda p:ast.dump(ast.parse(p.read_text()),include_attributes=False)


def coverage(source):
    prior=json.loads((R/'runs/v1599_readonly_context_durability/ENTRY_QUALIFICATION.json').read_text())['writer_source_coverage']
    original=R/'experiments/v1599_readonly_context_durability/route_ros.py'
    expected=original.read_text().replace("R/'experiments/v1574_current_owner_capture/causal_provider.py'","C/'causal_provider.py'").replace("R/'experiments/v1574_current_owner_capture/event_session.py'","C/'event_session.py'")
    expected=expected.replace('from causal_occupancy import CausalBall',"_close_spec=importlib.util.spec_from_file_location('v1602_actual_source_closure',C/'provider_close.py');_source_close=importlib.util.module_from_spec(_close_spec);_close_spec.loader.exec_module(_source_close)\nfrom causal_occupancy import CausalBall")
    expected=expected.replace("send(dict(kind='stop',run_id=task['run_id'],passed=result['passed'],issued_at=time.monotonic()))","source_journal_close=_source_close.close(tracker,result,lambda:send(dict(kind='stop',run_id=task['run_id'],passed=result['passed'],issued_at=time.monotonic())))")
    expected=expected.replace("artifacts=[('ROS_COMMANDS.json',rows)","artifacts=[('CAUSAL_SOURCE_JOURNAL_CLOSED.json',source_journal_close),('ROS_COMMANDS.json',rows)")
    assert ast.dump(ast.parse(expected),include_attributes=False)==tree(C/'route_ros.py'),'UNDECLARED_ROS_CHANGE'
    # The original ACTUAL_ROS/planner/controller writer wrapper and subprocess
    # invocation are byte-identical. New context dump is still inside that
    # wrapper; it has no direct child or descriptor escape.
    context=ast.parse((C/'route_context.py').read_text())
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom))and any(a.name in {'subprocess','ctypes'}for a in n.names)for n in ast.walk(context))
    dump=next(n for n in context.body if isinstance(n,ast.FunctionDef)and n.name=='dump')
    assert any(isinstance(n,ast.Assert)and '4 * 1024 ** 2'in ast.unparse(n)for n in ast.walk(dump))
    assert any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='open'and any(isinstance(a,ast.Constant)and a.value=='xb'for a in n.args)for n in ast.walk(dump))
    calls=[n.func.attr for n in ast.walk(dump)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
    assert 'replace'in calls and calls.count('fsync')==2
    route=(C/'route_ros.py').read_text()
    assert "else _entry.run(main)"in route and "with boundary"in (R/'experiments/v1479_retirement_scope_binding/entry_boundary.py').read_text()
    assert "env['PHASE_BOUNDED_WRITER_ROLE']='PLANNER'"in (R/'experiments/v1479_retirement_scope_binding/planning_job.py').read_text()
    assert 'source_hook_coverage_qualified'in (C/'supervisor.py').read_text()
    assert 'quota.charge_write'in (C/'native_driver.py').read_text()
    assert 'Scope(parent=parent_boundary'in (C/'transaction.py').read_text()
    assert 'Scope(parent=self.quota.output_boundary'in (C/'lifecycle.py').read_text()
    rows={}
    for role in ('ACTUAL_ROS','PLANNER','SUPERVISOR_LOG'):
        row=prior[role];assert row is True
        rows[role]=dict(source_hook_coverage_qualified=True,inherited_proof=row,
            inherited_qualification_file='runs/v1599_readonly_context_durability/ENTRY_QUALIFICATION.json',
            current_route_sha256=sha(C/'route_ros.py'),current_context_sha256=sha(C/'route_context.py'),
            current_journal_sha256=sha(C/'observation_journal.py'),
            source_only=True,new_ROS_runtime_executed=False)
    return rows
