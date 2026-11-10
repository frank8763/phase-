"""Selected saved evidence restore with exact Release/member SHA; zero models."""
import hashlib,json,subprocess,tarfile,threading
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1016_saved_route_diagnosis';O.mkdir(exist_ok=True)
index=json.loads((R/'records/nav2_v1015_20261110/V1015_RECORD_INDEX.json').read_text());record=index['archives'][0];tag=index['release_tag'];gh=R/'tools/phase_storage_20261107/vendor/gh';back=O/'download';back.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fetch(name):
 p=back/name
 if not p.exists():
  done=subprocess.run([str(gh),'release','download',tag,'--repo','frank8763/phase-','--pattern',name,'--dir',str(back)],capture_output=True,text=True,timeout=30);assert done.returncode==0,(done.stdout+done.stderr)[-1000:]
 return p
inv=json.loads(fetch(record['group']+'.INVENTORY.json').read_text());mapping={x['path']:x for x in inv['files']}
parts=[]
for part in record['parts']:
 p=fetch(part['name']);assert p.stat().st_size==part['bytes']and sha(p)==part['sha256'];parts.append(p)
names={'INDEPENDENT_AUDIT.json','ROS_RESULT.json','RESULT.json','COMPLETION.json','RECOVERY_CORRIDORS.json','RECOVERY_FAULT.json','PROFILE_EXECUTION.json','TASK.json','INGRESS.json.gz','COMMAND_TUBES.json.gz','MOTION_ENVELOPE.json.gz','SETUP.json','NATIVE_TRACE.npz','BODY_COMMANDS.json','BACKEND_ENTRY_BINDING.json'}
prefix='runs/v858_nav2_verified/v1015/main_we/'
selected={x for x in mapping if x.startswith(prefix)and Path(x).name in names or x.startswith(prefix+'COMMITTED_PROFILE_')}
proc=subprocess.Popen(['zstd','-dc'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
def feed():
 for p in parts:
  with p.open('rb')as f:
   while True:
    block=f.read(1024*1024)
    if not block:break
    proc.stdin.write(block)
 proc.stdin.close()
t=threading.Thread(target=feed);t.start();restored=[]
with tarfile.open(fileobj=proc.stdout,mode='r|')as archive:
 for member in archive:
  if member.name not in selected:continue
  row=mapping[member.name];raw=archive.extractfile(member).read();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
  dest=O/'saved'/member.name.removeprefix(prefix);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);restored.append(member.name)
t.join();assert proc.wait()==0 and set(restored)==selected
(O/'RESTORE_RECEIPT.json').write_text(json.dumps(dict(models=0,integrations=0,selected_sha_verified=restored,source_tag=tag),indent=2)+'\n')
for p in parts:p.unlink()
print(json.dumps(dict(models=0,restored_files=len(restored))))
