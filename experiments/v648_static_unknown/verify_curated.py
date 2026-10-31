"""Verify a curated evidence package without loading a controller or simulator."""
import argparse,gzip,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('package');a=p.parse_args();root=Path(a.package)
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'MANIFEST.json').read_text())
for row in manifest:
 f=root/row['path'];assert f.is_file()and f.stat().st_size==row['bytes']and sha(f.read_bytes())==row['sha256'],row['path']
ledger=json.loads((root/'trial_ledger.json').read_text());source_refs=0
for row in ledger:
 for name,h in row['source_hashes'].items():assert sha((root/'source_blobs'/(h+'.py')).read_bytes())==h;source_refs+=1
branches=0;success=0
for f in sorted((root/'selected').glob('*/*/result.json.gz')):
 with gzip.open(f,'rt')as stream:r=json.load(stream)
 branch=f.parent
 with gzip.open(branch/'trace.json.gz','rt')as stream:t=json.load(stream)
 assert len(t)==r['public_steps']and r['physics_steps']==8*len(t)
 digest=hashlib.sha256()
 with gzip.open(branch/'contacts.jsonl.gz','rb')as stream:
  for b in iter(lambda:stream.read(1048576),b''):digest.update(b)
 assert digest.hexdigest()==r['contacts']['contact_log_content_sha256']
 strict=r['goal_distance_m']<=.45 and r['contacts']['robot_obstacle_contact_records']==0 and r['contacts']['unknown_contact_records']==0
 assert strict==r['strict_safe_arrival'];branches+=1;success+=int(strict)
print(json.dumps({'status':'PASS','manifest_files':len(manifest),'source_references_verified':source_refs,'trial_directories_accounted':len(ledger),'selected_branch_contact_digests_verified':branches,'selected_strict_arrivals_including_repeats':success,'success_count_scope':'not an independent success rate','simulation_steps':0},indent=2))
