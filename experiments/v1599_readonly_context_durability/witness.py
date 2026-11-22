"""Complete fixed-policy witnesses from own outputs at every native block.

Timing comes from ONE nominal proposal, not parameter search. Each nominal and
prospective block computes the registered tracker once and holds its raw request
for five native steps. The complete final2200-zero block remains one boundary.
No expected state/control is ever a numerical input.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def boundaries(nominal_native):
    assert type(nominal_native)is int and 2200<=nominal_native<=8200 and nominal_native%5==0
    moving=nominal_native-2200
    return tuple([(offset,5)for offset in range(0,moving,5)]+[(moving,2200)])


def budget(nominal_native):
    cuts=boundaries(nominal_native);b=len(cuts)
    return dict(nominal_native=nominal_native,boundaries=b,copies=2*b,
        current_and_prospective_native=4400*b+nominal_native,
        full_phase_native=4400*b+2*nominal_native,
        batch_zero_calls=2*b,batch_native=2199*2*b,
        raw13array_bytes_per_phase=216*(nominal_native+1)+168*nominal_native+
            sum(216*(2201)+168*2200+216*(2201+n)+168*(2200+n)for _,n in cuts),
        full_tail_native=2200,complete200minimum=True,compression_fit_not_guaranteed=True)


def load(name,path,guard):
    guard.check();assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def append_block(branch,carrier,tracker,*,offset,count,moving_native,guard):
    assert count in (5,2200)
    if offset>=moving_native:
        assert count==2200
        for _ in range(2200):branch.advance(carrier,(0.,0.,0))
        return
    before=carrier.snapshot();state=before['state'];body=[float(state[k])for k in (0,1,2,3,5)]
    decision=tracker.select(body,native_tick=before['native'],sim_time=before['sim_time'])
    # Frozen stop time is an obligation, not a reason to silently consume more
    # motions when the independently carried policy arrives differently.
    assert not decision['terminal_requested'],'FIXED_STOP_TIMING_REACHED_EARLY_IN_FULL_WITNESS'
    raw=tuple(decision['raw_row']);start=len(branch.rows)
    for _ in range(5):branch.advance(carrier,raw)
    digest=hashlib.sha256()
    for row in branch.rows[start:]:
        import json
        digest.update(json.dumps(dict(native=row['before']['native'],raw=list(row['raw']),
            applied=list(row['applied'])),sort_keys=True,separators=(',',':'),allow_nan=False).encode())
    tracker.commit(decision,applied_native=5,applied_request_receipts_sha256=digest.hexdigest())


def run(*,carrier,tracker,method,setup,proposal,kind,stage,guard,sink,expected=None):
    guard.require_complete_witness(proposal,stage=stage,kind=kind)
    schema=load('v1599_original13array_schema',R/'experiments/v1552_complete_canonical_witness/evidence.py',guard)
    carrier_module=load('v1599_explicit_carrier',C/'carrier.py',guard)
    checks=load('v1599_complete_method_gates',C/'gates.py',guard)
    compare=load('v1599_original_independent_array_compare',R/'experiments/v1552_complete_canonical_witness/witness.py',guard).compare
    cuts=boundaries(proposal['nominal_native']);moving=proposal['motion_native']
    assert moving==proposal['nominal_native']-2200
    nominal=schema.Branch(carrier);active=None;child=None;name=None;saved=set();first=None
    result=dict(passed=False,closed=False,first_error=None,secondary_errors=[],stage=stage,
        complete_pairs=0,complete_nominal_native=0,response_method_sha256=method['response_method_sha256'],
        physical_native=0,replay_native=0,whole_route_passed=False)
    try:
        for index,(offset,count)in enumerate(cuts):
            assert carrier.native==method['base_method']['fixed_origin_native']+offset
            for tag in ('current','prospective'):
                guard.set_bucket(stage,'witness');name=f'b{index:04d}_{tag}'
                child=carrier.fork();active=schema.Branch(child)
                if tag=='prospective':
                    branch_tracker=tracker.fork()
                    append_block(active,child,branch_tracker,offset=offset,count=count,moving_native=moving,guard=guard)
                carrier_module.fill_stop(child,active,kind=kind)
                arrays=active.arrays();sink.data(name,arrays,accounting=guard.counts(),complete=True);saved.add(name)
                proof=checks.evaluate(arrays,method,setup,guard.geometry,expected_native=2200+(count if tag=='prospective'else 0),
                    zero_suffix=2200,raw_current_only=tag=='current')
                independent=None if expected is None else compare(arrays,expected.arrays(name))
                sink.proof(name,dict(safety=proof,comparison=independent,arrays_saved_before_gate=True))
                assert proof['passed'],'FULL_CURRENT_OR_PROSPECTIVE_GATE_REFUSED:'+name
                assert independent is None or independent['passed'],'INDEPENDENT_CURRENT_METHOD_DIFFERED:'+name
                active=None
            result['complete_pairs']+=1;guard.set_bucket(stage,'nominal')
            append_block(nominal,carrier,tracker,offset=offset,count=count,moving_native=moving,guard=guard)
            result['complete_nominal_native']+=count
        name='nominal';active=nominal;arrays=nominal.arrays()
        sink.data(name,arrays,accounting=guard.counts(),complete=True);saved.add(name)
        proof=checks.evaluate(arrays,method,setup,guard.geometry,expected_native=proposal['nominal_native'],zero_suffix=2200,raw_current_only=False)
        endpoint=checks.endpoint(arrays,method)
        independent=None if expected is None else compare(arrays,expected.arrays(name))
        sink.proof(name,dict(safety=proof,endpoint=endpoint,comparison=independent,arrays_saved_before_gate=True))
        assert proof['passed']and endpoint['passed'],'COMPLETE_NOMINAL_OR_SEGMENT_ENDPOINT_REFUSED'
        assert independent is None or independent['passed'],'INDEPENDENT_NOMINAL_DIFFERED'
        assert result['complete_pairs']==len(cuts)
        guard.require_complete_counts(stage,budget(proposal['nominal_native']))
        result.update(passed=True,complete_arrays_saved_before_gates=True)
    except BaseException as error:
        first=repr(error);result.update(first_error=first,traceback=traceback.format_exc())
        if child is not None and getattr(child,'batch_return',None)is not None:
            try:sink.raw_return(child,accounting=guard.counts())
            except BaseException as saving:result['secondary_errors'].append('raw_return:'+repr(saving))
        try:
            sink.abort(first_error=first,accounting=guard.counts(),
                branch_name=name,branch_arrays=None if active is None or name in saved else active.arrays(),
                nominal_prefix=None if nominal is active or 'nominal'in saved else nominal.arrays())
        except BaseException as saving:result['secondary_errors'].append('prefix_abort_save:'+repr(saving))
    finally:
        result.update(closed=True,accounting=guard.counts())
        try:sink.result(result)
        except BaseException as saving:result['passed']=False;result['secondary_errors'].append('phase_result_save:'+repr(saving))
    return result
