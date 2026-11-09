"""Actual saved-state direction regression; no new physics or navigation."""
import copy
import gzip
import hashlib
import importlib.abc
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
RAW=ROOT/'runs/v858_nav2_verified/v945/main_we'
OUT=ROOT/'runs/v947_rpccr_forward_commitment';REC=ROOT/'records/nav2_v947_20261109'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','physical','vehicle','factory','rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel());sys.path[:0]=[str(CODE),str(ROOT/'experiments/v945_rpccr_observation_liveness')]
from direction_contract import DirectionError,classify,require_forward_path,require_forward_request
from forward_selector import select
from command_tube import admit
from snapshot_geometry import field
from exact_footprint import pose_values


def main():
    rows=json.loads(gzip.decompress((RAW/'COMMAND_TUBES.json.gz').read_bytes()))
    cases=[r for r in rows if r['packet']['native_tick']>=11286]
    known=json.loads((RAW/'physics/SETUP.json').read_text())['known']
    static=lambda known,poses:pose_values(field(known),poses)
    plans=json.loads((RAW/'PLANS.json').read_text())
    original=classify(plans[-1]['path']);original_red=False
    try:require_forward_path(plans[-1]['path'])
    except DirectionError:original_red=True
    counts=Counter();accepted_forward_unchanged=0;safe_outputs=0;records=[]
    for row in cases:
        wanted=row['wanted'];now=row['proof']['issued_at']
        result=select(row['packet'],row['source'],wanted,known,now,[4.,-2.],admit,static)
        counts[result.mode]+=1
        assert result.selected is None or result.selected[0]>=0
        if result.proof is not None:
            assert result.proof['passed'];safe_outputs+=1
        if wanted[0]>0:
            nominal=admit(row['packet'],row['source'],*wanted,known,now)
            if nominal['passed']:
                assert result.selected==tuple(wanted)and result.proof==nominal
                accepted_forward_unchanged+=1
        if wanted==[0.,0.]:assert result.selected in [None,(0.,0.)]
        if wanted[0]<0:assert result.mode=='FORWARD_REFERENCE_REPLAN_REQUIRED'and result.selected is None
        records.append(dict(tick=row['packet']['native_tick'],wanted=wanted,mode=result.mode,
                            selected=result.selected,proof=result.proof))
    checks=dict(actual_original_reversing_reference_rejected=original_red,
                synthetic_forward_path_accepted=require_forward_path([[0.,0.,0.],[1.,0.,0.]])['forward_only'],
                no_reverse_normal_output=all(r['selected']is None or r['selected'][0]>=0 for r in records),
                original_admissible_forward_exact=accepted_forward_unchanged>0,
                no_silent_zero_clamp=all(r['selected']is None for r in records if r['wanted'][0]<0))
    for label,call in [('negative_twist',lambda:require_forward_request(-.1,0.)),
                       ('reverse_path',lambda:require_forward_path([[0.,0.,0.],[-1.,0.,0.]])),
                       ('malformed_path',lambda:require_forward_path([[0.,0.]]))]:
        try:call()
        except DirectionError:checks[label+'_rejected']=True
        else:checks[label+'_rejected']=False
    cfg=json.loads((CODE/'A_forward.yaml').read_text())
    base=json.loads((ROOT/'experiments/v945_rpccr_observation_liveness/A_motion.yaml').read_text())
    cfg['planner_server']['ros__parameters']['GridBased']['motion_model_for_search']='REEDS_SHEPP'
    cfg['controller_server']['ros__parameters']['FollowPath']['allow_reversing']=True
    checks['only_two_declared_config_changes']=cfg==base
    result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,navigation=0,
                original_last_reference=original,saved_decisions=len(cases),new_mode_counts=dict(counts),
                original_admissible_forward_preserved=accepted_forward_unchanged,
                unchanged_gate_qualified_outputs=safe_outputs,production_integrated=False,
                physical_ready=False,new_forward_plan_qualified=False,
                user_direction_contract='Normal forward route/controller/recovery; reversing reserved for separately qualified trapped escape.',
                next_required=['Actual same-input forward-only Smac/RPP qualification.',
                               'Steering-state handoff and persistent feedback stability.',
                               'Production observation liveness and exact failure timing.',
                               'Full pipeline and independent gates before a new physical window.'])
    (OUT/'SELECTIONS.json').write_text(json.dumps(records,indent=2)+'\n')
    for folder in [OUT,REC]:(folder/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    (REC/'PREPARATION_SOURCE_SHA.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in CODE.iterdir()if p.is_file()},physical_authorized=False),indent=2)+'\n')
    print(json.dumps(result,indent=2));assert result['passed']


if __name__=='__main__':main()
