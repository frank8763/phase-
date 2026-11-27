"""Fixed root cap and strict source-transport/runtime separation."""
import json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];S=R/'runs/v2184_fair_raw_controller_math'
ROOT_CAP=352*1024;SOURCE_META_CAP=RUNTIME_META_CAP=128*1024
ARCHIVE_CAP=READBACK_CAP=96*1024;RUNTIME_ARCHIVE_CAP=RUNTIME_READBACK_CAP=64*1024;RUNTIME_CAP=64*1024
def allocated(p):
    return int(subprocess.check_output(['du','-sx','-B1',str(p)],timeout=10).split()[0])if p.exists()else 0
def check(stage,extra=0):
    assert stage in {'preparation','source','runtime','closed'}and type(extra)is int and extra>=0
    amendment=json.loads((S/'INNER_STAGE_ALLOCATION_AMENDMENT.json').read_bytes())
    assert amendment['root_precharge_unchanged_bytes']==ROOT_CAP and amendment['Source_claims_or_numerics_so_far']==0
    other=sum(allocated(R/n)for n in ['runs/v2182_fairness_mechanism_diagnosis','runs/v2183_lossless_capture_stream'])
    assert other+ROOT_CAP<=1024**2,'PARALLEL1MIB_PRECHARGE_EXHAUSTED'
    assert allocated(S)+extra<=ROOT_CAP,'NATIVE_MATH_ROOT352KIB_EXHAUSTED'
    meta=0
    for p in S.rglob('*'):
        if p.is_file()and p.relative_to(S).parts[0]not in {'RUNTIME','SOURCE_TRANSPORT','RUNTIME_TRANSPORT'}:meta+=p.stat().st_blocks*512
    assert meta<= (SOURCE_META_CAP if stage in {'preparation','source'}else RUNTIME_META_CAP),'MATH_STAGE_METADATA_CAP'
    if stage in {'preparation','source'}:
        assert allocated(S/'SOURCE_TRANSPORT')<=ARCHIVE_CAP+READBACK_CAP+16*1024,'SOURCE_TRANSPORT_STAGE_CAP'
    if stage=='runtime':
        barrier=json.loads((S/'POST_SOURCE_STORAGE_BARRIER.json').read_bytes())
        assert barrier['passed']and barrier['actual_remote_all_SHA']and barrier['exact_transport_cleanup_completed']
        assert all(not(R/n).exists()for n in barrier['removed_transport_paths']),'SOURCE_TRANSPORT_REMAINS_AT_RUNTIME'
        assert allocated(S/'RUNTIME')+extra<=RUNTIME_CAP,'MATH_RUNTIME_EVIDENCE64KIB_EXHAUSTED'
    return dict(other_preparation_allocated=other,root_precharged=ROOT_CAP,root_actual_allocated=allocated(S),stage=stage)
