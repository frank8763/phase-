"""Explicit strict2200 native owner seam from canonical t0 to source event.

No old CuspTransaction/plain200 reserve/model peer is instantiated here. This
owner can acquire source at a real notice but cannot install a method or bridge.
Actual use still needs a separately qualified lifecycle and scientific binder.
"""
import copy
import importlib.util
from pathlib import Path

_s=importlib.util.spec_from_file_location('v1574_owner_io',Path(__file__).with_name('source_io.py'))
io=importlib.util.module_from_spec(_s);_s.loader.exec_module(io)
native_module=io.exact('v1574_exact_strict2200_native',io.R/'experiments/v1567_epoch_scope_target/native_step.py')
capture_module=io.exact('v1574_exact_source_capture',io.C/'capture.py')
session=io.exact('v1574_exact_source_notice',io.C/'event_session.py')


def unavailable(*args,**kwargs):
    raise RuntimeError('CURRENT_2200_LIVE_COMPONENT_NOT_QUALIFIED_OR_INSTALLED')


class CapturedBoundary(RuntimeError):
    def __init__(self,result):
        self.source=result
        super().__init__('CURRENT_SOURCE_CAPTURED_NO_METHOD_OR_PHYSICAL_ADMISSION')


class CanonicalOwner:
    def __init__(self,vehicle,*,task,output,setup,prepared_sources,atomic,check_budget,quota):
        assert task['case_id']=='WEST_EAST'and task['seed']==10060001 and task['controller_plugin']=='RPP'
        assert task['nav2_params']==str(io.R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json')
        assert vehicle.count==0 and float(vehicle.d.time)==0.,'SOURCE_OWNER_MUST_BIND_AT_ACTUAL_T0'
        self.output=Path(output).resolve();assert self.output.is_relative_to(io.R/'runs')
        self.task=copy.deepcopy(task);self.setup=copy.deepcopy(setup);self.sources=copy.deepcopy(prepared_sources)
        self.atomic=atomic;self.quota=quota;self.closed=False;self.bridge=None
        self.last_event_index=-1;self.last_published_native=None;self.capture_attempted=False
        self.preparation_attempted=False;self.prepared_history=None;self.source_refresh=None
        self.native=native_module.NativeStep(vehicle,run_id=task['run_id'],reserve=unavailable,physical_guard=unavailable,evidence_sink=None)
        self.native.before_native_budget=check_budget
        state=capture_module.fullstate(vehicle)
        self.atomic(self.output/'SOURCE_T0_IDENTITY.json',dict(run_id=task['run_id'],canonical_native=0,
            fullstate=state,fullstate_sha256=io.digest(state),numerical_permission=False,physical_permission=False))

    def observe_original_prefix(self,row,*,control_owner):
        assert not self.closed and not self.native.bridge_started
        assert not self.capture_attempted or control_owner=='APPLIED_STOP_TAIL','SOURCE_BOUNDARY_ONLY_ALLOWS_EXPLICIT_CLOSURE_TAIL'
        self.native.observe_original_prefix(row,control_owner=control_owner)

    def envelope(self):
        assert not self.closed
        n=self.native;wire,packet=n.current()
        feedback=dict(native_tick=wire['native_tick'],sim_time=wire['sim_time'],body=wire['body'],
                      encoders=[*packet['steering']['position'],*packet['steering']['velocity']],
                      last_ctrl=packet['controller_memory']['last_ctrl'],integral=packet['controller_memory']['integral'],
                      parked_target=packet['parked_target'],steering_motion_active=packet['steering_motion_active'],
                      gear_memory=dict(gear=n.gear.gear,brake_start=n.gear.brake_start,last_tick=n.gear.last_tick))
        self.last_published_native=n.vehicle.count
        return dict(kind='ROUTE_ACTUAL_FRAME',wire=wire,feedback=feedback,evidence_state_sha256=native_module.state_digest(n.vehicle))

    def prepare_source_notice(self,notice):
        assert not self.closed and not self.native.bridge_started and not self.preparation_attempted and not self.capture_attempted
        self.preparation_attempted=True
        packet=session.current_notice(notice,output=self.output,run_id=self.native.run_id,last_event_index=self.last_event_index)
        request=packet['request'];required=session.old.event.validate_request(request)
        assert request['event']['kind']=='CUSP_NEXT_SEGMENT_CHECK'and request['event_index']==0 and required==250
        v=self.native.vehicle;tail=v.commands[-required:]
        assert len(tail)==required and v.count-request['brake_start']>=required
        assert all(row[1]==row[2]==0. and row[5]is False for row in tail)
        self.quota.retire_grant()
        self.quota.prepare_grant(8*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=1800,external_writers=self.quota.external_writers)
        for name in ('history.py','refresh.py'):
            path=io.C/name
            assert __import__('hashlib').sha256(path.read_bytes()).hexdigest()==self.sources[str(path.relative_to(io.R))]
        history=io.exact('v1612_complete_history_preparation',io.C/'history.py')
        refresh=io.exact('v1612_single_current_refresh',io.C/'refresh.py')
        folder=self.output/'source_capture';folder.mkdir(exist_ok=True)
        try:
            self.prepared_history=history.PreparedHistory(native=self.native,output=self.output,packet=packet,source=self.sources,
                save=lambda proof:self.atomic(folder/'STOPPED_HISTORY_PREPARED.json',proof))
        except BaseException as error:
            first=repr(error);secondary=None
            try:self.atomic(folder/'STOPPED_HISTORY_PREPARATION_ERROR.json',dict(passed=False,first_error=first,models=0,
                applied_native=self.native.applied,current_capture_passed=False,numerical_permission=False,physical_permission=False))
            except BaseException as save_error:secondary=repr(save_error)
            if secondary is not None:error.preparation_save_secondary=secondary
            raise
        self.source_refresh=refresh.Refresh(self.prepared_history,initial_notice=notice,prepared_monotonic=__import__('time').monotonic())
        return self.source_refresh

    def on_cusp(self,notice):
        assert not self.closed and not self.native.bridge_started and not self.capture_attempted
        # Any failure closes this source transaction; do not request a second
        # notice/wire, install old certificates or start modeled ROS.
        self.capture_attempted=True;first=None;secondary=[];answer=None
        try:
            packet=session.current_notice(notice,output=self.output,run_id=self.native.run_id,last_event_index=self.last_event_index)
            assert self.source_refresh is not None and self.prepared_history is not None
            self.source_refresh.accept_final(packet,notice)
            request=packet['request'];required=session.old.event.validate_request(request)
            v=self.native.vehicle;tail=v.commands[-required:]
            assert v.count-request['brake_start']>=required and len(tail)==required
            assert all(row[1]==row[2]==0. and row[5]is False for row in tail),'ACTUAL_EVENT_REQUIRED_ZERO_TAIL'
            assert max(abs(x)for x in v.body()[3:])<=.003
            assert max(abs(x)for x in v.steering_sample()[2:])<=.03 and max(abs(x)for x in v.adapter.last[2:])<=1e-10
            folder=self.output/'source_capture';folder.mkdir(exist_ok=True)
            answer=capture_module.capture(self.native,request['actual']['wire'],run_id=self.native.run_id,
                prepared_sources=self.sources,causal_source=packet['current_causal_source'],request=request,
                output=self.output,setup=self.setup,prepared_history=self.prepared_history,save_proof=lambda proof:self.atomic(folder/'CAPTURE_PROOF.json',proof))
            self.atomic(folder/'CAPTURED_SOURCE.json',answer)
            self.last_event_index=notice['event_index']
        except BaseException as error:
            first=repr(error)
            if isinstance(error,capture_module.CaptureRefusal)and error.secondary:
                secondary.append(dict(stage='CAPTURE_PROOF_SAVE',error=error.secondary))
        try:
            self.atomic(self.output/'CURRENT_SOURCE_TRANSACTION_CLOSED.json',dict(closed=True,first_error=first,
                source_captured=answer is not None,actual_runtime_qualified=False,method_domain_accepted=False,
                numerical_permission=False,physical_permission=False,actual=self.native.exact_accounting()))
        except BaseException as error:secondary.append(dict(stage='TRANSACTION_CLOSE_SAVE',error=repr(error)))
        if first or secondary:
            error=RuntimeError(first or 'SOURCE_TRANSACTION_CLOSE_SAVE_FAILED');error.secondary_errors=secondary;raise error
        raise CapturedBoundary(answer)

    def close(self):
        self.closed=True
        self.atomic(self.output/'CANONICAL_OWNER_CLOSED.json',dict(closed=True,actual=self.native.exact_accounting(),
            strict2200_consumer_source=str((io.R/'experiments/v1567_epoch_scope_target/native_step.py').relative_to(io.R)),
            live_components_installed=bool(self.native.bridge_started),
            bridge_object_present=self.bridge is not None,
            physical_admission_granted_by_source_owner=False))
