"""Restore selected actual V934 stall evidence with exact SHA checks; zero models."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v936_rpccr_corridor_search';GH=R/'tools/phase_storage_20261107/vendor/gh';D=O/'download';D.mkdir(exist_ok=False);S=O/'saved';S.mkdir()
idx=json.loads((R/'records/nav2_v934_20261109/RECORD_INDEX.json').read_text());a=next(x for x in idx['archives']if x['group']=='phase-v934-20261109');subprocess.run([str(GH),'release','download',idx['release_tag'],'--repo','frank8763/phase-','--pattern',a['group']+'*','--dir',str(D)],check=True,timeout=60)
inv=json.loads((D/(a['group']+'.INVENTORY.json')).read_text());catalog={x['path']:x for x in inv['files']};parts=[];h=hashlib.sha256()
for row in a['parts']:
 p=D/row['name'];b=p.read_bytes();assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256'];h.update(b);parts.append(str(p))
assert h.hexdigest()==a['archive_sha256'];cat=subprocess.Popen(['cat',*parts],stdout=subprocess.PIPE);z=subprocess.Popen(['zstd','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();rows=[]
wanted={'COMMAND_TUBES.json.gz','MOTION_ENVELOPE.json.gz','PLANS.json','TASK.json','RESULT.json','SETUP.json','INGRESS.json.gz','ROUTER_REQUESTS.json','ROS_RESULT.json','NATIVE_TRACE.npz','BODY_COMMANDS.json','INITIAL_STATE.npz'}
with tarfile.open(fileobj=z.stdout,mode='r|')as t:
 for m in t:
  if '/v934/main_we/'not in m.name or Path(m.name).name not in wanted:continue
  row=catalog[m.name];data=t.extractfile(m).read();assert m.isfile()and len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];p=S/Path(m.name).name;assert not p.exists();p.write_bytes(data);rows.append(row)
assert z.wait()==0 and cat.wait()==0 and len(rows)==len(wanted)
(O/'RESTORE_VERIFIED.json').write_text(json.dumps(dict(passed=True,models=0,integrations=0,release=idx['release_tag'],files=rows),indent=2)+'\n');print('FIXTURE_READY',len(rows))
