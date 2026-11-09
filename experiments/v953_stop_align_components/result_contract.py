"""Child case-only writes; parent operation metadata. No factory/ROS/model imports."""
import json
from pathlib import Path

PREFIX='PHASE_COMPONENT_RESULT '


def save_child(case,result):
    case=Path(case)
    if case.is_dir():
        (case/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(PREFIX+json.dumps(result,separators=(',',':')),flush=True)


def read_parent(console,case):
    lines=[line[len(PREFIX):]for line in Path(console).read_text().splitlines()if line.startswith(PREFIX)]
    assert len(lines)==1,'EXACTLY_ONE_CHILD_RESULT_REQUIRED'
    result=json.loads(lines[0]);path=Path(case)/'QUALIFICATION.json'
    if path.exists():assert json.loads(path.read_text())==result,'CHILD_FILE_STDOUT_RESULT_MISMATCH'
    return result
