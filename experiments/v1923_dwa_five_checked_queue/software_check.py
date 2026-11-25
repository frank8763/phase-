"""Production evidence service and charged boundary, saved arrays only."""
import copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];S=R/'runs/v1923_dwa_five_checked_queue'
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def run(source):
    import numpy as np
    C=R/'experiments/v1922_dwa_five_admission_checked'
    prior_context=sys.modules.get('context')
    load('context',C/'context.py')
    sys.path.insert(0,str(C))
    quota_module=load('v1913_source_single_quota',C/'quota.py')
    resources=load('v1913_source_resource',C/'resources.py')
    io=load('v1913_source_output',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
    service_module=load('v1913_source_service',C/'evidence_service.py')
    old=R/'runs/v1911_dwa_resource_bootstrap_reconstruction'
    inputs=json.loads((old/'INPUTS.json').read_text());setup=json.loads((old/'inputs/SETUP.json').read_text())
    limits=json.loads((old/'inputs/LIMITS_DRAFT.json').read_text())
    # No virtual plant, Predictor, Allocator, policy, FFI numerical call or
    # geometry auditor exists in these explicit software fixtures.
    negative=[];results=[]
    for mode,row in zip(['FULL_ARRAYS','RECIPE'],inputs['profiles'][:2]):
        out=S/'SOFTWARE_CHECK'/mode;out.mkdir(parents=True)
        quota=quota_module.EvidenceQuota(out,limits);quota.bind_external_names([]);quota.write_enforcement_active=True
        quota.prepare_grant(8*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=1800,external_writers=[])
        ledger=SimpleNamespace(limits=limits,python=0,before=lambda *a:None)
        q=SimpleNamespace(np=np)
        service=service_module.Service(q,setup=setup,task=dict(software_only=True),source=source,out=out,quota=quota,ledger=ledger,window={})
        if mode=='FULL_ARRAYS':service.MAX_REBUILD_NATIVE=0
        proof=json.loads((old/'inputs'/row['json']).read_text())
        with np.load(old/'inputs'/row['npz'],allow_pickle=False)as z:arrays={k:z[k]for k in z.files}
        # Byte-accounted complete persistence before any downstream consumer.
        with io.OutputBoundary(out,quota.charge_write):receipt=service.persist(proof,arrays)
        assert receipt['mode']==mode and receipt['committed']
        proof['hybrid_evidence']=receipt
        try:service.load_prefix_after_full(proof)
        except AssertionError:negative.append('prefix_without_full_'+mode)
        else:raise AssertionError('PREFIX_BEFORE_FULL_ACCEPTED')
        def saved_callback(*args):
            ledger.python+=proof['native']
            return {k:a.copy()for k,a in arrays.items()}
        service.reconstruct=saved_callback # explicit saved-data fixture ONLY
        begin=time.monotonic()
        with service.load_full(proof)as decoded:
            assert all(decoded[k].tobytes()==arrays[k].tobytes()for k in arrays)
        elapsed=time.monotonic()-begin
        service.confirm_full_geometry(proof) # software call-order acknowledgement
        with service.load_prefix_after_full(proof)as prefix:
            assert prefix['states'].tobytes()==arrays['states'][:6].tobytes()
        try:service.persist(proof,arrays)
        except AssertionError:negative.append('duplicate_'+mode)
        else:raise AssertionError('DUPLICATE_ACCEPTED')
        assert not service.escrow.holds and not service.poisoned
        results.append(dict(mode=mode,raw_arrays_byte_equal=4,frame_bytes=receipt['frame_bytes'],decode_software_wall_s=elapsed,accounting=service.snapshot(),callback='SAVED_ARRAYS_NOT_MODEL'))
    # Original work bound across online+audit holds, never a second budget.
    esc=service.escrow.__class__(25000000);esc.reserve('one',2205,24995000)
    try:esc.before_online(24995000,3000)
    except AssertionError:negative.append('shared_cap_with_audit_hold')
    else:raise AssertionError('WORK_CAP_NOT_ENFORCED')
    tree=__import__('ast')
    original=(R/'experiments/v1863_remaining_routes_dwa/audit_component.py').read_text()
    seam=load('v1913_source_exact_seam',R/'experiments/v1907_dwa_reconstruction_contract/audit_seam.py')
    expected,proof=seam.build(original)
    expected=expected.replace('def audit(task,result,source):','def audit(task,result,source,*,predictive_arrays):')
    assert expected==(C/'audit_component.py').read_text()
    if prior_context is not None:sys.modules['context']=prior_context
    else:sys.modules.pop('context',None)
    return dict(passed=True,negative_cases=negative,profiles=results,audit_seam=proof,
                real_reconstruction_proof_path=str((old/'RESULT.json').relative_to(R)),
                software_callback_only_here=True,models=0,physical_native=0,replay_native=0)
