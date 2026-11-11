"""Stream verified Release evidence for offline actor-domain coverage only.

No simulator/model creation. Full archive SHA and every member SHA checked;
retain only two trace files temporarily, never rehydrate the full raw archive.
"""
import hashlib,json,subprocess,tarfile,tempfile,threading,urllib.request
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1055_atomic_publication_execution';D=R/'records/nav2_v1055_20261111'
def main():
 index=json.loads((D/'RECORD_INDEX.json').read_text());record=index['archives'][0];base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/'
 with urllib.request.urlopen(base+record['group']+'.INVENTORY.json',timeout=20)as response:catalog={x['path']:x for x in json.load(response)['files']}
 proc=subprocess.Popen(['zstd','-q','-dc'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);whole=hashlib.sha256();errors=[]
 def feed():
  try:
   for part in record['parts']:
    h=hashlib.sha256();n=0
    with urllib.request.urlopen(base+part['name'],timeout=60)as source:
     for b in iter(lambda:source.read(1048576),b''):whole.update(b);h.update(b);n+=len(b);proc.stdin.write(b)
    assert n==part['bytes']and h.hexdigest()==part['sha256']
  except BaseException as e:errors.append(repr(e))
  finally:proc.stdin.close()
 thread=threading.Thread(target=feed,daemon=True);thread.start();seen=set();segments={};plans={};normals=np.c_[np.cos(np.arange(8)*np.pi/8),np.sin(np.arange(8)*np.pi/8)]
 with tempfile.TemporaryDirectory(dir=O,prefix='coverage_readback_')as temporary:
  traces={}
  with tarfile.open(fileobj=proc.stdout,mode='r|')as archive:
   for member in archive:
    assert member.isfile()and member.name in catalog and member.name not in seen;row=catalog[member.name];stream=archive.extractfile(member);h=hashlib.sha256();prefix='runs/v858_nav2_verified/v1055/';suffix=member.name[len(prefix):]if member.name.startswith(prefix)else None;task=suffix.split('/')[0]if suffix else None;keep=task in ['full_main','full_repeat']
    if keep and suffix.endswith('/physics/NATIVE_TRACE.npz'):
     path=Path(temporary)/(task+'.npz')
     with path.open('xb')as out:
      for b in iter(lambda:stream.read(1048576),b''):h.update(b);out.write(b)
     traces[task]=path
    elif keep and(suffix.endswith('/EXECUTION_SEGMENTS.json')or suffix.endswith('/ADOPTED_PLAN.json')):
     data=stream.read();h.update(data);obj=json.loads(data)
     if suffix.endswith('/EXECUTION_SEGMENTS.json'):segments[task]=[{k:v for k,v in s.items()if k in ['kind','start_native','executed_native','planning_source','adopted_plan']}for s in obj]
     else:plans[member.name]=obj['planning_source']
    else:
     for b in iter(lambda:stream.read(1048576),b''):h.update(b)
    assert member.size==row['bytes']and h.hexdigest()==row['sha256'];seen.add(member.name)
  while proc.stdout.read(1048576):pass
  thread.join(timeout=65);assert not thread.is_alive()and not errors,errors;assert proc.wait(timeout=5)==0 and seen==set(catalog)and whole.hexdigest()==record['archive_sha256'];results=[]
  for task,path in sorted(traces.items()):
   z=dict(np.load(path));worst=-np.inf;covered=0
   for segment in segments[task]:
    source=segment['planning_source']if segment['kind']=='CERTIFIED_PARKED_HOLD'else plans[segment['adopted_plan']];i=segment['start_native'];n=segment['executed_native'];t=z['time'][i:i+n];actor=z['mocap_pos'][i:i+n,0,:2];features=np.c_[np.ones(len(t)),np.sin(.32*t),np.cos(.32*t)]
    for normal,vertices in zip(normals,source['periodic']['vertices']):
     values=features@np.asarray(vertices).T;projection=actor@normal;worst=max(worst,float((projection-values.max(axis=1)-2e-7).max()),float((values.min(axis=1)-2e-7-projection).max()))
    covered+=n
   assert covered==27088 and worst<=1e-8;results.append(dict(task=task,passed=True,actual_new_native_covered=covered,maximum_true_actor_projection_violation_m=worst))
  assert len(results)==2
 result=dict(passed=True,rows=results,all_archive_members_sha_verified=len(seen),models=0,integrations=0,truth_used_only_in_offline_evaluation=True,online_actor_truth_access=False,temporary_selected_traces_removed=True);(O/'OFFLINE_ACTOR_DOMAIN_COVERAGE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
