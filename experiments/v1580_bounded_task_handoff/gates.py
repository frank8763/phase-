"""Original full13array gates with registered current-time geometry and target."""
import hashlib
import importlib.util
from pathlib import Path
import math
R=Path(__file__).resolve().parents[2]


def original(guard):
    path=R/'experiments/v1552_complete_canonical_witness/gates.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location('v1580_original_complete_gates',path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def evaluate(arrays,method,setup,geometry,*,expected_native,zero_suffix,raw_current_only):
    assert method['scientific_integration_revision']==12 and method['geometry_kind']=='ORIGINAL_CAUSAL_TIME_POLYGONS'
    # Caller supplies a source-checked original gate module at preparation;
    # this never swaps a disk into the numeric geometry calculation.
    module=geometry.original_gate_module
    proof=module.evaluate(arrays,method,setup,geometry,expected_native=expected_native,
        zero_suffix=zero_suffix,raw_current_only=raw_current_only)
    # Original result label is fixed to FULL_PERIOD_DISK. Numeric operations
    # use the supplied geometry; publish the declared actual kind explicitly.
    proof['geometry_kind']='ORIGINAL_CAUSAL_TIME_POLYGONS';proof['scientific_integration_revision']=12
    return proof


def endpoint(arrays,method):
    s=arrays['states'][-1];target=method['actual_next_segment']['poses'][-1]
    rear=(float(s[0])-.3*math.cos(float(s[2])),float(s[1])-.3*math.sin(float(s[2])))
    distance=math.dist(rear,target[:2]);yaw=abs(math.atan2(math.sin(float(s[2])-target[2]),math.cos(float(s[2])-target[2])))
    return dict(passed=distance<=.12+1e-8 and yaw<=.20+1e-8,rear_error_m=distance,
        heading_error_rad=yaw,original_segment_gate=True,whole_route_passed=False)
