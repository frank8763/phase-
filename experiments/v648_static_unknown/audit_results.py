"""Offline integrity checks; does not execute a policy or simulator."""
import argparse,gzip,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired)
c=json.loads((root/'completion.json').read_text());audits=[]
for r in c.get('results',[]):
 cell=root/r['condition'];rows=json.loads((cell/'trace.json').read_text())
 h=hashlib.sha256()
 with gzip.open(cell/'contacts.jsonl.gz','rb') as stream:
  for b in iter(lambda:stream.read(1048576),b''):h.update(b)
 assert h.hexdigest()==r['contacts']['contact_log_content_sha256']
 execution=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()] if(cell/'v648_execution.jsonl').exists()else[]
 assert len(execution)==len(rows)==r['public_steps']
 assert r['physics_steps']==8*len(rows)==r['contacts']['physics_steps']
 assert r['static_obstacle_pose_unchanged'] and r['root_mutations_outside_mjstep']==0
 expected=r['goal_distance_m']<=.45 and r['contacts']['robot_obstacle_contact_records']==0 and r['contacts']['unknown_contact_records']==0
 assert expected==r['strict_safe_arrival']
 audits.append({'condition':r['condition'],'status':'PASS','public_steps':len(rows),'actual_physics_steps':r['physics_steps'],'contact_digest_verified':True})
hashes={r['initial_state_hash']for r in c.get('results',[])}
assert len(hashes)<=1,'PAIRED_INITIAL_STATE_HASH_MISMATCH'
print(json.dumps({'status':'PASS','same_initial_state_hash':next(iter(hashes),None),'branches':audits},indent=2))
