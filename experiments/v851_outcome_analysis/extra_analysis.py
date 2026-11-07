"""Read original profiling and actual stopped-cusp records; no model imports."""
import hashlib,json,signal
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_EXTRA_180S')));signal.alarm(180)
    out=R/'runs/v851_outcome_analysis/extra';out.mkdir(exist_ok=False);sources={}
    def raw(p):
        b=p.read_bytes();sources[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
    pair=R/'runs/v851_profile_output_worker/v851_main_slot01/paired'
    profile=json.loads(raw(pair/'OPERATION_PROFILE.json'));summary={}
    assert profile['overlapping_inclusive_timers_do_not_add']
    for name,row in profile['operations'].items():
        samples=np.asarray(row['samples_wall_s']);assert len(samples)==row['calls']and np.isfinite(samples).all()
        summary[name]=dict(calls=row['calls'],inclusive_wall_s=row['inclusive_wall_s'],p50_s=float(np.quantile(samples,.5)),p95_s=float(np.quantile(samples,.95)),max_s=float(samples.max()))
    records=[json.loads(x)for x in raw(pair/'geometry_memory/gear_transitions.jsonl').splitlines()]
    cusps=[x for x in records if x['status']=='STOPPED_CUSP_SWITCH']
    assert [x['step']for x in cusps]==[424,754,910,995]
    assert all(x['position_error_m']<=.16 and x['heading_error_rad']<=.25 and x['actual_xy_speed_m_s']<=.05 for x in cusps)
    result=dict(status='SAVED_PROFILE_AND_ACTUAL_STOPPED_CUSPS_VERIFIED',profiling=summary,inclusive_timers_overlap_do_not_add=True,actual_stopped_cusps=cusps,new_models=0,new_integrations=0,limitations='Saved actual records only. Native prediction, admission and nominal selection timers overlap; no sum or new backend speedup claim.')
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');(out/'INPUT_SHA256.json').write_text(json.dumps(sources,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
