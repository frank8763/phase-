"""Create one new worker from immutable V848; no previous source or output is modified."""
import ast
import hashlib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
OLD=R/'experiments/v848_goal_first_worker';W=R/'experiments/v850_progress_consistent_worker'
OUT=R/'runs/v850_progress_consistent_return'


def main():
    assert not W.exists();W.mkdir();OUT.mkdir(exist_ok=False)
    files={}
    for p in OLD.iterdir():
        if p.is_file()and p.suffix in ['.py','.json','.md']:
            (W/p.name).write_bytes(p.read_bytes());files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT/'ORIGINAL_SOURCE_SHA256.json').write_text(json.dumps(files,indent=2)+'\n')
    for p in W.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    print(json.dumps(dict(new_worker=str(W.relative_to(R)),models=0,integrations=0,original_sources_preserved=True)))


if __name__=='__main__':main()
