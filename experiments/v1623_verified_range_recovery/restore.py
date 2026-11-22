"""Bounded positive-progress Range continuation, original part SHA before use."""
import hashlib,io,json,os,fcntl,shutil,signal,tarfile,time,traceback,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs'/Path(__file__).resolve().parent.name
INDEX=R/'runs/v1382_weekend_campaign/storage/v1237/v1237.INDEX.json'
WANTED={f'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/{n}'for n in ['ROUTE_ROWS.json','ROUTE_RECOVERY_INPUT.json']}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 p=O/n;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,sort_keys=True,allow_nan=False)+'\n');t.replace(p)

class Reader(io.RawIOBase):
 def __init__(self,index):self.index=index;self.rows=iter(index['parts']);self.file=None;self.path=None;self.parts=[]
 def readable(self):return True
 def nextpart(self):
  if self.file:self.file.close();self.path.unlink();self.file=None
  row=next(self.rows,None)
  if row is None:return False
  assert row['bytes']<=32*1024**2 and Path(row['name']).name==row['name']
  path=O/'download'/row['name']
  prior=R/('runs/v1621_mechanism_input_recovery/download/'+row['name']if row['name'].endswith('000')else'runs/v1622_bounded_proposal_restore/download/'+row['name'])
  initial=0
  if prior.is_file():
   initial=prior.stat().st_size;assert 0<initial<=row['bytes'];shutil.copyfile(prior,path)
   save('PARTIAL_'+row['name']+'.json',dict(path=str(prior.relative_to(R)),bytes=initial,sha256=sha(prior)))
  requests=[]
  for attempt in range(4):
   offset=path.stat().st_size if path.exists()else 0
   if offset==row['bytes']:break
   url=self.index['release_url'].replace('/tag/','/download/')+'/'+row['name']
   headers={'Range':f'bytes={offset}-{row["bytes"]-1}'}if offset else{}
   started=time.monotonic()
   with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=120)as response:
    if offset:assert response.status==206 and response.headers['Content-Range'].startswith(f'bytes {offset}-')
    else:assert response.status==200
    count=offset
    with path.open('ab'if offset else'xb')as target:
     while True:
      block=response.read(1024**2)
      if not block:break
      count+=len(block);assert count<=row['bytes'];target.write(block)
   assert count>offset,'RANGE_NO_PROGRESS'
   requests.append(dict(offset=offset,received=count-offset,complete=count==row['bytes'],wall_s=time.monotonic()-started))
   save('TRANSFER_'+row['name']+'.json',dict(requests=requests,expected_bytes=row['bytes']))
  assert path.stat().st_size==row['bytes']and sha(path)==row['sha256'],'COMPLETE_PART_SHA_OR_LENGTH'
  self.parts.append(row);save('PART_PROGRESS.json',dict(verified=self.parts));self.path=path;self.file=path.open('rb');return True
 def readinto(self,b):
  while True:
   if self.file is None and not self.nextpart():return 0
   block=self.file.read(len(b))
   if block:b[:len(block)]=block;return len(block)
   if not self.nextpart():return 0
 def close(self):
  if self.file:self.file.close()
  super().close()

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));started=time.monotonic()
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RANGE_RECOVERY1200S')));signal.alarm(1200)
 assert all(json.loads((R/f'runs/{n}/RESULT.json').read_text())['passed']is False for n in ['v1621_mechanism_input_recovery','v1622_bounded_proposal_restore'])
 old=json.loads((R/'records/weekend_storage_v1382_20261120/RECOVERY_INDEX.json').read_text());group=next(g for g in old['verified_groups']if g['group']=='v1237');assert sha(INDEX)==group['recovery_index_sha256']
 deadline=json.loads((R/'runs/v1620_mechanism_boundary/EVALUATION_AUTHORIZATION.json').read_text())['absolute_deadline_unix'];assert time.time()+1200<deadline
 assert(R/'REVIEW_PENDING').is_file()
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0,index_sha256=sha(INDEX)),f)
 result=dict(passed=False,closed=False,models=0,physical_native=0,retained=[],new_full_archive_readback=False,prior_full_remote_group=group)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   (O/'download').mkdir();(O/'retained').mkdir();index=json.loads(INDEX.read_text());rows={r['path']:r for r in index['files']};reader=Reader(index);seen=set()
   with io.BufferedReader(reader,buffer_size=1024**2)as compressed:
    with tarfile.open(fileobj=compressed,mode='r|gz')as archive:
     for member in archive:
      assert member.isfile()and member.name in rows and member.name not in seen
      row=rows[member.name];assert row['bytes']==member.size
      h=hashlib.sha256();n=0;source=archive.extractfile(member);path=O/'retained'/Path(member.name).name;target=path.open('xb')if member.name in WANTED else None
      try:
       for block in iter(lambda:source.read(1024**2),b''):
        h.update(block);n+=len(block)
        if target:target.write(block)
      finally:
       if target:target.close()
      assert n==row['bytes']and h.hexdigest()==row['sha256'];seen.add(member.name)
      if member.name in WANTED:
       result['retained'].append(dict(original=member.name,path=str(path.relative_to(R)),bytes=n,sha256=h.hexdigest()));save('SELECTED_PROGRESS.json',result)
      if len(result['retained'])==2:break
   assert {r['original']for r in result['retained']}==WANTED
   result.update(passed=True,decoded_members_SHA_verified=len(seen),accessed_parts_all_SHA_verified=reader.parts)
  except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
  finally:signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-started);save('RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
