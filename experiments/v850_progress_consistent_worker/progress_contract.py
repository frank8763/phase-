"""Causal task-progress policy for already safety-qualified finite certificates.

Safety is evaluated by the unchanged native pipeline before this policy is used.
This module never constructs a model, advances physics, or accesses actor truth.
"""
import numpy as np

MIN_ADVANCE_M=.02
TOLERANCE=1e-10
VERSION='V850_COMMITTED_CERTIFICATE_PROGRESS'


def context(real,state,reference,cache,cursor,step,role='ORDINARY'):
    active=bool(state['center']is not None and reference is not None)
    result=dict(version=VERSION,active=active,role=role,step=int(step),
                minimum_advance_m=MIN_ADVANCE_M,old_created_step=None,
                old_terminal_goal_m=None,old_cursor=None,old_state_error=None,
                hidden_world_geometry_used=False)
    if not active:return result
    goal=np.asarray(reference['goal_xy'],float);current=np.asarray(real.qpos)[:2]
    assert goal.shape==(2,)and np.all(np.isfinite(goal))and np.all(np.isfinite(current)),'INVALID_PROGRESS_GEOMETRY'
    result.update(goal_xy=goal.tolist(),initial_xy=current.tolist(),current_goal_m=float(np.linalg.norm(current-goal)))
    if cache is not None:
        assert isinstance(cursor,int)and 0<=cursor<320,'INVALID_PROGRESS_OLD_CURSOR'
        q=cache['initial_qpos']if cursor==0 else cache['qpos'][cursor-1]
        v=cache['initial_qvel']if cursor==0 else cache['qvel'][cursor-1]
        error=max(float(np.max(abs(np.asarray(real.qpos)-q))),float(np.max(abs(np.asarray(real.qvel)-v))))
        assert error<=1e-8,'PROGRESS_OLD_CERTIFICATE_STATE_NOT_CURRENT'
        assert abs(float(real.time)-cache['start_time']-cursor*.01)<=1e-8,'PROGRESS_OLD_CERTIFICATE_TIME_NOT_CURRENT'
        terminal=np.asarray(cache['qpos'])[-1,:2]
        result.update(old_created_step=int(cache['created_step']),old_terminal_goal_m=float(np.linalg.norm(terminal-goal)),
                      old_cursor=int(cursor),old_state_error=error)
    return result


def assess(ctx,terminal_xy):
    result=dict(version=VERSION,active=ctx['active'],normal_allowed=True,
                recovery_only=False,reason=None,complete_goal_gain_m=None,
                terminal_goal_m=None,old_terminal_improvement_m=None)
    if not ctx['active']:return result
    goal=np.asarray(ctx['goal_xy']);xy=np.asarray(terminal_xy,float)
    assert xy.shape==(2,)and np.all(np.isfinite(xy)),'INVALID_PROGRESS_TERMINAL'
    terminal=float(np.linalg.norm(xy-goal))
    gain=ctx['current_goal_m']-terminal;previous=ctx['old_terminal_goal_m']
    improvement=None if previous is None else previous-terminal
    reason='PROGRESS_NO_COMPLETE_GAIN'if gain<MIN_ADVANCE_M-TOLERANCE else'PROGRESS_REPLACES_BETTER_RETAINED'if previous is not None and improvement<MIN_ADVANCE_M-TOLERANCE else None
    result.update(normal_allowed=reason is None,recovery_only=reason is not None and previous is None,
                  reason=reason,complete_goal_gain_m=gain,terminal_goal_m=terminal,
                  old_terminal_improvement_m=improvement)
    return result


def summarize(cache,ctx,decision,mode):
    assert mode in ['PROGRESS','RECOVERY_ENTRY','LEGACY_PHASE']
    if mode=='PROGRESS':assert decision['active']and decision['normal_allowed']
    if mode=='RECOVERY_ENTRY':assert decision['recovery_only']and not decision['normal_allowed']
    cache['progress_contract']=dict(context=ctx,assessment=decision,mode=mode)
    return cache
