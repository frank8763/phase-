"""Variable witness dependency/partial-source closure, no model/codec suite."""
import copy
from types import SimpleNamespace as NS


def run(c,source,target,save,refused,method):
    witness=c.load('v1587_source_variable_counts',c.C/'witness.py')
    sinks=c.load('v1587_source_variable_sink',c.C/'sink.py')
    guards=c.load('v1587_source_private_dependency',c.C/'capability.py')
    work=c.load('v1587_source_work',c.C/'work.py')
    table=[]
    for n in (2200,2205,8200):
        b=witness.budget(n);proposal=dict(nominal_native=n,motion_native=n-2200)
        names=sinks.names(proposal)
        assert len(names)==2*b['boundaries']+1 and names[-1]=='nominal'
        assert b['full_phase_native']==4400*b['boundaries']+2*n
        assert b['full_phase_native']<=5300800 and b['full_tail_native']==2200
        table.append(dict(nominal_native=n,branches=len(names),budget=b))
    refused('variable_non5_count',lambda:witness.boundaries(2201))
    # These are pure bookkeeping requests, no FFI invocation or stopping run.
    ledger=work.Work(native=2200,nominal=0,witness=2200,copies=0,engine=0,predictor=0,batch_calls=1)
    ledger.bucket('witness');ledger.claim(1)
    refused('unknown_work_not_retryable',lambda:ledger.claim(1))
    unknown=ledger.counts();assert unknown['native']==0 and unknown['inflight_unknown']
    ledger.acknowledge(1);ledger.claim(2199,batch=True)
    refused('batch_unknown_blocks_close',ledger.complete)
    ledger.acknowledge(2199,batch=True);ledger.complete()
    save(target/'SOFTWARE_VARIABLE_COUNTS.json',dict(software_no_model_calls=True,budgets=table,inflight_snapshot=unknown,acknowledged_metadata=ledger.counts(),actual_native=0,model_native=0))

    # Invoke the production dependency predicate on explicit software ports.
    # No Guard constructor/parent admission/definition binding is bypassed in
    # production; these unconstructed objects cannot be supplied to a launcher.
    g=object.__new__(guards.Guard);g.method=method;g.input_sha=method['response_method_sha256']
    g.check=lambda:None;g.owner=NS(verify_stopped_source=lambda m: m==method)
    g.active_phase=None;g.phases_started=['CPP_PROPOSAL','CPP_GENERATION']
    g.proposal_sha256='e'*64;g.generation_result_sha256=None
    completed=[];g.ledgers={'CPP_GENERATION':NS(complete=lambda:completed.append('complete'))}
    result=dict(passed=True,closed=True,first_error=None,secondary_errors=[],response_method_sha256=g.input_sha)
    path=target/'SOFTWARE_GENERATION.json';save(path,result)
    reader=NS(seal=dict(generation_result_sha256=c.sha(path),binding=dict(stage='CPP_GENERATION',response_method_sha256=g.input_sha,proposal_sha256='e'*64)))
    g.allow_saved_success_audit(path=path,reader=reader)
    assert g.generation_result_sha256==c.sha(path) and completed==['complete']
    for name,key,value in [('failed_generation','passed',False),('generation_secondary','secondary_errors',['SOFTWARE_CLOSE_GAP']),('generation_wrong_input','response_method_sha256','0'*64)]:
        bad=copy.deepcopy(result);bad[key]=value;badpath=target/(name+'.json');save(badpath,bad)
        refused(name,lambda badpath=badpath:g.allow_saved_success_audit(path=badpath,reader=reader))
    reader.seal['generation_result_sha256']='0'*64
    refused('generation_reader_wrong_result',lambda:g.allow_saved_success_audit(path=path,reader=reader))
    reader.seal['generation_result_sha256']=c.sha(path);reader.seal['binding']['proposal_sha256']='0'*64
    refused('generation_reader_wrong_proposal',lambda:g.allow_saved_success_audit(path=path,reader=reader))
    refused('private_guard_no_live_capability',lambda:g.require_live_component('CURRENT_CPP_RESERVE',method))
    g.generation_result_sha256=None;g.authority=dict(phase_seconds=dict(PYTHON_AUDIT=1800),absolute_deadline_unix=1795395600,hard_stop_monotonic=1e12)
    g.geometry=object();g.proposal={}
    refused('audit_not_started_without_generation_dependency',lambda:g.start_phase('PYTHON_AUDIT'))
    assert g.active_phase is None

    # Exercise the real partial-close adapter with an explicitly SOFTWARE
    # stream port. An emergency-save failure must not suppress stream close.
    closed=[]
    def denied(*args,**kwargs):raise OSError('SOFTWARE_PARTIAL_SAVE_DENIED')
    stream=NS(emergency=denied,abort=lambda **kwargs:closed.append(kwargs))
    sink=object.__new__(sinks.Sink);sink.aborted=False;sink.stream=stream
    err=refused('partial_first_and_close_preserved',lambda:sink.abort(first_error='SOFTWARE_FIRST_ERROR',accounting={'inflight_unknown':True},branch_name='partial',branch_arrays={'SOFTWARE':True},nominal_prefix=None))
    assert sink.aborted and len(closed)==1 and closed[0]['first_error']=='SOFTWARE_FIRST_ERROR'
    refused('partial_not_retried',lambda:sink.abort(first_error='SECOND',accounting={},branch_name=None,branch_arrays=None,nominal_prefix=None))
    save(target/'SOFTWARE_PHASE_DEPENDENCY.json',dict(passed=True,software_only=True,partial_close=closed,secondary=str(err),actual_native=0,model_native=0,generation_reader_dependency_checked=True))
    return dict(variable_complete_witness=True,unknown_and_first_error=True,
        runtime_model_arrays_tested=False,codec_or_old_storage_suite_rerun=False)
