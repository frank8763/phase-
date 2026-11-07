"""Independent saved-record check; does not import the production progress policy.

The existing physical, coverage, control and replay audits remain separate and
mandatory. This only verifies the new finite-certificate selection relation.
"""
import numpy as np


def check(certificate, real, old=None, cursor=None):
    proof=certificate['progress_contract'];ctx=proof['context'];assessment=proof['assessment'];mode=proof['mode']
    assert ctx['hidden_world_geometry_used']is False
    assert ctx['version']=='V850_COMMITTED_CERTIFICATE_PROGRESS'
    assert ctx['minimum_advance_m']==.02
    assert mode in ['PROGRESS','RECOVERY_ENTRY','LEGACY_PHASE']
    if mode=='LEGACY_PHASE':
        assert not ctx['active']and not assessment['active']
        return dict(mode=mode,checked=True)
    assert ctx['active']and assessment['active']
    goal=np.asarray(ctx['goal_xy']);position=np.asarray(real.qpos)[:2]
    assert np.max(abs(position-np.asarray(ctx['initial_xy'])))<=1e-8
    assert np.max(abs(np.asarray(certificate['prefix_initial_qpos'])-real.qpos))<=1e-8
    current=float(np.linalg.norm(position-goal))
    terminal=float(np.linalg.norm(np.asarray(certificate['qpos'])[-1,:2]-goal))
    gain=current-terminal
    assert abs(current-ctx['current_goal_m'])<=1e-10
    assert abs(terminal-assessment['terminal_goal_m'])<=1e-10
    assert abs(gain-assessment['complete_goal_gain_m'])<=1e-10
    improvement=None
    if old is None:
        assert ctx['old_created_step']is None and ctx['old_terminal_goal_m']is None
        assert assessment['old_terminal_improvement_m']is None
    else:
        assert isinstance(cursor,int)and 0<=cursor<320
        oldq=np.asarray(old['initial_qpos']if cursor==0 else old['qpos'][cursor-1])
        oldv=np.asarray(old['initial_qvel']if cursor==0 else old['qvel'][cursor-1])
        assert np.max(abs(oldq-real.qpos))<=1e-8 and np.max(abs(oldv-real.qvel))<=1e-8
        assert abs(real.time-old['start_time']-.01*cursor)<=1e-8
        previous=float(np.linalg.norm(np.asarray(old['qpos'])[-1,:2]-goal));improvement=previous-terminal
        assert ctx['old_created_step']==old['created_step']and ctx['old_cursor']==cursor
        assert abs(previous-ctx['old_terminal_goal_m'])<=1e-10
        assert abs(improvement-assessment['old_terminal_improvement_m'])<=1e-10
    if mode=='PROGRESS':
        assert gain>=.02-1e-10 and (improvement is None or improvement>=.02-1e-10)
        assert assessment['normal_allowed']and not assessment['recovery_only']and assessment['reason']is None
    else:
        assert old is None and ctx['role']=='ORDINARY'
        assert gain<.02-1e-10 and assessment['recovery_only']and not assessment['normal_allowed']
        assert assessment['reason']=='PROGRESS_NO_COMPLETE_GAIN'
    return dict(mode=mode,checked=True,complete_goal_gain_m=gain,old_terminal_improvement_m=improvement)
