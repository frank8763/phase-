"""Zero-model supplemental transport for the unchanged full V1372 audit."""
import importlib.abc
import json
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('SUPPLEMENT_MODELS_FORBIDDEN '+name)

sys.meta_path.insert(0,NoPhysical())
sys.path.insert(0,str(R/'experiments/v1372_coherent_sampling_fault'))
from component_context import read,sha,sources,dump
from sampling_audit import audit

def scalar(v):
    # Only producer NumPy scalar transport conversion; no changed verdicts/gates.
    import numpy as np
    assert isinstance(v,np.generic),'UNEXPECTED_NONSCALAR_TYPE'
    return v.item()

def main():
    import numpy as np
    manifest=read(C/'SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in manifest['files'].items())
    closed=R/'runs/v1372_coherent_sampling_fault';assert read(closed/'COMPLETION.json')['closed'] and not read(closed/'APPROVAL.json')['models_authorized']
    assert (R/'REVIEW_PENDING').exists() and sources()
    task=read(R/'experiments/v1372_coherent_sampling_fault/TASKS.json')[0]
    proof=audit(task)
    try:json.dumps(proof)
    except TypeError as exc:assert 'bool_' in str(exc);error=repr(exc)
    else:raise AssertionError('ORIGINAL_SERIALIZATION_FAILURE_NOT_REPRODUCED')
    types={k:type(v).__module__+'.'+type(v).__name__ for k,v in proof['checks'].items() if type(v) is not bool}
    encoded=json.dumps(proof,default=scalar,allow_nan=False);restored=json.loads(encoded)
    assert restored==proof and all(type(v) is bool for v in restored['checks'].values()),'AUDIT_VALUES_CHANGED_BY_TRANSPORT'
    fixture=dict(no=np.bool_(False),yes=np.bool_(True),precise=np.nextafter(np.float64(1.),np.float64(2.)))
    converted=json.loads(json.dumps(fixture,default=scalar));assert converted==fixture and converted['no'] is False and converted['yes'] is True and converted['precise']>1.
    dump(O/'SUPPLEMENTAL_INDEPENDENT_AUDIT.json',dict(restored,supplemental_only=True,original_batch_NOT_PASSED_preserved=True,
        original_audit_source_SHA=sha(R/'experiments/v1372_coherent_sampling_fault/sampling_audit.py'),python=sys.version,numpy=np.__version__,
        serialization_error_reproduced=error,converted_scalar_types=types,unchanged_values_exact=True,false_true_nextafter_regression=True,
        new_models=0,new_actual_native=0,new_own_replay_native=0,new_private_native=0))
    assert all(sha(R/p)==h for p,h in manifest['files'].items()) and sources(),'ORIGINAL_EVIDENCE_OR_SOURCE_CHANGED'
    dump(O/'SOURCE_PRESERVATION.json',dict(passed=True,original_source_and_closed_evidence_unchanged=True,files=len(manifest['files']),models=0,physical_native=0))
    print(json.dumps(dict(passed=restored['passed'],checks=len(restored['checks']),scalar_types=types,original_batch_preserved=True,models=0,physical_native=0)))
    return 0 if restored['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
