"""Source-bound original witness work planning; never produces controls.

Draft metadata API: no old modules imported, no numerical model calls.
"""
import ast
import hashlib
import json
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2]
CATALOGUE='experiments/v1221_exact_stop_pruning/candidate_observer.py'
TEMPLATE='runs/v1144_saved_entry_relay/software/ROWS.json'
STOP_SOURCE='experiments/v1186_live_observer_regeneration/stop_certificates.py'
ENDPOINT='experiments/v1221_exact_stop_pruning/endpoint_bound.py'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def checked(name,prepared):
    path=R/name;assert path.is_file()and not path.is_symlink()and path.resolve()==path
    assert path.stat().st_size<=1024**2 and prepared[name]==sha(path),'ORIGINAL_WITNESS_BUDGET_SOURCE_CHANGED'
    return path

def prefix_metadata(rows,cut):
    # Counts and modes/speed-sign only; no original target/control is returned.
    assert type(cut)is int and cut>0,'ORIGINAL_TEMPLATE_CUT_INVALID'
    remaining=cut;parts=[]
    for row in rows:
        assert isinstance(row,list)and len(row)==4
        target,speed,count,mode=row
        assert type(count)is int and count>0 and type(mode)is int and mode in [0,1]
        assert math.isfinite(target)and math.isfinite(speed)
        take=min(remaining,count)
        if take:parts.append(dict(native=take,stationary=(speed==0.),parked=bool(mode)))
        remaining-=take
        if remaining==0:break
    assert remaining==0,'ORIGINAL_TEMPLATE_CUT_OUTSIDE_SOURCE'
    return parts

def catalog_parameters(source):
    tree=ast.parse(source);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_synthesize')
    assign=next(n for n in f.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='catalog'for t in n.targets))
    v=assign.value;assert isinstance(v,ast.BinOp)and isinstance(v.op,ast.Add)and isinstance(v.right,ast.ListComp)
    initial=ast.literal_eval(v.left);assert initial==[(0.,0)]
    comp=v.right;assert isinstance(comp.elt,ast.Tuple)and [e.id for e in comp.elt.elts]==['t','n']
    assert len(comp.generators)==2 and [g.target.id for g in comp.generators]==['n','t']and not any(g.ifs or g.is_async for g in comp.generators)
    counts=ast.literal_eval(comp.generators[0].iter);turns=ast.literal_eval(comp.generators[1].iter)
    assert counts==[200,400,600,800]and turns==[0.,-.16,-.24,-.32,-.42722137342572125]
    cutloop=next(n for n in ast.walk(f)if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='cut')
    cuts=ast.literal_eval(cutloop.iter);assert cuts==[11400,11800]
    return initial+[(turn,count)for count in counts for turn in turns],cuts

def uncompressed_arrays(native):
    #8state+5memory,3mode+3gear+native+clock at N+1;
    #4ctrl+3request at N. float64/int64 bytes, no file/header/index.
    assert type(native)is int and native>=0
    return 168*(native+1)+56*native

class BudgetRefusal(AssertionError):
    def __init__(self,first,proof,secondary=None):super().__init__(first);self.proof=proof;self.secondary=secondary

