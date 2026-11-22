"""Same complete original gates plus actual next-segment nominal endpoint."""
import hashlib
import importlib.util
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2]


def exact(name,path,guard):
    guard.check();assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def geometry(method,setup,guard):
    assert method['scientific_integration_revision']==11
    base=exact('v1576_unchanged_complete_geometry',R/'experiments/v1552_complete_canonical_witness/gates.py',guard)
    return base.geometry(method,setup,guard)


def evaluate(arrays,method,setup,geom,*,expected_native,zero_suffix,raw_current_only):
    # Numeric full13array checking is invoked by the guarded owner only.
    s=importlib.util.spec_from_file_location('v1576_same_complete_array_gates',R/'experiments/v1552_complete_canonical_witness/gates.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    result=m.evaluate(arrays,method,setup,geom,expected_native=expected_native,
        zero_suffix=zero_suffix,raw_current_only=raw_current_only)
    result['scientific_integration_revision']=11
    return result


def endpoint(arrays,method):
    body=arrays['states'][-1];target=method['actual_next_segment']['poses'][-1]
    rear=(float(body[0])-.3*math.cos(float(body[2])),float(body[1])-.3*math.sin(float(body[2])))
    distance=math.dist(rear,target[:2]);angle=abs(math.atan2(math.sin(float(body[2])-target[2]),math.cos(float(body[2])-target[2])))
    return dict(passed=distance<=.12+1e-8 and angle<=.20+1e-8,
        rear_error_m=distance,heading_error_rad=angle,segment_gate_only=True,whole_route_passed=False)
