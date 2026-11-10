"""Scalar reconstruction with 1e-12 analytical metadata tolerance only."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('original_scalar_shaping',R/'experiments/v961_steering_continuity/independent_shaping.py');original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
def check(shape,packet,last):
    prior=shape['prior']
    assert(prior is None)==(last is None),'PRIOR_RESET_MISMATCH'
    if last is not None:
        assert set(prior)==set(last)=={'at','delta'}and prior['at']==last['at']and abs(prior['delta']-last['delta'])<=1e-12,'PRIOR_CAUSAL_STATE_MISMATCH'
    # Original check already allows1e-12 for scalar analytical delta/commands.
    # Use its verified saved delta as next checkpoint, avoiding a mix of NumPy
    # and scalar round-off in equality of the following metadata state.
    compatible=dict(shape,prior=last)
    result=original.check(compatible,packet,last)
    return None if result is None else dict(at=shape['at'],delta=shape['delta'])
