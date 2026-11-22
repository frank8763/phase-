"""Canonical t0 source owner -> real original CUSP -> goal-bound transaction.

This event boundary intentionally does not install a live bridge. New source
and complete private success cannot bypass the missing actual-current/runtime
qualification. No original model peer or old plain200 transaction is used.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def exact(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class PrivateBoundary(RuntimeError):
    def __init__(self,result):self.result=result;super().__init__('CURRENT_GOAL_BOUND_PRIVATE_CLOSED_NO_LIVE_INSTALLATION')


def create(vehicle,*,task,output,setup,prepared_sources,atomic,check_budget,quota,lock,private_admission,install_live,prepare_stage):
    old=exact('v1608_exact_canonical_source_owner',C/'capture_owner.py',prepared_sources)
    current=exact('v1608_current_input_binder',C/'current_input.py',prepared_sources)
    resolver=exact('v1608_current_stopped_source',C/'source_owner.py',prepared_sources)
    transaction=exact('v1608_single_goal_bound_transaction',C/'transaction.py',prepared_sources)
    registration_path=R/'runs/v1577_goal_bound_segment_bridge/SCIENTIFIC_REVISION_REGISTRATION.json'
    assert hashlib.sha256(registration_path.read_bytes()).hexdigest()==prepared_sources[str(registration_path.relative_to(R))]
    registration=json.loads(registration_path.read_text())
    # This callback must be the new lifecycle's once-budgeted admission
    # writer, not a supplied flag or a legacy window/60000tick task template.
    callback_path=Path(private_admission.__code__.co_filename).resolve()
    assert callback_path==C/'lifecycle.py'and hashlib.sha256(callback_path.read_bytes()).hexdigest()==prepared_sources[str(callback_path.relative_to(R))]
    assert Path(install_live.__code__.co_filename).resolve()==C/'lifecycle.py'
    assert Path(prepare_stage.__code__.co_filename).resolve()==C/'lifecycle.py'
    class CanonicalOwner(old.CanonicalOwner):
        def on_cusp(self,notice):
            try:super().on_cusp(notice)
            except old.CapturedBoundary as boundary:
                captured=boundary.source
            else:raise RuntimeError('CANONICAL_SOURCE_TRANSACTION_DID_NOT_CLOSE_AT_CAPTURE')
            # Any other exception propagates. No second capture is attempted.
            source_folder=self.output/'source_capture'
            proof=json.loads((source_folder/'CAPTURE_PROOF.json').read_text())
            event=old.session.current_notice(notice,output=self.output,run_id=self.native.run_id,
                last_event_index=self.last_event_index-1)
            request=event['request']
            method=current.describe(captured,request,proof,registration=registration,
                registration_sha256=digest(registration),source_manifest_sha256=digest(prepared_sources),
                save_proof=lambda p:self.atomic(source_folder/'GOAL_BOUND_INPUT_PROOF.json',p))
            self.atomic(source_folder/'GOAL_BOUND_METHOD.json',method)
            stopped=resolver.StoppedSource(canonical_owner=self,capture=captured,proof=proof,request=request,
                prepared_sources=prepared_sources,output=self.output,setup=setup)
            stopped.verify_stopped_source(method)
            folder=self.output/'goal_bound_private';folder.mkdir(exist_ok=False)
            private_admission(method=method,stopped_source=stopped,output=folder,lock=lock)
            context={}
            result=transaction.execute(output=folder,source_owner=stopped,method=method,setup=setup,
                source=prepared_sources,lock=lock,save_result=lambda p:self.atomic(folder/'TRANSACTION_RESULT.json',p),context_out=context,prepare_stage=prepare_stage,parent_boundary=quota.output_boundary)
            if not result['passed']:raise PrivateBoundary(result)
            self.bridge=install_live(context=context,canonical_owner=self)
    return CanonicalOwner(vehicle,task=task,output=output,setup=setup,prepared_sources=prepared_sources,
        atomic=atomic,check_budget=check_budget,quota=quota)
