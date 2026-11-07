"""Bridge full native-safe original offers to the common single-gear merit."""
import copy
import numpy as np
from maneuver_core import ReferenceOwner,evaluate,COMMIT_NATIVE


def commit_ticks(c):return COMMIT_NATIVE if c.get('maneuver_contract',{}).get('normal_allowed')else 328 if c.get('maneuver_contract')else 8


def segment(reference):
    owner=ReferenceOwner();owner.install(reference['path'],reference['goal_xy'],0);owner.index=int(reference['index']);return owner.segment()


def assess_offer(reserved,reference,real,offer,state,step):
    if state['center']is None:return None
    assert reference is not None,'TRACKED_MANEUVER_REQUIRES_CAUSAL_REFERENCE'
    seg=segment(reference);old,cursor=getattr(reserved,'maneuver_old',(reserved.cache,reserved.cursor))
    original_old_key=None
    if old is not None:
        original_old_key=old.get('maneuver_contract',{}).get('segment_key')
        # Reproject the still state-matched old physical endpoint in the same
        # current segment coordinate system, retaining the original provenance.
        old=dict(old,maneuver_contract=dict(segment_key=seg.key))
    decision=evaluate(seg,offer,real.qpos,real.qvel,float(real.time),old=old,old_cursor=cursor if old is not None else None)
    decision.update(reference_path=reference['path'],reference_index=reference['index'],goal_xy=reference['goal_xy'],old_created_step=None if old is None else old['created_step'],old_cursor=None if old is None else cursor,old_original_segment_key=original_old_key,role='BACKUP_RETURN'if getattr(reserved,'maneuver_return',False)else'ORDINARY',created_step=step,real_entry_qpos=real.qpos.tolist(),real_entry_qvel=real.qvel.tolist(),real_entry_time=float(real.time),hidden_world_geometry_used=False)
    return decision


def decorate(offer,reference,state,step):
    if state['center']is None:return
    assert 'maneuver_contract'in offer
    offer['maneuver_contract']['mode']='PROGRESS'if offer['maneuver_contract']['normal_allowed']else'EXPLICIT_FINITE_RECOVERY'
    offer['maneuver_contract']['execution_commit_native']=commit_ticks(offer)


def verify_native(reserved,real,public_step,native_offset):
    c=reserved.cache
    if c is None:return
    if c['created_step']==public_step:
        q=c['prefix_native_qpos'][native_offset];v=c['prefix_native_qvel'][native_offset];ctrl=c['prefix_command']
    elif reserved.executing:
        i=reserved.cursor-8+native_offset;assert 0<=i<320;q=c['qpos'][i];v=c['qvel'][i];ctrl=c['controls'][i]
    else:return
    error=max(float(np.max(abs(real.qpos-q))),float(np.max(abs(real.qvel-v))),float(np.max(abs(real.ctrl[reserved.ids]-ctrl))))
    assert error<=1e-8,'EVERY_NATIVE_PREFIX_OR_RETAINED_CONTRACT_MISMATCH'
