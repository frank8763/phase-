"""Compare full physical setup; only two construction performance clocks are metadata."""
import copy,json
from pathlib import Path
import numpy as np
IGNORED=['actor.swept_envelope_reference.elapsed_s','actor.swept_envelope_reference.search.wall_s']
def canonical_setup(setup):
    result=copy.deepcopy(setup)
    if result.get('actor')is None:return result
    certificate=result['actor']['swept_envelope_reference']
    certificate.pop('elapsed_s',None);certificate['search'].pop('wall_s',None)
    return result
def repeat_check(baseline,repeat):
    b,r=Path(baseline),Path(repeat)
    setups=[json.loads((p/'physics/SETUP.json').read_text())for p in [b,r]]
    initials=[np.load(p/'physics/INITIAL_STATE.npz')['state']for p in [b,r]]
    audits=[json.loads((p/'INDEPENDENT_AUDIT.json').read_text())for p in [b,r]]
    initial_error=float(np.max(abs(initials[0]-initials[1])))if initials[0].shape==initials[1].shape else None
    same=canonical_setup(setups[0])==canonical_setup(setups[1])
    return dict(passed=same and initial_error is not None and initial_error<=1e-8 and all(a['passed']for a in audits),same_complete_physical_setup=same,initial_state_max_error=initial_error,both_functional_safe_arrivals=all(a['passed']for a in audits),ignored_construction_performance_metadata_only=IGNORED,exact_navigation_trajectory_claim=False,repeat_contract='Same complete physical setup and initial state, both full dynamic arrivals, each own executed-control replay <=1e-8; asynchronous trajectories may differ.')
