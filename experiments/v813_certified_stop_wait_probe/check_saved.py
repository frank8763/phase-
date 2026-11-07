"""Fixed saved inputs; model import forbidden. No physical work."""
import argparse, copy, gzip, hashlib, importlib.abc, json, sys
from pathlib import Path
import numpy as np

own=Path(__file__).parent; repo=own.parents[1]
for p in ['runtime/mk-mini/training/phase14_lidar_depth_nav/envs',
          'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',
          'experiments/v733_early_low_translation_scan',
          'experiments/v753_coupled_progress_repaired',
          'experiments/v812_soft_global_reference']:
    sys.path.insert(0,str(repo/p))
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname=='mujoco' or fullname.startswith('mujoco.'):
            raise RuntimeError('SAVED_QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
from dynamic_scene import Motion
from sensor_model import packet
from packet_contract import packet_equal
from motion_tracker import Tracker
from unseen_prior import set_public_origin

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--assert-old-nonretreating',action='store_true');a=ap.parse_args()
    pair=repo/'runs/v812_soft_global_reference/main_slot01/paired';cell=pair/'geometry_memory'
    read=lambda p:json.loads(p.read_text())
    decisions=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()]
    old=next(r for r in decisions if r['step']==586 and r['candidate_role']=='ORDINARY' and r['stage']=='BACKUP_APPEND')
    brake=old['detail']['candidates'][0]
    accepted=[r for r in old['detail']['candidates']if r['reason']is None]
    assert brake['kind']=='BRAKE_ONLY' and brake['reason']=='TIME_CLEARANCE'
    assert accepted and all(r['kind']=='REVERSE_BRAKE'for r in accepted)
    if a.assert_old_nonretreating:
        print('RED: old step586 admits advance only with reverse fallback; brake witness',brake['early_rejection_witness_value_m'],flush=True)
        assert brake['reason']is None,'OLD_ADVANCE_DOES_NOT_PRESERVE_BRAKE_ONLY_RESERVE'
    root=repo/'runs/v813_certified_stop_wait_probe/pre_navigation';root.mkdir(parents=True,exist_ok=False)
    protocol=read(pair/'STATIC_PROTOCOL.json'); motion=Motion(read(pair/'DYNAMIC_PROTOCOL.json'))
    noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
    with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:
        packets=[]
        for line in f:
            p=json.loads(line)
            if p['step']>586:break
            assert packet_equal(p,packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,noise)),'ORIGINAL_NOISY_SENSOR_NOT_EXACT'
            packets.append(p)
    wanted={}
    with(cell/'motion_estimate.jsonl').open()as f:
        for line in f:
            r=json.loads(line)
            if r['step']in[402,586]:wanted[r['step']]={k:v for k,v in r.items()if k!='step'}
            if r['step']>=586:break
    set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();states={}
    for p in packets:
        _,state=tracker.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
        if p['step']in wanted:
            assert state==wanted[p['step']],'ORIGINAL_CAUSAL_STATE_CHANGED'
            states[p['step']]=state
    for step in[402,586]:
        with np.load(cell/'ordinary_certificates'/f'certificate_{step-1:04d}.npz')as z:
            assert z['controls'].shape==(320,4) and np.all(z['target'][2:]==0.)
            prior=next(r for r in decisions if r['step']==step-1 and r['candidate_role']=='ORDINARY' and r['stage']=='BACKUP_APPEND')
            assert prior['detail']['candidates'][0]['reason']is None
    plan=read(cell/'planning_0402.json');assert any(p[3]<0 for p in plan['path'])
    out=dict(status='FIXED_STOP_WAIT_SAVED_INPUTS_EXACT',checkpoints=[402,586],raw_packets=len(packets),causal_states_exact=True,
             original_reverse_admission_reproduced=True,models=0,integrations=0,
             original_brake_early_witness_m=brake['early_rejection_witness_value_m'])
    (root/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))
if __name__=='__main__':main()
