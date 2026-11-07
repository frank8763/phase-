"""One causal reference owner and a common forward/reverse certificate merit.

This module never constructs a model or advances physics. A caller must retain
all original native safety, sensing, control, coverage and replay checks.
"""
from dataclasses import dataclass
import hashlib
import json
import numpy as np

ADVANCE=.02
import os
COMMIT_NATIVE=int(os.environ.get('PHASE_MANEUVER_COMMIT_NATIVE','32'));assert COMMIT_NATIVE in [32,64,328]
EPS=1e-10
VERSION='V853_COMMON_SEGMENT_COMMITMENT'
RENEWAL_CAUSES={'CURRENT_GEOMETRY_INVALID','EXECUTION_DIVERGENCE','OBSERVED_NO_PROGRESS'}


def wrap(value):return(value+np.pi)%(2*np.pi)-np.pi


def poses(qpos):
    q=np.asarray(qpos,float)
    assert q.ndim==2 and q.shape[1]>=7 and np.isfinite(q).all()
    return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]


@dataclass(frozen=True)
class Segment:
    reference_id:str
    start:int
    end:int
    gear:int
    points:np.ndarray
    goal:np.ndarray
    is_last:bool

    @property
    def key(self):return f'{self.reference_id}:{self.start}:{self.end}:{self.gear}'

    def project(self,values):
        values=np.asarray(values,float).reshape(-1,3);p=self.points
        assert np.isfinite(values).all()
        delta=np.diff(p[:,:2],axis=0);length=np.linalg.norm(delta,axis=1)
        offset=values[:,None,:2]-p[None,:-1,:2]
        fraction=np.clip(np.sum(offset*delta[None],axis=2)/np.maximum(length**2,1e-12),0.,1.)
        nearest=p[None,:-1,:2]+fraction[:,:,None]*delta[None]
        distances=np.linalg.norm(values[:,None,:2]-nearest,axis=2);which=np.argmin(distances,axis=1);row=np.arange(len(values))
        arc=np.r_[0.,np.cumsum(length)][which]+fraction[row,which]*length[which]
        heading=p[which,2]+fraction[row,which]*wrap(np.diff(p[:,2]))[which]
        contour=distances[row,which];heading_error=np.abs(wrap(values[:,2]-heading))
        # Same arc/contour/heading weights as the original nominal objective,
        # scaled by 1/8. The active gear never shares a projection with a later
        # overlapping segment. Goal distance is deliberately not the merit.
        merit=arc-.625*contour-.625*heading_error
        return dict(arc=arc,contour=contour,heading_error=heading_error,merit=merit)

    def cusp_settled(self,pose,qvel):
        return bool(not self.is_last and np.linalg.norm(np.asarray(pose)[:2]-self.points[-1,:2])<=.16 and abs(wrap(float(pose[2]-self.points[-1,2])))<=.25 and np.linalg.norm(np.asarray(qvel)[:2])<=.05)


