"""One immutable recovery action after acknowledged normal-action quiescence."""
import copy
import hashlib
import json
import math
import numpy as np
from state_reference import (ACTUAL_PROGRESS_REQUIRED, POSITION_ENVELOPE, REQUIRED,
                             _old, snapshot_state)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


class TrackingGuard:
    def __init__(self, plan):
        self.path=copy.deepcopy(plan['path'])
        self.path_sha256=fingerprint(self.path)
        self.mode='FOLLOW_ACCEPT_PENDING'

    def monitor_body(self, packet):
        assert fingerprint(self.path)==self.path_sha256,'COMMITTED_REFERENCE_MUTATED'
        if self.mode not in {'FOLLOW_RECOVERY','STOPPED_REPLAN'}:
            return
        pose=np.asarray(packet['body'][:3]);path=np.asarray(self.path)
        assert pose.shape==(3,) and np.isfinite(pose).all(),'NONFINITE_RECOVERY_OBSERVATION'
        index=int(np.argmin(np.linalg.norm(path[:,:2]-pose[:2],axis=1)))
        position=float(np.linalg.norm(path[index,:2]-pose[:2]))
        heading=abs(math.atan2(math.sin(pose[2]-path[index,2]),math.cos(pose[2]-path[index,2])))
        # Original limits, with a conservative bound for reference sampling.
        assert position+.00625<=.04,'ONLINE_RECOVERY_POSITION_ENVELOPE_FAILED'
        assert heading+.758770385*.00625<=.035,'ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED'


