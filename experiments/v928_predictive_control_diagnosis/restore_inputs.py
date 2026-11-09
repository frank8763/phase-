"""Restore only fixed archived inputs; no physical dependency import."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v928_predictive_control_diagnosis';GH=R/'tools/phase_storage_20261107/vendor/gh';proof=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for idxpath,group,label in [('records/nav2_v863_execution_20261107/RECORD_INDEX.json','v862-v863-evidence','navigation'),('records/nav2_v909_20261109/RECORD_INDEX.json','phase-v909-continuation-20261109','response')]:
 idx=json.load(open(R/idxpath));a=next(x for x in idx['archives']if x['group']==group);D=O/(label+'_download');D.mkdir(exist_ok=False)
 subprocess.run([str(GH),'release','download',idx['release_tag'],'--repo','frank8763/phase-','--pattern',group+'*','--dir',str(D)],check=True,timeout=90)
 inventory=json.load(open(D/(group+'.INVENTORY.json')));catalog={r['path']:r for r in inventory['files']};h=hashlib.sha256();parts=[]
 for row in a['parts']:
  p=D/row['name'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];h.update(p.read_bytes());parts.append(str(p))
 assert h.hexdigest()==a['archive_sha256']
 cat=subprocess.Popen(['cat',*parts],stdout=subprocess.PIPE);zstd=subprocess.Popen(['zstd','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();seen=set();S=O/'saved'
 with tarfile.open(fileobj=zstd.stdout,mode='r|')as t:
  for m in t:
   wanted=(label=='navigation'and('/v862/'in m.name or'/v863/'in m.name)and m.name.endswith(('/PLANS.json','/COMMANDS.json','/physics/BODY_COMMANDS.json','/physics/NATIVE_TRACE.npz','/physics/SETUP.json','/TASK.json'))or label=='response'and'/platform_'in m.name and m.name.endswith(('/BODY_SAMPLES.npz','/QUALIFICATION.json')))
   if not wanted:continue
   row=catalog[m.name];assert m.isfile()and m.name not in seen;data=t.extractfile(m).read();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];p=S/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);proof.append(dict(path=m.name,bytes=len(data),sha256=row['sha256'],release=idx['release_tag']));seen.add(m.name)
 assert zstd.wait()==0 and cat.wait()==0
 print(label,'selected',len(seen),flush=True)
(O/'RESTORE_VERIFIED.json').write_text(json.dumps(dict(models=0,integrations=0,members=proof),indent=2)+'\n')
print('Restored',len(proof),'SHA-verified fixed input members',flush=True)