def analyze(*,prepared_sources,save_proof):
    proof=dict(passed=False,models=0,new_analytical_native=0,physical_native=0,
               source_only=True,model_permission=False,controls_output=False,original_search_budget_complete=False)
    first=None;answer=None
    try:
        paths={name:checked(name,prepared_sources)for name in [CATALOGUE,TEMPLATE,STOP_SOURCE,ENDPOINT]}
        catalog,cuts=catalog_parameters(paths[CATALOGUE].read_text());rows=json.loads(paths[TEMPLATE].read_text())['rows']
        stop_tree=ast.parse(paths[STOP_SOURCE].read_text());stop_f=next(n for n in stop_tree.body if isinstance(n,ast.FunctionDef)and n.name=='prove')
        tuples=[n for n in ast.walk(stop_f)if isinstance(n,ast.Tuple)and len(n.elts)==4 and all(isinstance(x,ast.Constant)for x in n.elts)]
        assert sum([x.value for x in n.elts]==[0.,0.,2200,0]for n in tuples)==2
        # Account the exact explicit propagation call sites. This is not a
        # bound on opaque geometry/import/math operations or actual runtime.
        endpoint=ast.parse(paths[ENDPOINT].read_text())
        upper=next(n for n in endpoint.body if isinstance(n,ast.FunctionDef)and n.name=='upper_bound')
        simulations=[n for n in ast.walk(upper)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='simulate']
        assert len(simulations)==1 and isinstance(simulations[0].func.value,ast.Name)and simulations[0].func.value.id=='engine'
        kinds=next(n for n in ast.walk(upper)if isinstance(n,ast.For)and isinstance(n.target,ast.Tuple)and [x.id for x in n.target.elts]==['kind','schedule'])
        assert isinstance(kinds.iter,ast.List)and len(kinds.iter.elts)==2
        assert [n.elts[0].value for n in kinds.iter.elts]==['current','prospective']
        assert any(n is simulations[0]for n in ast.walk(kinds))
        cases=[]
        for turn,stage_native in catalog:
            for cut in cuts:
                pieces=prefix_metadata(rows,cut)+[dict(native=2200,stationary=True,parked=False)]
                if stage_native:pieces=[dict(native=stage_native,stationary=False,parked=False),dict(native=2200,stationary=True,parked=False)]+pieces
                length=sum(p['native']for p in pieces);prefixes=[]
                for part in pieces:
                    n=part['native']
                    if part['stationary']or part['parked']:prefixes.append(n)
                    else:prefixes.extend([8]*(n//8)+([n%8]if n%8 else []))
                assert sum(prefixes)==length
                core_calls=1+2*len(prefixes)
                core_native=length+sum(2200+2200+n for n in prefixes)
                raw=uncompressed_arrays(length)+sum(uncompressed_arrays(2200)+uncompressed_arrays(2200+n)for n in prefixes)
                stop_native=core_native-length
                # endpoint and certify each traverse <=B boundaries. A
                # rejection-reproduction branch adds one pair and skips
                # certify; that pair is <=one completeB traversal.
                bounded_explicit_native=length+2*stop_native
                bounded_explicit_calls=1+4*len(prefixes)
                canonical_raw_upper=uncompressed_arrays(length)+2*(raw-uncompressed_arrays(length))
                cases.append(dict(original_catalogue_index=len(cases),stage_native=stage_native,source_cut=cut,
                     nominal_native=length,old_full_stop_boundaries=len(prefixes),full_no_pruning_core_engine_calls=core_calls,
                     full_no_pruning_core_cpp_native=core_native,complete8array_raw_payload_bytes=raw,
                     explicit_endpoint_certify_reproduction_upper_cpp_native=bounded_explicit_native,
                     explicit_endpoint_certify_reproduction_upper_engine_calls=bounded_explicit_calls,
                     canonical_all_explicit_call_raw_payload_upper_bytes=canonical_raw_upper,
                     independent_audit_calls=None,
                     serialization_and_compression_disk_peak_bytes=None,model_execution_permitted=False))
        assert len(cases)==42
        proof.update(passed=True,cases=cases,original_catalogue_entries=42,
             selector_initial_common_stop_native=2200,
             explicit_CPP_callsite_upper_native=2200+sum(v['explicit_endpoint_certify_reproduction_upper_cpp_native']for v in cases),
             explicit_CPP_simulate_callsite_upper=1+sum(v['explicit_endpoint_certify_reproduction_upper_engine_calls']for v in cases),
             explicit_CPP_Engine_constructor_upper=1+2*len(cases),
             explicit_callsite_bound_includes_endpoint_certify_or_reproduction=True,
             opaque_import_geometry_math_or_actual_runtime_work_unknown=True,
             original_search_budget_complete=False,
             internal_constructions_unknown=True,raw_payload_not_actual_disk_bound=True,
             original_input_and_current_state_not_rebound=True,
             source_SHA={name:sha(path)for name,path in paths.items()},
             no_old_import_model_or_control_execution=True)
        answer=proof.copy()
    except BaseException as error:first=repr(error);proof['first_error']=first
    secondary=None
    try:save_proof(proof)
    except BaseException as error:secondary=repr(error);proof['passed']=False
    if first or secondary:raise BudgetRefusal(first or'ORIGINAL_BUDGET_PROOF_SAVE_FAILED',proof,secondary)
    return answer