class RecoveryTransaction:
    def __init__(self, original_goal, known):
        self.original_goal=tuple(original_goal);self.known=copy.deepcopy(known)
        self.mode='NORMAL';self.events=[];self.path=None;self.path_sha256=None
        self.used_prior_tick=-1;self.started_at=None;self.installed_at=None
        self.guard=None

    def _record(self, action, **values):
        event=dict(action=action,mode=self.mode,**values);self.events.append(event);return event

    @staticmethod
    def fresh(packet, source, now, stopped=False, liveness=False):
        assert 0<=now-packet['body_measured_at']<=(.2 if liveness else .05),'STALE_BODY'
        age=source['source_age_s']+max(0.,now-source.get('decision_at',now))
        assert 0<=age<=.2,'STALE_SCAN'
        assert source['source_native_tick']<=packet['native_tick'],'FUTURE_SOURCE'
        prior=source['periodic'];assert prior['source_tick']<=source['source_native_tick'],'FUTURE_PERIODIC_SOURCE'
        assert prior['omega']==.32 and prior['amplitude']==.25,'CHANGED_PRIOR'
        if stopped:
            snapshot_state(packet,source,now)

    def request(self, packet, source, now):
        assert self.mode in {'NORMAL','WAIT_NEW_CAUSAL_SOURCE'},'RECOVERY_ALREADY_ACTIVE'
        self.fresh(packet,source,now)
        assert source['periodic']['source_tick']>self.used_prior_tick,'NO_NEW_CAUSAL_INFORMATION'
        self.started_at=now;self.mode='CANCEL_PENDING'
        self.entry_error=float(np.linalg.norm(np.asarray(packet['body'][:2])-self.original_goal))
        return self._record('CANCEL_NORMAL_NAVIGATION')

    def canceled(self, acknowledged, terminal_status):
        assert self.mode=='CANCEL_PENDING','UNEXPECTED_CANCEL_CALLBACK'
        assert acknowledged is True and terminal_status in [5,6],'NORMAL_ACTION_NOT_QUIESCENT'
        self.mode='STOPPED_REVALIDATION'
        return self._record('WAIT_FRESH_STOPPED_BODY',normal_terminal_status=terminal_status)

    def install(self, proposal, packet, source, now):
        assert self.mode=='STOPPED_REVALIDATION','CANCEL_OR_STOP_NOT_ACKNOWLEDGED'
        self.fresh(packet,source,now,stopped=True)
        assert proposal['passed'] is True and proposal['status']=='STATE_CONTINUOUS_RECOVERY_REFERENCE','UNQUALIFIED_REFERENCE'
        assert tuple(proposal['original_goal'])==self.original_goal,'ORIGINAL_GOAL_CHANGED'
        current=snapshot_state(packet,source,now);initial=np.asarray(proposal['initial_state'])
        assert np.linalg.norm(current[:2]-initial[:2])<=.01 and abs(current[2]-initial[2])<=.01,'POSE_DRIFT_REQUIRES_REPLAN'
        assert abs(current[3]-initial[3])<=.01,'STEERING_DRIFT_REQUIRES_REPLAN'
        states=np.asarray(proposal['state_path']);assert np.max(abs(states[0]-initial))<=1e-12
        assert proposal['path']==states[:,:3].tolist(),'STATE_REFERENCE_PATH_MISMATCH'
        static,dynamic=_old.Geometry(self.known,source['periodic']).clearances(states[:,:3])
        assert float(np.minimum(static,dynamic).min())>=REQUIRED,'CURRENT_CAUSAL_SET_REJECTS_REFERENCE'
        lower=self.entry_error-float(np.linalg.norm(states[-1,:2]-self.original_goal))-2*POSITION_ENVELOPE
        assert lower>=ACTUAL_PROGRESS_REQUIRED,'NO_CERTIFIED_ACTUAL_PROGRESS_LOWER_BOUND'
        self.guard=TrackingGuard(proposal);self.path=self.guard.path;self.path_sha256=self.guard.path_sha256
        self.used_prior_tick=source['periodic']['source_tick'];self.installed_at=now;self.mode='FOLLOW_ACCEPT_PENDING'
        return self._record('SEND_FOLLOW_PATH_ONCE',path=copy.deepcopy(self.path),path_sha256=self.path_sha256,
                            controller_id='RecoveryFollowPath',goal_checker_id='recovery_goal_checker',
                            original_goal=list(self.original_goal),actual_goal_progress_lower_m=lower)

    def accepted(self, accepted):
        assert self.mode=='FOLLOW_ACCEPT_PENDING','UNEXPECTED_FOLLOW_ACCEPT_CALLBACK'
        assert accepted is True,'FOLLOW_PATH_REJECTED'
        self.mode='FOLLOW_RECOVERY';self.guard.mode=self.mode
        return self._record('KEEP_COMMITTED_REFERENCE')

    def periodic_normal_plan(self):
        return self._record('IGNORE_PERIODIC_REFERENCE_OVERWRITE' if self.mode in {'FOLLOW_ACCEPT_PENDING','FOLLOW_RECOVERY','STOPPED_REPLAN'} else 'NORMAL_REFERENCE_UPDATE_ALLOWED')

    def monitor_body(self, packet):
        if self.guard is not None:
            self.guard.mode=self.mode;self.guard.monitor_body(packet)

    def monitor(self, packet, source, now):
        self.fresh(packet,source,now,liveness=True)
        if self.mode in {'CANCEL_PENDING','FOLLOW_ACCEPT_PENDING'}:
            assert now-(self.started_at if self.mode=='CANCEL_PENDING' else self.installed_at)<=2.,'ACTION_HANDSHAKE_TIMEOUT'
        if self.mode in {'FOLLOW_RECOVERY','STOPPED_REPLAN'}:
            assert now-self.installed_at<=35.,'RECOVERY_SEGMENT_TIMEOUT'
            self.monitor_body(packet)
        return self._record('COMMAND_AND_NATIVE_GUARDS_REMAIN_REQUIRED')

    def follow_completed(self, status):
        assert self.mode=='FOLLOW_RECOVERY','UNEXPECTED_FOLLOW_RESULT'
        assert status==4,'FOLLOW_PATH_DID_NOT_SUCCEED'
        self.mode='STOPPED_REPLAN';self.guard.mode=self.mode
        return self._record('WAIT_FRESH_STOPPED_BODY')

    def finish_segment(self, packet, source, now):
        assert self.mode=='STOPPED_REPLAN','FOLLOW_PATH_NOT_COMPLETE'
        self.fresh(packet,source,now,stopped=True)
        assert np.linalg.norm(np.asarray(packet['body'][:2])-self.path[-1][:2])<=.04,'SEGMENT_ENDPOINT_NOT_REACHED'
        progress=self.entry_error-float(np.linalg.norm(np.asarray(packet['body'][:2])-self.original_goal))
        assert progress>=.4,'NO_ACTUAL_SEGMENT_PROGRESS'
        self.mode='WAIT_NEW_CAUSAL_SOURCE';self.guard.mode=self.mode
        return self._record('PLAN_TO_ORIGINAL_GOAL',goal=list(self.original_goal),measured_segment_progress_m=progress,original_goal_success=False)

    def fault(self, reason):
        self.mode='FAILED'
        if self.guard:self.guard.mode=self.mode
        return self._record('STOP_AND_CANCEL_ALL_ACTIONS',reason=reason)
