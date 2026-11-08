"""Reconstruct refuge admissions from actual policy-visible inputs; no model."""
import gzip,json,sys
from pathlib import Path
import numpy as np
from refuge_logic import choose_refuge,wait_ok
def audit_refuge(out):
    out=Path(out);saved=json.loads((out/'REFUGE_SUPERVISION.json').read_text());motion=json.loads(gzip.decompress((out/'MOTION_ENVELOPE.json.gz').read_bytes()));known=json.loads((out/'physics/SETUP.json').read_text())['known'];states={s['native_tick']:s for s in motion['states']}
    with np.load(out/'physics/NATIVE_TRACE.npz')as z:
        tick_to_q={round(float(t)*100):q for t,q in zip(z['time'],z['qpos'])}
    events=saved['events'];requests=0
    for event in events:
        source=event['source'];state=states[source['source_native_tick']]
        assert source['source_scan_sim_time']==state['time']
        assert np.allclose(source['support_bounds'],state['support_bounds'],rtol=0,atol=1e-10),'REFUGE_FORECAST_NOT_CAUSAL'
        assert state['native_tick']<=event['native_tick'],'FUTURE_SCAN_USED'
        if event['event']=='REFUGE_REQUEST':
            history=event['breadcrumbs'];assert all(h['native_tick']<=event['native_tick']for h in history)
            for h in history:
                if h['native_tick']==0:continue
                q=tick_to_q[h['native_tick']];assert np.allclose(q[:2],h['body'][:2],rtol=0,atol=1e-8),'BREADCRUMB_NOT_ACTUAL_ODOMETRY'
            expected=choose_refuge(event['body'],history,source['support_bounds'],source['source_age_s'],known)
            assert expected is not None and event['selection']is not None
            assert expected['breadcrumb_native_tick']==event['selection']['breadcrumb_native_tick']and np.allclose(expected['goal'],event['selection']['goal'],rtol=0,atol=1e-10)
            assert not wait_ok(event['body'],source['support_bounds'],source['source_age_s'],hold=6.)
            requests+=1
        elif event['event']=='REFUGE_REACHED':assert wait_ok(event['body'],source['support_bounds'],source['source_age_s'],hold=4.),'ACTUAL_REFUGE_HOLD_NOT_ADMITTED'
    result=dict(passed=not saved['actor_truth_used']and requests<=3,causal_refuge_requests=requests,total_events=len(events),models=0,integrations=0,scope='Actual odometry history and causal set admission only; physical execution/whole navigation separately audited')
    (out/'REFUGE_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
