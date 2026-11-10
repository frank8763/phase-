"""Real V987 witnesses fail the proposed final-target coordination contract."""
import gzip
import hashlib
import json
from pathlib import Path
from independent import check

R=Path(__file__).resolve().parents[2]
O=R/'runs/v990_coordinated_actuation'


def main():
    receipt=json.loads((O/'RESTORE_RECEIPT.json').read_text())
    for row in receipt['files']:
        assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    setup=json.loads((O/'saved_v987/physics/SETUP.json').read_text())
    rows=json.loads(gzip.decompress((O/'saved_v987/physics/YAW_FEEDBACK.json.gz').read_bytes()))
    witnesses=[]
    for tick in [6124,6144,6184,6229]:
        row=next(r for r in rows if r['native_tick']==tick)
        try:check(row['proof']['previous'],row['actual_ctrl'],setup['limits'],setup['slew_per_second'])
        except AssertionError as e:witnesses.append(dict(native_tick=tick,rejected=True,reason=str(e),actual_ctrl=row['actual_ctrl']))
        else:witnesses.append(dict(native_tick=tick,rejected=False))
    result=dict(passed=False,expected_red=True,original_failure_reproduced=all(x['rejected']for x in witnesses),
                seam='Actual saved previous/final four-motor targets; no altered fixture',witnesses=witnesses,
                physical_tracking_failure_still_unfixed=True,models=0,integrations=0)
    (O/'BASELINE_RED.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));assert result['original_failure_reproduced']


if __name__=='__main__':main()
