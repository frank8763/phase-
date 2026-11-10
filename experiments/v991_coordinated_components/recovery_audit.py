"""Forward alternatives and certificate provenance, independently checked by index."""
import gzip
import json
from pathlib import Path

def audit(out):
    rows=json.loads(gzip.decompress((Path(out)/'COMMAND_TUBES.json.gz').read_bytes()))
    expected=[[0.,0.]]+[[v,v*k]for v in[.05,.1]for k in[-.758770385,0.,.758770385]]
    count=0;modes={}
    for row in rows:
        r=row.get('recovery')
        if r is None:continue
        count+=1;mode=r['mode'];modes[mode]=modes.get(mode,0)+1
        assert not row['wait_renewal']and row['wanted']!=[0.,0.]
        assert not r['nominal_proof']['passed']
        alternatives=r['alternatives'];assert len(alternatives)==7
        assert [a['requested']for a in alternatives]==expected
        for i,a in enumerate(alternatives):
            p=a['proof'];assert a['index']==i and a['passed']==p['passed']and [p['v'],p['w']]==a['control']
            assert p['body_native_tick']==row['packet']['native_tick']and p['source_native_tick']==row['source']['source_native_tick']and p['issued_at']==row['proof']['issued_at']
            qualified=p['static_lower_m']>=.155 and(p['dynamic_lower_m']is None or p['dynamic_lower_m']>=.155)and(p['terminal_cycle_lower_m']is None or p['terminal_cycle_lower_m']>=.155)
            assert qualified==p['passed']
        selected=r['selected']
        if selected is None:assert mode=='NO_NEW_CERTIFIED_CONTROL';continue
        # Rate limiting may give several requests the same executed command.
        matches=[a for a in alternatives if a['control']==list(selected)and a['passed']and a['proof']==row['proof']]
        assert matches,'SELECTED_CONTROL_HAS_NO_QUALIFIED_ORIGIN'
        if mode=='CERTIFIED_PROGRESS_ALTERNATIVE':assert any(a['short_goal_progress_m']>1e-4 for a in matches)
        elif mode=='CERTIFIED_CLEARANCE_RECOVERY':assert any(a['nominal_one_second_clearance_gain_m']>1e-4 for a in matches)
        elif mode=='CERTIFIED_STOP_ONLY':assert list(selected)==[0.,0.]
        else:raise AssertionError('UNREGISTERED_RECOVERY_MODE')
    return dict(passed=True,recovery_decisions=count,modes=modes,forward_alternatives=7,models=0,integrations=0)
