"""Rebuild the original raw observation history before a new physical batch."""
import ast,gzip,hashlib,json,sys
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v793_complete_joint_navigation'))
sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'))
sys.path.insert(1,str(repo/'experiments/v753_coupled_progress_repaired'))
from motion_tracker import Tracker
from dynamic_scene import Motion
from unseen_prior import set_public_origin
from packet_contract import packet_equal
from sensor_model import packet
read=lambda p:json.loads(p.read_text())
pair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired';cell=pair/'geometry_memory'
out=repo/'runs/v799_preparation';assert not out.exists();out.mkdir()
protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json')
motion=Motion(config);noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
beliefs={r['step']:{k:v for k,v in r.items()if k!='step'}for r in map(json.loads,(cell/'motion_estimate.jsonl').open())}
set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();matched=[];count=0
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:
    for line in f:
        p=json.loads(line);assert packet_equal(p,packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,noise))
        _,state=tracker.update_packet(p,protocol['known_rectangles'],protocol['known_circles']);count+=1
        if p['step']in[404,541,617]:
            assert state==beliefs[p['step']]and state['center']is None
            matched.append(p['step'])
assert matched==[404,541,617]
for f in own.glob('*.py'):ast.parse(f.read_text())
entries=read(own/'FIXED_COMMANDS.json')['checkpoints']
assert [x['step']for x in entries]==matched and all(len(x['candidates'])==25 for x in entries)
r=dict(status='FIXED_SPATIAL_NOMINAL_FIXTURE_QUALIFIED',raw_packets_exact=count,causal_states_exact=matched,
    model_initializations=0,integrations=0,original_nominal_future_rejections=75,
    proves_joint_qualification=False,full_global_navigation_started=False)
(out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
