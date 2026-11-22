"""Current stopped source -> one proposal -> full CPP -> independent Python.

Runs in the canonical CPU2 owner under its already-held execution lock. This
module cannot construct a vehicle, admit a round or publish bridge-ready. A
completed private result still requires the separate live-current capability,
fixed-reference and actual evidence/replay qualification before installation.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def load(name,path,source):
    assert sha(path)==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def execute(*,output,source_owner,method,setup,source,lock,save_result,context_out=None,prepare_stage=None,parent_boundary=None):
    result=dict(passed=False,closed=False,first_error=None,secondary_errors=[],
        scientific_revision=12,proposal_executed=False,generation_executed=False,audit_executed=False,
        physical_permission=False,whole_route_passed=False,physical_native=0,replay_native=0,optimizer_calls=0)
    guard=None;phase_sink=None;proposal_store=None;stage=None;leases={}
    try:
        output=Path(output).resolve();assert output.is_relative_to(R/'runs')
        assert (output/'GOAL_BOUND_PRIVATE_ADMISSION.json').is_file(),'GOAL_BOUND_CURRENT_EVENT_NOT_ADMITTED'
        guards=load('v1587_private_admission',C/'capability.py',source)
        guard=guards.Guard(output=output,lock=lock,method=method,prepared_sources=source,source_owner=source_owner)
        writer_module=load('v1587_original_writer',R/'experiments/v1436_pathlib_control_rename/writer_budget.py',source)
        io=load('v1587_original_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py',source)
        codec=load('v1587_original_exact_evidence_codec',R/'experiments/v1507_priest_response_evidence/branch_store.py',source)
        definitions=load('v1587_original_explicit_definitions',R/'experiments/v1530_explicit_we_private_binding/definitions.py',source)
        a=guard.authority
        defs,definition_proof=definitions.load_definitions(source,authority=dict(scope='ORIGINAL_WE_DEFINITIONS_ONLY',
            models_authorized=False,method_origin_authorized=False,boot_id=a['boot_id'],
            absolute_deadline_unix=a['absolute_deadline_unix'],hard_stop_monotonic=a['hard_stop_monotonic']),lock=lock)
        scopes=load('v1587_composed_writer_scopes',C/'scoped_output.py',source)
        root_scope=scopes.Scope(parent=parent_boundary,folder=output,writers=writer_module,io=io,maximum_bytes=2*1024**2,source_identity=digest(source))
        root_writer=root_scope.writer
        def root_save(name,value):
            with root_scope.activate():codec.write_atomic(output/name,codec.encoded(value),root_writer)
        root_save('DEFINITION_BINDING.json',definition_proof)
        origin_module=load('v1587_current_origin',C/'origin.py',source)
        origin=origin_module.prepare(method,defs,guard,lambda p:root_save('CURRENT_ORIGIN.json',p))
        field=load('v1587_fixed_current_time_geometry',C/'timed_field.py',source)
        guard.geometry=field.PreparedField(known=setup['known'],snapshot=method['base_method']['physical_source']['causal_snapshot'],
            origin_native=method['base_method']['fixed_origin_native'],origin_sim_time=method['base_method']['fixed_origin_sim_time'],
            maximum_native=10400,guard=guard)
        root_save('PREPARED_GEOMETRY.json',dict(cells=sorted(guard.geometry.cells),origin=guard.geometry.origin,
            end=guard.geometry.end,geometry_kind=method['geometry_kind'],causal_snapshot_sha256=method['causal_snapshot_sha256']))
        carriers=load('v1587_current_continuous_carriers',C/'carrier.py',source)
        tracker_module=load('v1587_fixed_goal_tracker',C/'tracker.py',source)
        proposals=load('v1587_single_policy_proposal',C/'nominal.py',source)
        proposal_sinks=load('v1587_policy_durable_blocks',C/'proposal_sink.py',source)
        complete=load('v1587_complete_variable_witness',C/'witness.py',source)
        sinks=load('v1587_complete_bounded_sink',C/'sink.py',source)
        gear=method['base_method']['physical_source']['gear_memory']
        def new_tracker():
            return tracker_module.SegmentTracker(method['actual_next_segment'],origin_body=method['base_method']['physical_source']['packet']['body'],
                origin_native=method['base_method']['fixed_origin_native'],origin_sim_time=method['base_method']['fixed_origin_sim_time'])
        # Validate the entry domain before any numerical construction.
        new_tracker()
        parameters_path=R/'experiments/v1159_bounded_steering_load/PARAMETERS.json'
        assert sha(parameters_path)==source[str(parameters_path.relative_to(R))]
        coefficients=json.loads(parameters_path.read_text())['coefficients']
        def new_carrier(kind,stage):
            engine=None
            if kind=='CPP':
                assert Path(defs['engine'].Engine.__init__.__code__.co_filename).resolve()==R/'experiments/v1159_bounded_steering_load/engine.py'
                guard.begin(stage,'Engine');engine=defs['engine'].Engine(setup,coefficients);guard.completed(stage,'Engine')
            return carriers.create(kind=kind,stage=stage,defs=defs,setup=setup,origin=origin,
                gear_memory=gear,method=method,guard=guard,engine=engine)
        leases={}
        def open_writer(name):
            folder=output/name;folder.mkdir(exist_ok=False)
            lease=scopes.Scope(parent=parent_boundary,folder=folder,writers=writer_module,io=io,maximum_bytes=32*1024**2,source_identity=digest(source))
            leases[name]=lease
            return folder,lease.writer
        stage='CPP_PROPOSAL'
        if prepare_stage is not None:prepare_stage(stage)
        guard.start_phase(stage);guard.set_bucket(stage,'nominal')
        folder,writer=open_writer('proposal');result['proposal_executed']=True
        with leases['proposal'].activate()as boundary:
            proposal_store=proposal_sinks.ProposalSink(folder=folder,writer=writer,boundary=boundary,method=method,source=source,
                setup=setup,geometry=guard.geometry)
            proposal=proposals.run(new_carrier('CPP',stage),new_tracker(),guard=guard,
                save_block=proposal_store.block,save_partial=proposal_store.partial,save_result=proposal_store.result)
        proposal_sinks.verify(folder,method=method,source=source,check=guard.check)
        guard.finish_phase(stage);guard.freeze_proposal(proposal,path=folder/'PROPOSAL.json')
        generation_folder=None;generation_reader=None
        for stage,kind,folder_name in [('CPP_GENERATION','CPP','generation'),('PYTHON_AUDIT','PYTHON','audit')]:
            if prepare_stage is not None:prepare_stage(stage)
            guard.start_phase(stage);guard.set_bucket(stage,'nominal');phase_sink=None
            folder,writer=open_writer(folder_name);result[folder_name+'_executed']=True
            with leases[folder_name].activate()as boundary:
                phase_sink=sinks.Sink(folder=folder,writer=writer,boundary=boundary,method=method,proposal=proposal,
                    proposal_sha256=guard.proposal_sha256,stage=stage,source=source)
                answer=complete.run(carrier=new_carrier(kind,stage),tracker=new_tracker(),method=method,setup=setup,
                    proposal=proposal,kind=kind,stage=stage,guard=guard,sink=phase_sink,expected=generation_reader)
                if not answer['passed']:result['first_error']=answer['first_error']or 'PRIVATE_PHASE_RESULT_NOT_SAVED'
                assert answer['passed']and answer['closed']and answer['secondary_errors']==[],'GOAL_BOUND_COMPLETE_PHASE_REFUSED'
            guard.finish_phase(stage)
            filename='GENERATION.json'if stage=='CPP_GENERATION'else'AUDIT.json'
            readback=sinks.reader(folder,method=method,proposal=proposal,proposal_sha256=guard.proposal_sha256,
                stage=stage,result_sha256=sha(folder/filename),source=source,check=guard.check)
            if stage=='CPP_GENERATION':
                generation_folder=folder;generation_reader=readback
                guard.allow_saved_success_audit(path=folder/filename,reader=generation_reader)
            else:
                result['complete_model_reference']=dict(generation_result_sha256=sha(generation_folder/'GENERATION.json'),
                    audit_result_sha256=sha(folder/'AUDIT.json'),proposal_sha256=guard.proposal_sha256,
                    nominal_native=proposal['nominal_native'],generation_seal=generation_reader.seal,audit_seal=readback.seal,
                    fixed_reference_not_fresh_wire=True,actual_current_reserve_qualified=False)
        guard.require_current_event_input(method)
        assert all(sha(R/n)==h for n,h in source.items())
        result['passed']=True
    except BaseException as error:
        result['first_error']=result['first_error']or repr(error);result['traceback']=traceback.format_exc()
        if getattr(error,'secondary',None):result['secondary_errors'].append('source_or_origin_save:'+repr(error.secondary))
        # A carrier-construction failure occurs before witness.run can own its
        # sink. Close that stream here; never fabricate a branch or rerun work.
        if phase_sink is not None and not phase_sink.stream.closed:
            try:
                with leases[folder_name].activate():phase_sink.abort(first_error=result['first_error'],accounting=guard.counts(),branch_name=None,branch_arrays=None,nominal_prefix=None)
            except BaseException as saving:result['secondary_errors'].append('unowned_phase_close:'+repr(saving))
        if proposal_store is not None and not proposal_store.closed:
            try:
                with leases['proposal'].activate():proposal_store.result(dict(passed=False,closed=True,first_error=result['first_error'],accounting=guard.counts()))
            except BaseException as saving:result['secondary_errors'].append('proposal_close:'+repr(saving))
    finally:
        result.update(closed=True,accounting=guard.counts()if guard else dict(models=0,native=0,physical_native=0,replay_native=0))
        try:save_result(result)
        except BaseException as saving:
            result['passed']=False;result['secondary_errors'].append('transaction_result_save:'+repr(saving))
            print('GOAL_BOUND_TRANSACTION_RESULT_SAVE_GAP:'+json.dumps(result,allow_nan=False),flush=True)
    if result['passed']and context_out is not None:
        assert context_out=={}
        context_out.update(guard=guard,defs=defs,method=method,setup=setup,proposal=proposal,
            geometry=guard.geometry,generation_reader=generation_reader,source_owner=source_owner,
            result_path=output/'TRANSACTION_RESULT.json')
    return result
