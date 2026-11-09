"""Output-only wrapper around the immutable V950 scientific component worker."""
import importlib.util
import json
import sys
from pathlib import Path

CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]
BASE=ROOT/'experiments/v950_steering_response'
sys.path.insert(0,str(BASE))
spec=importlib.util.spec_from_file_location('frozen_v950_component_worker',BASE/'worker.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)


def target_path(path,case):
    path=Path(path)
    operation=ROOT/'runs/v951_component_output_entry'
    if path.parent==operation and path.name.startswith('CASE_')and path.name.endswith('_RESULT.json'):
        return case/'QUALIFICATION.json'
    assert path.resolve().is_relative_to(case.resolve()),'OUTPUT_OUTSIDE_REGISTERED_CASE'
    return path


def main():
    sys.path.insert(0,str(CODE))
    from entry_authority import authorized
    index=int(sys.argv[1]);assert 1<=index<=18,'FIRST_CASE_MUST_NOT_RERUN'
    task=json.loads((BASE/'TASKS.json').read_text())[index]
    case=ROOT/task['output']
    engine.OUT=ROOT/'runs/v951_component_output_entry'
    engine.authorized=authorized
    def write(path,data):
        target_path(path,case).write_text(json.dumps(data,indent=2)+'\n')
    engine.dump=write
    return engine.main()


if __name__=='__main__':sys.exit(main())
