"""Freeze original model/controller closure and original failed-state evidence."""
from component_context import *
def main():
    assert not (O/'ROUND_WINDOW.json').exists(),'CANNOT_REFREEZE_LIVE_OR_CLOSED_WINDOW'
    files=read(R/'experiments/v1371_overnight_retrospective/SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in files.items()),'OLD_SOURCE_CHANGED'
    prior=Path(read(C/'TASKS.json')[0]['prior_raw'])
    for name in ['APPLIED_JOURNAL.json','physics/NATIVE_TRACE.npz','physics/SETUP.json','physics/SENSORS.json.gz']:
        p=prior/name;files[str(p.relative_to(R))]=sha(p)
    for p in sorted(C.iterdir()):
        if p.is_file() and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
    dump(C/'SOURCE_FREEZE.json',dict(files=files,scope='single sampling fault component; no goal navigation; new physical authority required'))
    print(json.dumps(dict(frozen=True,files=len(files),models=0)))
if __name__=='__main__':main()
