"""Adversarial public interfaces, immutable contracts and old-tail ownership.

Pure saved-array/synthetic inputs, no physical model or integration. A receipt
checks public endpoints; the original every-native-tick auditor is still needed.
"""
import argparse,copy,hashlib,json,signal
from pathlib import Path
import numpy as np
from qualify import certificate,qpos
from maneuver import ReferenceOwner,evaluate,CommittedPrefix
from coordinator import Coordinator

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('OFFLINE_BOUNDARIES_180S')));signal.alarm(180)
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=R/'runs/v852_maneuver_contract/boundaries_final01');out=parser.parse_args().output.resolve();assert out.is_relative_to(R/'runs/v852_maneuver_contract');out.mkdir(parents=True,exist_ok=False)
    passed=[]
    def rejected(label,call):
        try:call()
        except (AssertionError,ValueError):passed.append(label);return
        raise AssertionError('UNREJECTED_BOUNDARY:'+label)
    path=np.array([[0.,0.,0.,1.],[-.5,0.,0.,-1.],[-1.,0.,0.,-1.],[-.5,0.,0.,1.],[2.,0.,0.,1.]])
    c=certificate(-.06,-.3,x8=-.01);controller=Coordinator();controller.install_reference(path,[2.,0.],0)
    assert controller.try_certificate(c,qpos(0.),np.zeros(6),0.,role='ORDINARY')['accepted']
    stored=controller.last_accepted['qpos'].copy();c['qpos'][:]=12.;assert np.array_equal(controller.last_accepted['qpos'],stored);passed.append('caller_mutation_does_not_change_accepted_certificate')
    rejected('accepted_arrays_are_readonly',lambda:controller.last_accepted['qpos'].__setitem__((0,0),12.))
    rejected('premature_reference_renewal',lambda:controller.install_reference(path,[2.,0.],12,cause='CURRENT_GEOMETRY_INVALID',observed_this_frame=True,evidence_id='x'))
    rejected('premature_backup_finish',controller.backup_finished)
    source=controller.last_accepted
    for n in [8,16,24,32]:
        q=source['initial_qpos']if n==8 else source['qpos'][n-9];v=source['initial_qvel']if n==8 else source['qvel'][n-9]
        controller.actual_public_receipt(q,v,controller.retained_command())
    # A worse new full endpoint must be compared with the owned old endpoint
    # even when a caller supplies no old argument.
    entry=source['qpos'][23].copy();new=certificate(-.1,-.2,x8=-.07,entry=entry);new.update(created_time=.32,start_time=.40)
    decision=controller.try_certificate(new,entry,source['qvel'][23],.32,role='BACKUP_RETURN')
    assert not decision['accepted']and decision['decision']['reason']=='NO_IMPROVEMENT_OVER_RETAINED';passed.append('owned_remaining_endpoint_compared_without_optional_caller_argument')
    rejected('caller_cannot_override_owned_remainder',lambda:controller.try_certificate(new,entry,source['qvel'][23],.32,role='BACKUP_RETURN',old=new,old_cursor=0))
    rejected('failed_remaining_receipt_is_transactional',lambda:controller.actual_public_receipt(source['qpos'][31]+.001,source['qvel'][31],controller.retained_command()))
    assert controller.committed.native==32 and controller.last_accepted is source
    oldq=source['qpos'].copy();oldctrl=source['controls'].copy();oldkey=source['maneuver_contract']['segment_key']
    renewed=path.copy();renewed[-1,1]=.1
    controller.install_reference(renewed,[2.,0.],12,cause='CURRENT_GEOMETRY_INVALID',observed_this_frame=True,evidence_id='causal_12')
    assert controller.last_accepted['maneuver_contract']['previous_segment_key']==oldkey and controller.last_accepted['maneuver_contract']['segment_key']==controller.reference.segment().key
    assert np.array_equal(controller.last_accepted['qpos'],oldq)and np.array_equal(controller.last_accepted['controls'],oldctrl);passed.append('causal_reference_renewal_reprojects_old_merit_without_changing_physical_tail')
    for n in range(40,329,8):controller.actual_public_receipt(source['qpos'][n-9],source['qvel'][n-9],controller.retained_command())
    assert controller.last_accepted is None and controller.backup_finished()['reference_retained'];passed.append('all328_public_endpoint_receipts_keep_full_remainder_then_release')
    owner=ReferenceOwner();owner.install(path,[2.,0.],0);segment=owner.segment();valid=certificate(-.06,-.3,x8=-.01)
    for label,change in [
        ('nonconstant_native_control_inside_public_action',lambda x:x['controls'].__setitem__((1,0),.01)),
        ('nonfinite_prefix',lambda x:x['prefix_poses'].__setitem__((0,0),np.nan)),
        ('prefix_tail_time_gap',lambda x:x.__setitem__('start_time',.09)),
        ('wrong_velocity_shape',lambda x:x.__setitem__('qvel',np.zeros((320,1))))]:
        bad=copy.deepcopy(valid);change(bad);rejected(label,lambda bad=bad:evaluate(segment,bad,qpos(0.),np.zeros(6),0.))
    # Force a final progress failure after matching states: the receipt must not
    # mark the commitment complete on its exceptional path.
    decision=evaluate(segment,valid,qpos(0.),np.zeros(6),0.);committed=CommittedPrefix(segment,valid,decision,qpos(0.))
    for n in [8,16,24]:
        q=valid['initial_qpos']if n==8 else valid['qpos'][n-9];v=valid['initial_qvel']if n==8 else valid['qvel'][n-9];committed.receipt(q,v,committed.next_command())
    committed.origin_merit+=2.
    rejected('failed_final_progress_receipt_is_transactional',lambda:committed.receipt(valid['qpos'][23],valid['qvel'][23],committed.next_command()))
    assert committed.native==24 and not committed.replacement_allowed
    value=dict(status='ADVERSARIAL_PUBLIC_BOUNDARIES_ZERO_MODEL_PASS',passed=True,checks=passed,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*.py')},new_models=0,new_integrations=0,new_navigation=0,all_native_tick_receipts_qualified=False,limitations='Synthetic endpoint receipts and saved-array logic; original full-state native audit and actual worker integration remain unexecuted.')
    (out/'QUALIFICATION.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
