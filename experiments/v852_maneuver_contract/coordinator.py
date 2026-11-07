"""Common admission seam for ordinary/return proposals and committed receipts.

The model-dependent safety layer must produce and retain the full certificate.
This module coordinates metadata and returns existing commands without writing
physical state. It is a new offline-qualified control core, not a deployed loop.
"""
import copy
import numpy as np
from maneuver import ReferenceOwner,evaluate,CommittedPrefix


class Coordinator:
    def __init__(self):self.reference=ReferenceOwner();self.committed=None;self.last_accepted=None

    def install_reference(self,*args,**kwargs):
        assert self.committed is None or self.committed.replacement_allowed,'UNFINISHED_EXECUTION_COMMITMENT'
        result=self.reference.install(*args,**kwargs)
        self._rebase_retained('CAUSAL_REFERENCE_RENEWAL',self.reference.history[-1])
        return result

    def _rebase_retained(self,reason,evidence):
        # A causal new reference or actual settled cusp changes the merit's
        # coordinate system, never the retained physical states or controls.
        if self.last_accepted is None:return
        old=self.last_accepted['maneuver_contract'];new=dict(old)
        new['previous_segment_key']=old['segment_key'];new['segment_key']=self.reference.segment().key
        new['reprojection']=dict(reason=reason,evidence=copy.deepcopy(evidence))
        self.last_accepted=dict(self.last_accepted,maneuver_contract=new)

    def try_certificate(self,certificate,entry_qpos,entry_qvel,entry_time,*,role,old=None,old_cursor=None):
        assert role in ['ORDINARY','BACKUP_RETURN']
        if self.committed is not None and not self.committed.replacement_allowed:
            assert self.committed.segment.key==self.reference.segment().key
            return dict(status='CONTINUE_COMMITTED32',accepted=False,role=role,command=self.committed.next_command().tolist(),heavy_candidate_search_required=False)
        segment=self.reference.segment()
        if self.last_accepted is not None:
            assert old is None and old_cursor is None,'RETAINED_COMPARISON_IS_OWNED_BY_COORDINATOR'
            assert self.committed.native>=32
            old=self.last_accepted;old_cursor=self.committed.native-8
        decision=evaluate(segment,certificate,entry_qpos,entry_qvel,entry_time,old=old,old_cursor=old_cursor)
        if not decision['normal_allowed']:return dict(status='RETAIN_OLD_OR_EXPLICIT_RECOVERY_REQUIRED',accepted=False,role=role,decision=decision)
        selected=copy.deepcopy(certificate)
        for key in ['qpos','qvel','controls','initial_qpos','initial_qvel','prefix_initial_qpos','prefix_command','prefix_poses']:
            selected[key]=np.array(selected[key],copy=True);selected[key].flags.writeable=False
        selected['maneuver_contract']=dict(segment_key=segment.key,reference_id=segment.reference_id,role=role,decision=copy.deepcopy(decision))
        self.committed=CommittedPrefix(segment,selected,decision,entry_qpos);self.last_accepted=selected
        return dict(status='NEW_COMPLETE_CERTIFICATE_COMMITTED32',accepted=True,role=role,decision=decision,command=self.committed.next_command().tolist(),new_physical_validation_claimed=False)

    def actual_public_receipt(self,qpos,qvel,applied_command):
        assert self.committed is not None and self.last_accepted is not None
        if not self.committed.replacement_allowed:
            assert self.committed.segment.key==self.reference.segment().key
            return self.committed.receipt(qpos,qvel,applied_command)
        # Continue the original unmodified remainder when no better complete
        # certificate is available. Do not erase it at the 32-tick boundary.
        n=self.committed.native+8;assert n<=328
        expected_q=self.last_accepted['qpos'][n-9];expected_v=self.last_accepted['qvel'][n-9]
        assert max(np.max(abs(np.asarray(qpos)-expected_q)),np.max(abs(np.asarray(qvel)-expected_v)))<=1e-8,'RETAINED_ACTUAL_STATE_MISMATCH'
        assert np.max(abs(np.asarray(applied_command)-self.retained_command()))<=1e-12,'RETAINED_ACTUAL_CTRL_MISMATCH'
        self.committed.native=n
        if n==328:self.last_accepted=None
        return dict(actual_native=n,complete=n==328,physical_state_written=False)

    def retained_command(self):
        assert self.last_accepted is not None and self.committed is not None
        if not self.committed.replacement_allowed:return self.committed.next_command()
        assert self.committed.native<328
        return self.last_accepted['controls'][self.committed.native-8].copy()

    def backup_finished(self):
        assert self.last_accepted is None,'RETAINED_TAIL_NOT_FINISHED'
        return self.reference.after_backup_finished()

    def advance_cusp(self,pose,qvel):
        assert self.committed is None or self.committed.replacement_allowed,'UNFINISHED_EXECUTION_COMMITMENT'
        self.reference.advance_cusp(pose,qvel)
        self._rebase_retained('ACTUAL_SETTLED_CUSP',dict(pose=np.asarray(pose).tolist(),qvel=np.asarray(qvel).tolist()))
