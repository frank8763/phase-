"""Preserve upstream redistribution notices without duplicate Boost copyright copies."""
import hashlib,json,shutil
from pathlib import Path
from package_records import R,ROOT,OUT,REC,archive

def main():
 base=ROOT/'runtime_licenses';base.mkdir(exist_ok=False);mapping=[];seen={}
 inputs=[]
 for root in [ROOT/'rootfs/usr/share/doc',ROOT/'rootfs/opt/ros/jazzy/share']:
  inputs.extend(p for p in root.rglob('*')if p.is_file()and p.name.lower().startswith(('copyright','license','copying','notice')))
 # Debian copyright records may refer to common license texts by path.
 inputs.extend(p for p in Path('/usr/share/common-licenses').iterdir()if p.is_file())
 for p in sorted(inputs):
  data=p.read_bytes();digest=hashlib.sha256(data).hexdigest();target=base/(digest+'.txt')
  if digest not in seen:target.write_bytes(data);seen[digest]=target
  mapping.append(dict(original_path=str(p),stored_path=str(target.relative_to(R)),sha256=digest,bytes=len(data)))
 (base/'LICENSE_MAP.json').write_text(json.dumps(dict(scope='All copyright/license/copying/notice files from verified extracted packages and referenced system common license texts; deduplicated by SHA256',entries=mapping),indent=2)+'\n')
 group=archive('v856-third-party-licenses',base.iterdir());index=json.loads((REC/'RECORD_INDEX.json').read_text());index['archives'].append({k:v for k,v in group.items()if k!='files'});index['runtime_requires']+='; restore v856-third-party-licenses for redistribution notices';index['final_remote_index_asset']='FINAL_RECORD_INDEX.json';index['status']='LOCAL_ALL_GROUPS_SHA_VERIFIED_AWAITING_LICENSE_SUPPLEMENT_UPLOAD';(REC/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n');(OUT/'FINAL_RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n');print('LICENSE_GROUP_PACKAGED',len(mapping),len(seen),flush=True)
if __name__=='__main__':main()
