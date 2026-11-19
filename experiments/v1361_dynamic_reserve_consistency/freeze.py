"""Freeze this new source tree plus the exact unchanged parent closure."""
import hashlib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def main():
    old=R/'experiments/v1359_reverse_restart_bridge/SOURCE_FREEZE.json'
    files=json.loads(old.read_text())['files']
    for p,h in files.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
    for p in sorted(C.iterdir()):
        if p.is_file() and p.name!='SOURCE_FREEZE.json':
            files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
    (C/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=files,scope='V1361 fixed originalWE commandaware dynamic reserve main/successrepeat; original17:00 deadline; no24'),indent=2)+'\n')
    print(json.dumps(dict(frozen=True,files=len(files),models=0,physical_native=0)))


if __name__=='__main__':main()
