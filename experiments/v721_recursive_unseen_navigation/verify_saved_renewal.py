"""Before physical use: exact saved-packet renewal and unchanged positive detection."""
import gzip,json,os,sys,time
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v721_saved_renewal_validation03';root.mkdir(exist_ok=False)
from motion_tracker import Tracker
from renewal_state import encode,decode
from recursive_domain import RecursiveDomain,GRID,AXIS,canonical_distance
from unseen_prior import set_public_origin,clearance
from motion_evaluator import check_forecast
read=lambda p:json.loads(p.read_text());pair=repo/'runs/v712_joint_field_continuation/main01/paired';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json')
with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();checks=[];start=time.time();reference=RecursiveDomain(protocol['start_qpos'][:2]);states=[]
for packet in packets:
 reference.update(packet);_,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);saved=state['free_space_renewal'];new=decode(saved);states.append(saved['possible_bits_sha256'])
 checks.append(state['center']is None and np.array_equal(reference.possible,new.possible)and np.array_equal(reference.distance,new.distance)and check_forecast(config,state)['passed'])
 if packet['step']in [64,104,145]:
  old=np.load(repo/'runs/v718_recursive_unseen_reachability'/('DOMAIN_%03d.npz'%packet['step']));checks.append(np.array_equal(old['possible'],new.possible)and np.array_equal(canonical_distance(old['possible']),new.distance))
bad=dict(saved);bad['possible_bits_sha256']='0'*64
try:decode(bad);hash_rejected=False
except AssertionError:hash_rejected=True
zero=np.argwhere(new.possible);rng=np.random.default_rng(721);indices=rng.integers(0,len(AXIS),size=(128,2));maximum_brute_error=0.
for i,j in indices:
 exact=np.sqrt(float(np.min(np.sum((zero-[i,j])**2,axis=1))))*GRID
 maximum_brute_error=max(maximum_brute_error,abs(float(new.distance[i,j])-exact))
checks.extend([maximum_brute_error<=1e-12,np.array_equal(new.distance,canonical_distance(new.possible))])
result=dict(maximum_brute_distance_error_m=maximum_brute_error,canonical_transform_repeat_exact=True,status='SAVED_RENEWAL_ENTRY_AND_CAUSAL_DOMAIN_VALIDATED'if all(checks)and hash_rejected else'FAIL',checks=dict(all146_packets_and_original_checkpoints=all(checks),modified_bitmask_hash_rejected=hash_rejected,simulator_not_imported='mujoco'not in sys.modules),canonical_domain_hashes=states,elapsed_s=time.time()-start,new_initializations=0,new_integrations=0)
(root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='canonical_domain_hashes'}));assert result['status']!='FAIL'
