"""Freeze all new scientific/operational files and required prior raw inputs."""
from component_context import *


def main():
    parent=read(R/'experiments/v1367_shared_recovery_component/SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in parent.items()),'PRIOR_FROZEN_SOURCE_CHANGED'
    for p in sorted(C.iterdir()):
        if p.is_file() and p.name!='SOURCE_FREEZE.json':parent[str(p.relative_to(R))]=sha(p)
    prior=Path(read(C/'TASKS.json')[0]['prior_raw'])
    for name in ['APPLIED_JOURNAL.json','physics/NATIVE_TRACE.npz','physics/INITIAL_STATE.npz','physics/SETUP.json','INITIAL_PACKET.json','FINAL_INDEPENDENT_AUDIT.json']:
        p=prior/name;parent[str(p.relative_to(R))]=sha(p)
    dump(C/'SOURCE_FREEZE.json',dict(files=parent,scope='V1368 four fixed shared safe recovery components, no full navigation; new bounded human window required'))
    print(json.dumps(dict(frozen=True,files=len(parent),models=0)))


if __name__=='__main__':main()
