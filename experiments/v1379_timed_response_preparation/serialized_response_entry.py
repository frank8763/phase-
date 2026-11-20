"""Scalar-safe preparation output; old failures immutable and separately counted."""
from pathlib import Path
import json as stdjson
import sys
from types import SimpleNamespace
import response_entry
original=response_entry.original
R=Path(__file__).resolve().parents[2]
original.O=R/'runs/v1379_timed_response_preparation/serialized03'


def scalar(value):
    import numpy as np
    if isinstance(value,np.generic):return value.item()
    raise TypeError('UNDECLARED_JSON_TYPE '+type(value).__name__)


def dumps(value,**kwargs):
    return stdjson.dumps(value,default=scalar,**kwargs)


original.json=SimpleNamespace(loads=stdjson.loads,dumps=dumps)
if __name__=='__main__':
    if '--serialization-check' in sys.argv:
        import numpy as np
        value=stdjson.loads((R/'runs/v858_nav2_verified/v1378/steering_response/FINAL_INDEPENDENT_AUDIT.json').read_text())
        value['nested']={'passed':np.bool_(True),'failed':np.bool_(False),'one_ulp':np.nextafter(np.float64(1),np.float64(2))}
        result=stdjson.loads(dumps(value,indent=2,allow_nan=False))
        assert result['nested']['failed'] is False and result['nested']['passed'] is True and result['nested']['one_ulp']>1.
        print(stdjson.dumps(dict(passed=True,full_prior_real_audit_nested_JSON_roundtrip=True,models=0,analytical_native=0)))
    else:raise SystemExit(original.main())
