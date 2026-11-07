"""Immutable full-safe compound certificate; cursor is controller metadata only."""
import hashlib
import numpy as np
from legacy_method import schedule


def prepare(real, prediction, parameters, detail, state, command_map, step):
    assert state['hidden_world_geometry_used'] is False
    assert abs(float(state['time'])-float(real.time))<=1e-10
    q=np.asarray(prediction['qpos']);v=np.asarray(prediction['qvel'])
    p=np.asarray(prediction['poses']);c=np.asarray(prediction['controls'])
    assert q.shape==(328,len(real.qpos))and v.shape==(328,len(real.qvel))
    assert p.shape==(328,3)and c.shape==(328,4)
    assert all(np.isfinite(x).all()for x in [q,v,p,c])
    expected=schedule(parameters,real.ctrl[command_map.ids],command_map)
    assert np.array_equal(c,expected),'COMPOUND_SCHEDULE_CHANGED'
    assert detail['admissible']and detail['clearance_m']>=.155 and detail['self_margin_m']>=.002
    assert detail['arc_progress_m']>=-.01
    assert np.linalg.norm(v[-1,:2])<=.025 and np.linalg.norm(v[-1,3:6])<=.025
    certificate=dict(label=detail['label'],created_step=int(step),start_time=float(real.time),
        initial_qpos=real.qpos.copy(),initial_qvel=real.qvel.copy(),
        initial_ctrl=real.ctrl[command_map.ids].copy(),parameters=np.asarray(parameters).copy(),
        minimum_causal_clearance_m=float(detail['clearance_m']),
        minimum_self_margin_m=float(detail['self_margin_m']))
    for name,value in [('qpos',q),('qvel',v),('poses',p),('controls',c)]:
        certificate[name]=value.copy();certificate[name].setflags(write=False)
    return certificate


def current(certificate,cursor,real,command_map):
    assert certificate is not None and type(cursor)is int and 0<=cursor<=328 and cursor%8==0
    q=certificate['initial_qpos']if cursor==0 else certificate['qpos'][cursor-1]
    v=certificate['initial_qvel']if cursor==0 else certificate['qvel'][cursor-1]
    ctrl=certificate['initial_ctrl']if cursor==0 else certificate['controls'][cursor-1]
    qe=float(np.max(abs(real.qpos-q)));ve=float(np.max(abs(real.qvel-v)))
    ce=float(np.max(abs(real.ctrl[command_map.ids]-ctrl)))
    te=abs(float(real.time)-certificate['start_time']-cursor*.01)
    assert max(qe,ve)<=1e-8,'RETAINED_CURRENT_FULL_STATE_MISMATCH'
    assert ce<=1e-12,'RETAINED_CURRENT_APPLIED_CTRL_MISMATCH'
    assert te<=1e-8,'RETAINED_CURRENT_TIME_MISMATCH'
    return dict(qpos_error=qe,qvel_error=ve,ctrl_error=ce,time_error=te)


def fingerprint(certificate):
    if certificate is None:return None
    h=hashlib.sha256()
    for name in ['initial_qpos','initial_qvel','initial_ctrl','parameters','qpos','qvel','poses','controls']:
        h.update(np.asarray(certificate[name]).tobytes())
    h.update(repr((certificate['label'],certificate['created_step'],certificate['start_time'],
                   certificate['minimum_causal_clearance_m'],certificate['minimum_self_margin_m'])).encode())
    return h.hexdigest()


def portion(certificate,start,end):
    assert 0<=start<end<=328 and start%8==end%8==0
    return {name:certificate[name][start:end]for name in ['qpos','qvel','poses','controls']}
