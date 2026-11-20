from component_context import *
def main():
    assert not (O/'ROUND_WINDOW.json').exists(),'FREEZE_AFTER_LAUNCH_FORBIDDEN'
    files=read(R/'experiments/v1376_prepared_capture_component/SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in files.items())
    raw=Path(read(C/'TASKS.json')[0]['prior_raw'])
    for name in ['APPLIED_JOURNAL.json','TASK.json','SEGMENT_RECORDS.json','CAUSAL_OBSERVATIONS.json','physics/NATIVE_TRACE.npz','physics/SETUP.json']:
        p=raw/name;files[str(p.relative_to(R))]=sha(p)
    for name in ['ORIGINAL_COUPLED_ENVELOPE_GEOMETRY.json','ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json','ENVELOPE_SOURCE_FREEZE.json']:
        p=R/'runs/v1377_timed_handoff_witness'/name;files[str(p.relative_to(R))]=sha(p)
    for p in [*(R/'experiments/v1377_timed_handoff_witness').iterdir(),*(R/'experiments/v1374_day_handoff_validation').iterdir(),R/'runs/v1374_day_handoff_validation/CAPTURE_NOMINAL_PROBE.json',*C.iterdir()]:
        if p.is_file() and p.name!='SOURCE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
    dump(C/'SOURCE_FREEZE.json',dict(files=files,scope='single saved32210 steering response under full declared envelope;17:00; no driving'))
    print(json.dumps(dict(frozen=True,files=len(files),models=0)))
if __name__=='__main__':main()
