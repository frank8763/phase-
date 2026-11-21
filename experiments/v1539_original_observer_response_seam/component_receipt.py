"""Consume a closed component without granting the original observer domain.

Pure bounded JSON/AST/source receipts. No numerical module imports or calls.
This draft needs its own necessary source qualification before production use.
"""
import ast
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
BASE=R/'runs/v1536_review_precharge_source'
SOURCE_RECOVERY=R/'runs/v1537_stop_closure_source_recovery'
RUNTIME_RECOVERY=R/'runs/v1538_stop_runtime_recovery'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class ComponentDomainRefusal(AssertionError):
    def __init__(self,first,proof,secondary=None):
        super().__init__(first);self.proof=proof;self.secondary=secondary

def checked(name,prepared,*,maximum=4*1024**2):
    path=R/name
    assert not Path(name).is_absolute()and '..'not in Path(name).parts
    assert path.resolve()==path and path.is_file()and not path.is_symlink()
    assert path.stat().st_size<=maximum and prepared[name]==sha(path),'COMPONENT_RECEIPT_SOURCE_CHANGED'
    return path

def json_checked(name,prepared):return json.loads(checked(name,prepared).read_text())

def original_requirement(name,function,prepared):
    path=checked(name,prepared)
    tree=ast.parse(path.read_text());body=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==function)
    # Exact original stop tuple, not a naked integer elsewhere in a comment.
    stops=[]
    for n in ast.walk(body):
        if isinstance(n,ast.Tuple)and len(n.elts)==4 and all(isinstance(v,ast.Constant)for v in n.elts):
            values=[v.value for v in n.elts]
            if values==[0.,0.,2200,0]:stops.append(n.lineno)
    assert stops,'ORIGINAL_COMPLETE_STOP_SOURCE_NOT_FOUND'
    return dict(path=name,sha256=sha(path),function=function,original_complete_stop_native=2200,
                stop_tuple_lines=stops,function_AST_sha256=hashlib.sha256(ast.dump(body,include_attributes=False).encode()).hexdigest(),
                imported=False,executed=False)

def read_component(*,prepared_sources,save_proof,requested_scope):
    proof=dict(passed=False,stage='source_receipt',component_only=True,
               original_observer_search_authorized=False,freshwire_authorized=False,
               physical_authorized=False,models_authorized=False,complete_response_qualified=False,
               whole_route_qualified=False,new_model_steps=0)
    first=None;answer=None
    try:
        def read(path):return json_checked(str(path.relative_to(R)),prepared_sources)
        recovery=read(BASE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
        freeze_path=checked(str((BASE/'SOURCE_FREEZE.json').relative_to(R)),prepared_sources)
        assert recovery['passed']and recovery['source_freeze_sha256']==sha(freeze_path)
        assert recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
        source_remote=read(SOURCE_RECOVERY/'FULL_REMOTE_VERIFIED.json')
        runtime_remote=read(RUNTIME_RECOVERY/'FULL_REMOTE_VERIFIED.json')
        index_path=checked(str((RUNTIME_RECOVERY/'ARCHIVE_INDEX.json').relative_to(R)),prepared_sources)
        index=json.loads(index_path.read_text());members={r['path']:r for r in index['files']}
        assert len(members)==len(index['files'])==runtime_remote['members']
        assert index['archive_bytes']==runtime_remote['archive_bytes']
        assert runtime_remote['source_commit']==source_remote['source_commit']
        for remote in [source_remote,runtime_remote]:
            assert remote['passed']and all(remote[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])
        values={}
        for name in ['COMPLETION.json','model/RESULT.json','model/INDEPENDENT_COMPARISON.json','model/CPP_BRANCH_SAVED.json','model/PYTHON_BRANCH_SAVED.json']:
            path=BASE/name;relative=str(path.relative_to(R));assert members[relative]['sha256']==prepared_sources[relative]
            values[name]=read(path)
        result=values['model/RESULT.json'];comparison=values['model/INDEPENDENT_COMPARISON.json']
        assert values['COMPLETION.json']['passed']and result['closed']and result['passed']and result['first_error']is None and result['secondary_errors']==[]
        assert result['generation_analytical_native']==result['audit_analytical_native']==200
        assert result['generation_inflight_unknown']is result['audit_inflight_unknown']is False
        assert result['physical_native']==result['ownreplay_native']==result['nominal_native']==result['optimizer_calls']==0
        assert comparison['passed']and set(comparison['maximum_errors'])=={'states','ctrl','memory','modes','gear','native','sim_time','requests'}
        assert all(type(v)in [int,float]and v==0 for v in comparison['maximum_errors'].values())
        for name in ['CPP_BRANCH_SAVED.json','PYTHON_BRANCH_SAVED.json']:
            receipt=values['model/'+name];row=receipt['arrays'];path=BASE/'model'/row['path']
            assert Path(row['path']).name==row['path']and receipt['complete']and receipt['native']==200
            assert receipt['binding']==comparison['source_binding']
            relative=str(path.relative_to(R));checked(relative,prepared_sources,maximum=1024**2)
            assert members[relative]['sha256']==row['sha256']==prepared_sources[relative]and members[relative]['bytes']==row['bytes']==path.stat().st_size
        requirements=[original_requirement('experiments/v1221_exact_stop_pruning/candidate_observer.py','_synthesize',prepared_sources),
                      original_requirement('experiments/v1186_live_observer_regeneration/stop_certificates.py','prove',prepared_sources),
                      original_requirement('experiments/v1195_eight_gib_timed_refuge/candidate_observer.py','candidate_rows',prepared_sources)]
        proof.update(stage='domain_boundary',component_current_stop_passed=True,component_generation_native=200,
                     component_independent_audit_native=200,component_tube_lower_m=comparison['stop_proof']['causal_tube_lower_m'],
                     method_input_sha256=comparison['source_binding']['method_input_sha256'],source_binding=comparison['source_binding'],
                     original_stop_requirements=requirements,original2200_response_executed=False,
                     original_geometry_interval_domain_qualified=False,original_current_candidate_search_executed=False,
                     complete_original_stop_permission=False,requested_scope=requested_scope)
        assert requested_scope=='READ_CLOSED_COMPONENT_ONLY','COMPONENT200_NOT_ORIGINAL2200_SEARCH_OR_ACTUAL_AUTHORITY'
        proof['passed']=True;answer=dict(proof)
    except BaseException as error:first=repr(error);proof.update(first_error=first,failed_stage=proof['stage'])
    secondary=None
    try:save_proof(proof)
    except BaseException as error:
        secondary=repr(error);proof['passed']=False;proof['secondary_save_error']=secondary
    if first is not None or secondary is not None:raise ComponentDomainRefusal(first or'COMPONENT_RECEIPT_PROOF_SAVE_FAILED',proof,secondary)
    return answer
