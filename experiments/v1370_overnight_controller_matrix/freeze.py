"""Freeze all overnight sources, exact unchanged closure and eight phase inputs."""
from component_context import *

def main():
    files=read(R/'experiments/v1369_guard_audit_runtime/SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in files.items())
    for p in sorted(C.iterdir()):
        if p.is_file() and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
    for phase in read(C/'PHASES.json'):
        p=R/phase['source'];files[str(p.relative_to(R))]=sha(p)
    for p in [R/'runs/v1369_guard_audit_runtime/PRODUCER_AUDIT.json',R/'runs/v1368_rolling_map_entry/QUALIFICATION.json']:
        files[str(p.relative_to(R))]=sha(p)
    dump(C/'SOURCE_FREEZE.json',dict(files=files,scope='fixed offline controller matrix, tomorrow09:00, no adaptive repair or fresh24'))
    print(json.dumps(dict(frozen=True,files=len(files),models=0)))

if __name__=='__main__':main()
