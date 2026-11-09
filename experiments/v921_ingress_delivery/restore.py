"""Verify downloaded Release parts and restore to a separate empty destination.
Usage: python restore.py DOWNLOAD_DIRECTORY EMPTY_DESTINATION
Download matching .part files and INVENTORY.json assets from RECORD_INDEX release.
Does not import a simulator or launch an experiment.
"""
import hashlib,json,subprocess,sys,tarfile
from pathlib import Path
src=Path(sys.argv[1]).resolve();dst=Path(sys.argv[2]).resolve();assert not dst.exists();dst.mkdir(parents=True)
for ip in sorted(src.glob('*.INVENTORY.json')):
 d=json.loads(ip.read_text());parts=[src/p['name']for p in d['parts']];assert len(parts)==1
 assert hashlib.sha256(parts[0].read_bytes()).hexdigest()==d['archive_sha256'];catalog={r['path']:r for r in d['files']};seen=set()
 proc=subprocess.Popen(['zstd','-dc',str(parts[0])],stdout=subprocess.PIPE)
 with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
  for member in tf:
   row=catalog[member.name];target=dst/member.name;assert member.isfile()and target.resolve().is_relative_to(dst)and member.name not in seen
   data=tf.extractfile(member).read();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():assert target.read_bytes()==data
   else:target.write_bytes(data)
   seen.add(member.name)
 assert proc.wait()==0 and seen==set(catalog)
print('All downloaded members verified; no model execution.')
