"""Recheck saved horizon decomposition and add actual tracking metrics; no MJ."""
import ast,gzip,hashlib,json
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v798_legacy_tracking_transplant'
out=repo/'runs/v798_saved_causal_diagnosis';read=lambda p:json.loads(p.read_text())
assert(repo/'REVIEW_PENDING').exists()
assert read(repo/'runs/v798_supplemental_saved_audit/RESULT.json')['maximum_saved_error']==0
assert not(out/'INDEPENDENT_RECHECK.json').exists()
result=read(root/'RESULT.json');proof=read(out/'RESULT.json')
entries=read(root/('S200_R%02d_CANDIDATES.json'%(result['attempted_replans']-1)))
for x,row in zip(entries,proof['final_candidate_rows']):
    z=np.load(root/(x['label']+'.npz'));bad=np.flatnonzero(z['causal_values']<.155)
    assert row['first_causal_rejection_tick']==int(bad[0]+1)>240
    assert row['minimum_tick']==int(np.argmin(z['causal_values'])+1)==328
    assert x['legacy_diagnostic']['reason']is None
    assert x['static_minimum_m']>=.155 and x['clearance_m']<.155
source=repo/'experiments/v793_complete_joint_navigation/serial_predictor.py'
tree=ast.parse(source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='project_to_segment_path')
scope={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
path=np.asarray(read(repo/'experiments/v798_legacy_tracking_transplant/REFERENCE_PATH.json')['path'])
actual=[]
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
    for l in f:
        r=json.loads(l)
        if r['context']!='ORIGINAL_REPLAY'and not r['context'].endswith('_REPEAT'):actual.append(r)
q=np.asarray([r['qpos']for r in actual]);v=np.asarray([r['qvel']for r in actual])
yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
arc,contour,heading=scope[node.name](np.c_[q[:,:2],yaw],path)
low=(np.linalg.norm(v[:,:2],axis=1)<=.025)&(np.linalg.norm(v[:,3:6],axis=1)<=.025)
summary=dict(status='SAVED_CAUSAL_DECOMPOSITION_RECHECKED',all_final_first_rejection_after_240=True,
    final_candidates=len(entries),actual_native=len(actual),
    maximum_contour_error_m=float(contour.max()),final_contour_error_m=float(contour[-1]),
    final_heading_error_rad=float(abs((yaw[-1]-heading[-1]+np.pi)%(2*np.pi)-np.pi)),
    active_prefix_simulation_s=result['committed_replans']*.32,
    low_speed_active_prefix_s=float(low[:result['committed_replans']*32].sum()*.01),
    low_speed_whole_branch_s=float(low.sum()*.01),
    no_model_initializations=0,no_integrations=0,
    original_audit_error_not_rewritten=True,original_complete_pipeline_not_claimed=True,
    interpretation='All 13 original nominal 240-native proposals pass, their current extended 328-native schedules fail only after 240. This is not a claim that the original complete RP-CCR lacked 328-native backups, nor a proof all physical controls are impossible.')
(out/'INDEPENDENT_RECHECK.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
