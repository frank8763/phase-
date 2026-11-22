"""Once complete production SOURCE target; runtime remains unexecuted."""
import ast,fcntl,importlib.abc,importlib.util,json,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1587_target_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def main():
    start=time.monotonic();resources=c.bootstrap();c.guard()
    lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),models_authorized=False),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,
        phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,original_Gear_calls=0,
        actual_capture_qualified=False,actual_runtime_qualified=False,complete_actual_source_target_passed=False,whole_route_passed=False)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory'}:raise AssertionError('COMPLETE_SOURCE_NO_NUMERICS:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert not(path.name in {'model.py','coupled_model.py','prediction.py','engine.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','step','simulate','compute'}),'SOURCE_MODEL_OR_ALLOCATOR_FORBIDDEN'
                assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future'},'SOURCE_NUMERICAL_BINDING_FORBIDDEN'
                assert not('gear_handoff.py'in str(path)and frame.f_code.co_name=='select'),'SOURCE_ORIGINAL_GEAR_FORBIDDEN'
            assert time.monotonic()-start<120,'SOURCE_TARGET_TIME_CAP'
    def audit(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            path=Path(args[0]);assert not path.is_absolute()or not path.resolve().is_relative_to(c.R),'SOURCE_PHASE_FFI_FORBIDDEN'
    sys.addaudithook(audit);sys.setprofile(profile)
    try:
        source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
        target=c.O/'source_target';target.mkdir(exist_ok=False)
        wm=c.load('v1587_unchanged_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1587_unchanged_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'));negative=[]
        def refused(name,fn):
            try:fn()
            except (AssertionError,KeyError,ValueError,RuntimeError,OSError,AttributeError)as error:
                row=dict(name=name,error=repr(error),secondary=getattr(error,'secondary',None),scope='SOFTWARE_OR_UNADMITTED_SOURCE_ONLY')
                negative.append(row);c.put(target/('REFUSAL_'+name+'.json'),row);return error
            raise AssertionError('NEW_COMPLETE_SOURCE_NEGATIVE_ACCEPTED:'+name)
        with io.OutputBoundary(target,writer.reserve):
            save=lambda path,value:c.put(path,value,maximum=128*1024)
            interfaces,method=c.load('v1587_new_source_interfaces',C/'source_cases.py').run(c,source,target,save,refused)
            phase=c.load('v1587_new_variable_phase_source',C/'phase_cases.py').run(c,source,target,save,refused,method)
            coverage=c.load('v1587_exact_writer_hook_reuse',C/'writer_coverage.py').coverage(source)
            save(target/'WRITER_SOURCE_COVERAGE.json',coverage)
            old=c.R/'runs/v1579_canonical_digest_scope';review=c.read(old/'CLOSED_REVIEW.json')
            assert review['closed']and not review['passed']and review['saved_remaining_storage_subtarget_passed']
            for name,key in [('source_target/QUALIFICATION.json','subtarget_sha256'),('source_target/actual_software/CURRENT_CLOSED.json','software_current_closed_sha256'),('source_target/actual_software/CURRENT.bin','software_current_stream_sha256')]:assert c.sha(old/name)==review[key]
            assert c.read(old/'source_target/QUALIFICATION.json')['software_only']
            reused=[]
            for name in ['tracker.py','carrier.py','witness.py','gates.py','current_reserve.py','reference.py','actual_sink.py','scoped_output.py','transaction.py','close.py','accounting.py','lifecycle.py','canonical_owner.py','native_driver.py','pump.py','actual_audit.py','legacy_actual_audit.py','recorded.py','capability.py','live_guard.py','execution.py','stream.py','sink.py','budget.py','base_quota.py','quota.py','supervisor.py','native_entry.py','route_ros.py','route_context.py','round_barrier.py']:
                before=(c.R/'experiments/v1585_fifteen_gib_runtime'/name).read_text()
                after=(C/name).read_text().replace('v1587_complete_runtime_source','v1585_fifteen_gib_runtime').replace('v1587','v1585')
                assert ast.dump(ast.parse(before))==ast.dump(ast.parse(after)),name
                reused.append(dict(file=name,current_sha256=c.sha(C/name)))
            edges={
                'canonical_owner.py':['current.describe(captured,request,proof','transaction.execute(','self.bridge=install_live('],
                'lifecycle.py':["C/'canonical_owner.py'","C/'components.py'",'self.components.install()'],
                'components.py':['install.before_current_engine(context,native)','reserve.CurrentReserve(','n.reserve=self.reserve','self.execution_module.Execution('],
                'native_driver.py':['life.Lifecycle(','owner.bind_initialized_t0(','pump_module.Pump(','module.integrated('],
                'actual_audit.py':['binding.verify(','previous.integrated('],
                'transaction.py':['guard.allow_saved_success_audit(','readback=sinks.reader(',"if not answer['passed']",'save_result(result)']}
            for name,needles in edges.items():assert all(value in (C/name).read_text()for value in needles),name
            save(target/'QUALIFICATION.json',dict(passed=True,software_only=True,interfaces=interfaces,phase=phase,negative_cases=negative,source_call_edges=edges,reused_sources=reused,source_interfaces_not_runtime_success=True,model_native=0,physical_native=0))
            save(target/'TASK.json',c.read(C/'TASKS.json')[0])
        native=c.load('v1587_real_unadmitted_native_CLI',C/'native_entry.py');prior=sys.argv;sys.argv=['native_entry',str(target/'TASK.json')]
        try:assert native.main()==1
        finally:sys.argv=prior
        denial=c.read(c.O/'unadmitted/CLI_REFUSAL.json')
        assert denial['closed']and not denial['passed']and 'GOAL_BOUND_ACTUAL_RUNTIME_NOT_ADMITTED'in denial['first_error']
        assert denial['source_binding_before_factory']and not denial['actual_counts_unknown']
        assert not(c.O/'ROUND_WINDOW.json').exists()and not(c.O/'ACTUAL_ONCE_CLAIM.json').exists()
        gates={name:True for name in ('goal_bound_policy','variable_complete_witness','unknown_and_first_error','current_source_runtime_binding','bounded_production_CLI','current_CPP2200_API','actual_durable_policy_and_reference','actual_lifecycle_and_replay_source_pipeline','once_owner_and_caps')}
        assert all(c.sha(c.R/n)==h for n,h in source.items())
        c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,models_authorized=False,complete_actual_source_target_passed=True,actual_capture_qualified=False,actual_runtime_qualified=False,whole_route_passed=False),maximum=4*1024**2)
        result.update(passed=True,source_gates=gates,complete_actual_source_target_passed=True,writer_source_coverage={k:v['source_hook_coverage_qualified']for k,v in coverage.items()},writer_coverage_proof_sha256=c.sha(target/'WRITER_SOURCE_COVERAGE.json'),source_members=len(source),negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources,prior_proof_reuse_not_suite_rerun=True,runtime_numerical_outcomes_unexecuted=True)
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
    print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}))
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