class ReferenceOwner:
    """Retain a reference through recovery completion; renew only on evidence."""
    def __init__(self):self.path=None;self.goal=None;self.reference_id=None;self.index=0;self.plan_step=None;self.history=[]

    def install(self,path,goal,step,*,cause='INITIAL',observed_this_frame=False,evidence_id=None):
        path=np.array(path,float,copy=True);goal=np.array(goal,float,copy=True)
        assert path.ndim==2 and path.shape[1]==4 and len(path)>=2 and np.isfinite(path).all()
        assert goal.shape==(2,)and np.isfinite(goal).all()and np.isin(path[:,3],[-1,1]).all()
        assert type(step)is int and step>=0
        if self.path is None:assert cause=='INITIAL'
        else:
            assert cause in RENEWAL_CAUSES,'MODE_COMPLETION_IS_NOT_REPLAN_EVIDENCE'
            assert observed_this_frame and evidence_id and step-self.plan_step>=12,'CAUSAL_REPLAN_EVIDENCE_REQUIRED'
        identity=hashlib.sha256(json.dumps(dict(path=path.tolist(),goal=goal.tolist()),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        path.flags.writeable=False;goal.flags.writeable=False
        self.path,self.goal,self.reference_id,self.index,self.plan_step=path,goal,identity,0,step
        self.history.append(dict(step=step,cause=cause,evidence_id=evidence_id,reference_id=identity))

    def segment(self):
        assert self.path is not None
        i=self.index;gear=int(self.path[min(i+1,len(self.path)-1),3]);start=i;end=i+1
        while start>0 and int(self.path[start,3])==gear:start-=1
        while end<len(self.path)-1 and int(self.path[end+1,3])==gear:end+=1
        return Segment(self.reference_id,start,end,gear,self.path[start:end+1,:3],self.goal,end==len(self.path)-1)

    def update_index(self,index):
        segment=self.segment();assert self.index<=index<=segment.end-1,'CANNOT_SKIP_UNSETTLED_CUSP'
        self.index=int(index)

    def advance_cusp(self,pose,qvel):
        segment=self.segment();assert segment.cusp_settled(pose,qvel),'ACTUAL_STOPPED_CUSP_REQUIRED'
        self.index=segment.end

    def after_backup_finished(self):
        assert self.path is not None
        return dict(reference_id=self.reference_id,index=self.index,reference_retained=True,requires_fresh_validation_before_new_controls=True)


def evaluate(segment,certificate,entry_qpos,entry_qvel,entry_time,*,old=None,old_cursor=None):
    """Choose among independently safety-qualified finite original contracts.

    No safety assertion here constitutes a new safety evaluation. Original
    geometry/self/native/control/coverage auditors remain mandatory.
    """
    q=np.asarray(certificate['qpos']);v=np.asarray(certificate['qvel']);controls=np.asarray(certificate['controls'])
    assert q.ndim==v.ndim==controls.ndim==2 and q.shape[0]==v.shape[0]==320 and q.shape[1]>=7 and v.shape[1]>=2 and controls.shape==(320,4)
    prefix_poses=np.asarray(certificate['prefix_poses']);assert prefix_poses.shape==(8,3)and np.isfinite(prefix_poses).all()
    assert np.array_equal(controls,np.repeat(controls[::8],8,axis=0)),'PUBLIC_CONTROL_MUST_MATCH_ALL_EIGHT_NATIVE_TICKS'
    assert abs(certificate['start_time']-certificate['created_time']-.08)<=1e-8
    assert np.isfinite(q).all()and np.isfinite(v).all()and np.isfinite(controls).all()
    assert certificate['minimum_causal_predicted_clearance_m']>=.155 and certificate['minimum_predicted_self_domain_margin_m']>=.002
    assert np.linalg.norm(v[-1,:2])<=.025 and certificate['terminal_speed_m_s']<=.025
    entry_qpos=np.asarray(entry_qpos);entry_qvel=np.asarray(entry_qvel)
    assert entry_qpos.shape==(q.shape[1],)and entry_qvel.shape==(v.shape[1],)and np.isfinite(entry_qpos).all()and np.isfinite(entry_qvel).all()
    assert np.asarray(certificate['initial_qpos']).shape==entry_qpos.shape and np.asarray(certificate['initial_qvel']).shape==entry_qvel.shape
    assert np.max(abs(entry_qpos-certificate['prefix_initial_qpos']))<=1e-8 and abs(entry_time-certificate['created_time'])<=1e-8
    origin=poses(entry_qpos[None])[0];origin_merit=float(segment.project([origin])['merit'][0])
    future=poses(q[[COMMIT_NATIVE-9,-1]]);projected=segment.project(future);gains=projected['merit']-origin_merit
    # 8 nominal +24 tail =32 actual native ticks (four public actions).
    # This is an execution commitment, not a terminal promise repeatedly reset
    # by a new nominal command after just one public action.
    terminal_ok=bool(projected['contour'][-1]<=.20 and projected['heading_error'][-1]<=.50)
    cusp_at32=segment.cusp_settled(future[0],v[COMMIT_NATIVE-9]);cusp_atend=segment.cusp_settled(future[-1],v[-1])
    goal_at32=bool(segment.is_last and np.linalg.norm(future[0,:2]-segment.goal)<=.45)
    goal_atend=bool(segment.is_last and np.linalg.norm(future[-1,:2]-segment.goal)<=.45)
    short_ok=bool(gains[0]>=ADVANCE-EPS or cusp_at32 or goal_at32)
    full_ok=bool(gains[-1]>=ADVANCE-EPS or cusp_atend or goal_atend)
    old_improvement=None
    if old is not None:
        assert type(old_cursor)is int and 0<=old_cursor<320
        oq=old['initial_qpos']if old_cursor==0 else np.asarray(old['qpos'])[old_cursor-1]
        ov=old['initial_qvel']if old_cursor==0 else np.asarray(old['qvel'])[old_cursor-1]
        assert max(np.max(abs(entry_qpos-oq)),np.max(abs(entry_qvel-ov)))<=1e-8
        assert abs(entry_time-old['start_time']-.01*old_cursor)<=1e-8
        assert old['maneuver_contract']['segment_key']==segment.key,'OLD_CONTRACT_DIFFERENT_REFERENCE_PHASE'
        old_end=float(segment.project(poses(np.asarray(old['qpos'])[-1:]))['merit'][0])
        old_improvement=float(projected['merit'][-1]-old_end)
    dominant=old_improvement is None or old_improvement>=ADVANCE-EPS
    reason='OUTSIDE_ACTIVE_SEGMENT_TUBE'if not terminal_ok else'NO_COMMITTED32_PROGRESS'if not short_ok else'NO_FULL328_PROGRESS'if not full_ok else'NO_IMPROVEMENT_OVER_RETAINED'if not dominant else None
    return dict(version=VERSION,segment_key=segment.key,gear=segment.gear,normal_allowed=reason is None,reason=reason,committed_native_ticks=COMMIT_NATIVE,route_merit_gain_commit_m=float(gains[0]),route_merit_gain328_m=float(gains[-1]),old_terminal_merit_improvement_m=old_improvement,terminal_contour_m=float(projected['contour'][-1]),terminal_heading_error_rad=float(projected['heading_error'][-1]),goal_distance_gain_m=float(np.linalg.norm(origin[:2]-segment.goal)-np.linalg.norm(future[-1,:2]-segment.goal)),cusp_at32=cusp_at32,goal_at32=goal_at32,original_native_safety_still_required=True)


class CommittedPrefix:
    """State-matched execution receipts; never changes physical state or ctrl."""
    def __init__(self,segment,certificate,decision,entry_qpos):
        assert decision['normal_allowed']and decision['segment_key']==segment.key
        self.segment,self.certificate,self.decision=segment,certificate,decision
        self.origin_merit=float(segment.project(poses(np.asarray(entry_qpos)[None]))['merit'][0]);self.native=0

    @property
    def replacement_allowed(self):return self.native>=COMMIT_NATIVE

    def next_command(self):
        assert not self.replacement_allowed,'COMMITTED_PREFIX_ALREADY_COMPLETED'
        if self.native==0:return np.asarray(self.certificate['prefix_command']).copy()
        return np.asarray(self.certificate['controls'])[self.native-8].copy()

    def receipt(self,qpos,qvel,applied_command):
        n=self.native+8;assert n<=COMMIT_NATIVE
        q=np.asarray(self.certificate['initial_qpos']if n==8 else self.certificate['qpos'][n-9]);v=np.asarray(self.certificate['initial_qvel']if n==8 else self.certificate['qvel'][n-9])
        assert max(np.max(abs(np.asarray(qpos)-q)),np.max(abs(np.asarray(qvel)-v)))<=1e-8,'COMMITTED_ACTUAL_STATE_MISMATCH'
        assert np.max(abs(np.asarray(applied_command)-self.next_command()))<=1e-12,'COMMITTED_ACTUAL_CTRL_MISMATCH'
        if n==COMMIT_NATIVE:
            pose=poses(np.asarray(qpos)[None])[0];gain=float(self.segment.project([pose])['merit'][0]-self.origin_merit)
            assert gain>=ADVANCE-EPS or self.segment.cusp_settled(pose,qvel)or(self.segment.is_last and np.linalg.norm(pose[:2]-self.segment.goal)<=.45),'COMMITTED_PROGRESS_NOT_REALIZED'
        # Commit metadata only after every state/control/progress check passes.
        self.native=n
        return dict(actual_native=n,complete=self.replacement_allowed,physical_state_written=False)
