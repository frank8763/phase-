"""Shared analytical bindings; no diagnostic import guards in live code."""
from pathlib import Path
import sys
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1186_live_observer_regeneration'
sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'))
import chain as original
q=original.q;np=q.np
def validate_input(x):
    p=x['packet'];s=x['source'];assert type(p['native_tick'])is int and p['native_tick']>=0 and abs(p['sim_time']-.01*p['native_tick'])<=1e-8
    assert p['dynamic_discovered']and p['steering']['native_tick']==p['native_tick']and 'body_lateral'in p
    assert s['source_native_tick']<=p['native_tick']and 0<=s['source_age_s']<=.051
    assert abs(s['source_age_s']-(p['sim_time']-.01*s['source_native_tick']))<=1e-8
    initial=q.initial(p);assert np.isfinite(initial['state']).all()and np.isfinite(initial['last_ctrl']).all()
    return True
