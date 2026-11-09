"""Callback-independent recovery transaction. All effects are explicit caller actions.

No actuator permissions are created here. A production adapter must retain the
existing command/native guards; this module cannot replace them.
"""
import copy
import functools
import hashlib
import json
import math

import numpy as np

from recovery import MIN_PROGRESS_M, certify


def fingerprint(path):
    return hashlib.sha256(json.dumps(path, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def guarded(method):
    @functools.wraps(method)
    def invoke(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as error:
            self.fault(str(error))
            raise
    return invoke


class RecoveryTransaction:
    def __init__(self, original_goal, known):
        self.original_goal = tuple(original_goal)
        self.known = copy.deepcopy(known)
        self.mode = 'NORMAL'
        self.path = None
        self.path_sha256 = None
        self.entry_error = None
        self.used_prior_tick = -1
        self.events = []
        self.started_at = None
        self.installed_at = None

    def _record(self, action, **values):
        event = dict(action=action, mode=self.mode, **values)
        self.events.append(event)
        return event

    @staticmethod
    def fresh(packet, source, now, stopped=False):
        assert np.isfinite([now, *packet['body'], packet['body_measured_at'],
                            source['source_age_s']]).all(), 'NONFINITE_SOURCE'
        assert 0 <= now-packet['body_measured_at'] <= .05, 'STALE_BODY'
        age = source['source_age_s']+max(0., now-source.get('decision_at', now))
        assert 0 <= age <= .2, 'STALE_SCAN'
        assert source['source_native_tick'] <= packet['native_tick'], 'FUTURE_SOURCE'
        prior = source['periodic']
        assert prior['source_tick'] <= source['source_native_tick'], 'FUTURE_PERIODIC_SOURCE'
        assert prior['omega'] == .32 and prior['amplitude'] == .25, 'CHANGED_PRIOR'
        if stopped:
            assert max(abs(packet['body'][3]), abs(packet['body'][4])) <= .03, 'BODY_NOT_STOPPED'

    @guarded
    def request(self, packet, source, now):
        assert self.mode in {'NORMAL', 'WAIT_NEW_CAUSAL_SOURCE'}, 'RECOVERY_ALREADY_ACTIVE'
        self.fresh(packet, source, now)
        assert source['periodic']['source_tick'] > self.used_prior_tick, 'NO_NEW_CAUSAL_INFORMATION'
        self.mode = 'CANCEL_PENDING'
        self.started_at = now
        self.entry_error = float(np.linalg.norm(np.asarray(packet['body'][:2])-self.original_goal))
        return self._record('CANCEL_NORMAL_NAVIGATION')

    @guarded
    def canceled(self, acknowledged):
        assert self.mode == 'CANCEL_PENDING', 'UNEXPECTED_CANCEL_CALLBACK'
        if not acknowledged:
            return self.fault('NORMAL_CANCELLATION_REJECTED')
        self.mode = 'STOPPED_REVALIDATION'
        return self._record('WAIT_FRESH_STOPPED_BODY')

    @guarded
    def install(self, proposal, packet, source, now):
        assert self.mode == 'STOPPED_REVALIDATION', 'CANCEL_OR_STOP_NOT_ACKNOWLEDGED'
        self.fresh(packet, source, now, stopped=True)
        assert proposal['passed'] is True and proposal['status'] == 'RECOVERY_SEGMENT', 'UNQUALIFIED_REFERENCE'
        assert tuple(proposal['original_goal']) == self.original_goal, 'ORIGINAL_GOAL_CHANGED'
        path = proposal['path']
        delta = np.asarray(path[0])-packet['body'][:3]
        delta[2] = math.atan2(math.sin(delta[2]), math.cos(delta[2]))
        assert np.linalg.norm(delta[:2]) <= .01 and abs(delta[2]) <= .01, 'POSE_DRIFT_REQUIRES_REPLAN'
        proof = certify(path, self.known, source['periodic'])
        assert proof['passed'], 'CURRENT_CAUSAL_SET_REJECTS_REFERENCE'
        improvement = self.entry_error-float(np.linalg.norm(np.asarray(path[-1][:2])-self.original_goal))
        assert improvement >= MIN_PROGRESS_M, 'NO_CERTIFIED_PROGRESS'
        self.path = copy.deepcopy(path)
        self.path_sha256 = fingerprint(self.path)
        self.used_prior_tick = source['periodic']['source_tick']
        self.installed_at = now
        self.mode = 'FOLLOW_ACCEPT_PENDING'
        return self._record('SEND_FOLLOW_PATH_ONCE', path=copy.deepcopy(self.path),
                            path_sha256=self.path_sha256, controller_id='FollowPath',
                            original_goal=list(self.original_goal), certificate=proof)

    @guarded
    def accepted(self, accepted):
        assert self.mode == 'FOLLOW_ACCEPT_PENDING', 'UNEXPECTED_FOLLOW_ACCEPT_CALLBACK'
        if not accepted:
            return self.fault('FOLLOW_PATH_REJECTED')
        self.mode = 'FOLLOW_RECOVERY'
        return self._record('KEEP_COMMITTED_REFERENCE')

    def periodic_normal_plan(self):
        if self.mode in {'FOLLOW_ACCEPT_PENDING', 'FOLLOW_RECOVERY', 'STOPPED_REPLAN'}:
            return self._record('IGNORE_PERIODIC_REFERENCE_OVERWRITE', path_sha256=self.path_sha256)
        return self._record('NORMAL_REFERENCE_UPDATE_ALLOWED')

    @guarded
    def follow_completed(self, status):
        assert self.mode == 'FOLLOW_RECOVERY', 'UNEXPECTED_FOLLOW_RESULT'
        if status != 4:
            return self.fault('FOLLOW_PATH_DID_NOT_SUCCEED')
        self.mode = 'STOPPED_REPLAN'
        return self._record('WAIT_FRESH_STOPPED_BODY')

    @guarded
    def finish_segment(self, packet, source, now):
        assert self.mode == 'STOPPED_REPLAN', 'FOLLOW_PATH_NOT_COMPLETE'
        self.fresh(packet, source, now, stopped=True)
        pose = np.asarray(packet['body'][:2])
        assert np.linalg.norm(pose-self.path[-1][:2]) <= .2, 'SEGMENT_ENDPOINT_NOT_REACHED'
        progress = self.entry_error-float(np.linalg.norm(pose-self.original_goal))
        assert progress >= .4, 'NO_ACTUAL_SEGMENT_PROGRESS'
        self.mode = 'WAIT_NEW_CAUSAL_SOURCE'
        return self._record('PLAN_TO_ORIGINAL_GOAL', goal=list(self.original_goal),
                            measured_segment_progress_m=progress,
                            original_goal_success=False)

    @guarded
    def monitor(self, packet, source, now):
        self.fresh(packet, source, now)
        if self.mode in {'CANCEL_PENDING', 'FOLLOW_ACCEPT_PENDING'}:
            anchor = self.started_at if self.mode == 'CANCEL_PENDING' else self.installed_at
            assert now-anchor <= 2., 'ACTION_HANDSHAKE_TIMEOUT'
        if self.mode in {'FOLLOW_RECOVERY', 'STOPPED_REPLAN'}:
            assert now-self.installed_at <= 35., 'RECOVERY_SEGMENT_TIMEOUT'
            assert fingerprint(self.path) == self.path_sha256, 'COMMITTED_REFERENCE_MUTATED'
        return self._record('COMMAND_AND_NATIVE_GUARDS_REMAIN_REQUIRED')

    def fault(self, reason):
        self.mode = 'FAILED'
        return self._record('STOP_AND_CANCEL_ALL_ACTIONS', reason=reason)
