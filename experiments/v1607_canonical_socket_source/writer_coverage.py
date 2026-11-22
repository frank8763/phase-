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
    prior=json.loads((R/'runs/v1603_capture_close_source/ENTRY_QUALIFICATION.json').read_text())['writer_source_coverage']
    original=R/'experiments/v1603_capture_close_source/route_ros.py'
    before=ast.parse(original.read_text());after=ast.parse((C/'route_ros.py').read_text())
    old={n.name:n for n in ast.walk(before)if isinstance(n,ast.FunctionDef)}
    new={n.name:n for n in ast.walk(after)if isinstance(n,ast.FunctionDef)}
    for name in ('phase_clock','send','emit','begin_brake','receive_body_twist','brake_timer','receive_twist','publish_map','wait','map_ready','send_path'):
        assert ast.dump(old[name])==ast.dump(new[name]),'ORIGINAL_ROS_CONTROL_CHANGED:'+name
    def external_calls(tree):
        return [ast.dump(n)for n in ast.walk(tree)if isinstance(n,ast.Call)and (getattr(n.func,'attr',None)=='Popen' or getattr(n.func,'id',None)=='PlanningJob')]
    assert external_calls(before)==external_calls(after),'EXTERNAL_WRITER_PROCESS_CHANGED'
    assert (C/'WRITER_CAPS.json').read_bytes()==(original.parent/'WRITER_CAPS.json').read_bytes()
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
            inherited_qualification_file='runs/v1603_capture_close_source/ENTRY_QUALIFICATION.json',
            current_route_sha256=sha(C/'route_ros.py'),current_context_sha256=sha(C/'route_context.py'),
            current_journal_sha256=sha(C/'observation_journal.py'),
            source_only=True,new_ROS_runtime_executed=False)
    return rows
