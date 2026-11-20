from component_context import *
def main():
    assert not (O/'ROUND_WINDOW.json').exists(),'FREEZE_AFTER_LAUNCH_FORBIDDEN'
    files=read(R/'experiments/v1375_actual_capture_component/SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in files.items())
    raw=Path(read(C/'TASKS.json')[0]['prior_raw'])
    for name in ['APPLIED_JOURNAL.json','TASK.json','SEGMENT_RECORDS.json','CAUSAL_OBSERVATIONS.json','physics/NATIVE_TRACE.npz','physics/SETUP.json']:
        p=raw/name;files[str(p.relative_to(R))]=sha(p)
    prior=R/'runs/v858_nav2_verified/v1375/capture_main'
    for name in ['APPLIED_JOURNAL.json','CAPTURE_COMMANDS.json','RESULT.json','FINAL_INDEPENDENT_AUDIT.json','physics/NATIVE_TRACE.npz']:
        p=prior/name;files[str(p.relative_to(R))]=sha(p)
    p=O/'NOMINAL_PREPARED_CAPTURE.json';files[str(p.relative_to(R))]=sha(p)
    for p in [*(R/'experiments/v1374_day_handoff_validation').iterdir(),R/'runs/v1374_day_handoff_validation/CAPTURE_NOMINAL_PROBE.json',*C.iterdir()]:
        if p.is_file() and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
    dump(C/'SOURCE_FREEZE.json',dict(files=files,scope='actual measured capture main and successful repeat;17:00 hard stop; no full goal navigation'))
    print(json.dumps(dict(frozen=True,files=len(files),models=0)))
if __name__=='__main__':main()
