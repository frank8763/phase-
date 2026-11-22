"""New production CLI; missing authority is saved before physical binding."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1606_native_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def main():
    c.bootstrap();os.chdir(c.R)
    task=c.read(Path(sys.argv[1]));assert task in c.read(C/'TASKS.json')
    result=None
    try:
        lifecycle=c.load('v1606_real_lifecycle',C/'lifecycle.py')
        if not(c.O/'ROUND_WINDOW.json').exists():lifecycle.authorize(task,{})
        result=lifecycle.run(task,c.read(c.O/'ROUND_WINDOW.json'))
        return 0 if result['passed']and result['closed']and result['first_error']is None and result['secondary_errors']==[]else 1
    except BaseException as error:
        # No RESULT is fabricated over a partial native result. This separate
        # CLI record retains a real initialization attempt as unknown if no
        # native machine record could be saved.
        out=Path(task['output']);target=out if out.is_dir()else c.O/'unadmitted'
        target.mkdir(exist_ok=True)
        source=c.draft_sources();budgets=c.load('v1606_cli_bounded_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
        io=c.load('v1606_cli_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        writer=budgets.WriterBudget(target,role='PLANNER',maximum_bytes=1024**2,source_identity=c.sha(C/'native_entry.py'))
        value=dict(passed=False,closed=True,first_error=repr(error),traceback=traceback.format_exc(),
            source_binding_before_factory=True,actual_counts_unknown=(out/'INITIALIZATION_ATTEMPT.json').exists(),
            no_runtime_success_inferred=True,whole_route_passed=False)
        with io.OutputBoundary(target,writer.reserve):c.put(target/'CLI_REFUSAL.json',value)
        print(json.dumps(dict(passed=False,closed=True,first_error=repr(error))))
        return 1


if __name__=='__main__':raise SystemExit(main())
