"""Once bounded original-EW-proposal restoration; all bytes SHA before decode."""
import fcntl,hashlib,io,json,os,re,shutil,signal,subprocess,tarfile,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
INDEX=R/'runs/v1382_weekend_campaign/storage/v1237/v1237.INDEX.json';PROOF=INDEX.parent/'FULL_REMOTE_VERIFIED.json';BASE='runs/v858_nav2_verified/v1237/route_main_EAST_WEST/'
WANTED={BASE+'ROUTE_ROWS.json',BASE+'ROUTE_RECOVERY_INPUT.json'}
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,x):
 p=O/name;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.replace(p)
class Reader(io.RawIOBase):
 def __init__(self,index):self.index=index;self.iterator=iter(index['parts'][:4]);self.file=None;self.path=None;self.parts=[]
 def readable(self):return True
 def nextpart(self):
  if self.file:
   self.file.close();st=self.path.lstat();old=self.parts[-1];assert self.path.stat().st_size==old['bytes']and sha(self.path)==old['sha256'];put('VERIFIED_TRANSPORT_CLEANUP_'+old['name']+'.json',dict(path=str(self.path.relative_to(R)),sha256=old['sha256'],bytes=st.st_size,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino,verified_original_remote_part=True));assert (self.path.lstat().st_dev,self.path.lstat().st_ino,self.path.lstat().st_size,self.path.lstat().st_mtime_ns)==(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns);self.path.unlink();self.file=None
  row=next(self.iterator,None)
  if row is None:return False
  assert row['bytes']<=32*1024**2 and Path(row['name']).name==row['name'];p=O/'download'/row['name']
  prior=R/('runs/v1621_mechanism_input_recovery/download/'+row['name']if row['name'].endswith('000')else'runs/v1622_bounded_proposal_restore/download/'+row['name'])
  if prior.is_file():
   assert prior.stat().st_size<=row['bytes'];shutil.copyfile(prior,p);put('ORIGINAL_PARTIAL_'+row['name']+'.json',dict(path=str(prior.relative_to(R)),bytes=prior.stat().st_size,sha256=sha(prior),untouched=True))
  url=self.index['release_url'].replace('/tag/','/download/')+'/'+row['name']
  for call in range(12):
   offset=p.stat().st_size if p.exists()else 0
   if offset==row['bytes']:break
   end=min(offset+4*1024**2,row['bytes'])-1;piece=O/'download/range.tmp';headers=O/'download/headers.tmp';assert not piece.exists()
   answer=subprocess.run(['curl','--fail','--location','--silent','--show-error','--connect-timeout','20','--max-time','100','--range',str(offset)+'-'+str(end),'--dump-header',str(headers),'--output',str(piece),'--write-out','%{http_code}',url],cwd=R,capture_output=True,text=True,timeout=110)
   n=piece.stat().st_size if piece.exists()else 0;spans=re.findall(r'(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)\s*$',headers.read_text(errors='replace'))
   put('RANGE_'+row['name']+'_'+str(call)+'.json',dict(start=offset,end=end,bytes=n,http=answer.stdout.strip(),returncode=answer.returncode,stderr=answer.stderr[-1000:],exact_expected_total=row['bytes']))
   assert answer.returncode==0 and answer.stdout.strip()=='206'and n==end-offset+1 and spans and tuple(map(int,spans[-1]))==(offset,end,row['bytes']),'EXACT_POSITIVE_RANGE_REFUSED'
   with piece.open('rb')as f,p.open('ab')as dest:shutil.copyfileobj(f,dest,1024**2)
   piece.unlink();headers.unlink()
  assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'],'ORIGINAL_PART_SHA_REFUSED'
  self.parts.append(row);put('PART_PROGRESS.json',dict(verified=self.parts));self.path=p;self.file=p.open('rb');return True
 def readinto(self,b):
  while True:
   if self.file is None and not self.nextpart():return 0
   v=self.file.read(len(b))
   if v:b[:len(v)]=v;return len(v)
   if not self.nextpart():return 0
 def close(self):
  if self.file:self.file.close()
  super().close()
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));start=time.monotonic();auth=read(R/'runs/v1769_overnight_phase_campaign/AUTHORIZATION.json');assert time.time()+1200<auth['absolute_stop_unix']
 assert read(R/'runs/v1769_overnight_phase_campaign/NS_RELAY_RESULT.json')['passed']
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0,maximum_wall_s=1200),f)
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('EXACT_EW_RESTORE1200')));signal.alarm(1200)
 result=dict(passed=False,closed=False,models=0,physical_native=0,retained=[],old_failures_untouched=True,new_full_archive_claim=False)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   assert (R/'REVIEW_PENDING').is_file();assert int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0])+(32+512)*1024**2<15*1024**3
   original=read(R/'records/weekend_storage_v1382_20261120/RECOVERY_INDEX.json');group=next(g for g in original['verified_groups']if g['group']=='v1237');assert sha(INDEX)==group['recovery_index_sha256']and read(PROOF)['passed']
   index=read(INDEX);known={r['path']:r for r in index['files']};(O/'download').mkdir();(O/'retained').mkdir();reader=Reader(index);seen=set()
   with io.BufferedReader(reader,buffer_size=1024**2)as compressed,tarfile.open(fileobj=compressed,mode='r|gz')as archive:
    for member in archive:
     assert member.isfile()and member.name in known and member.name not in seen;expected=known[member.name];assert member.size==expected['bytes'];stream=archive.extractfile(member);h=hashlib.sha256();n=0;p=O/'retained'/Path(member.name).name;target=p.open('xb')if member.name in WANTED else None
     try:
      for block in iter(lambda:stream.read(1024**2),b''):
       h.update(block);n+=len(block)
       if target:target.write(block)
     finally:
      if target:target.close()
     assert n==expected['bytes']and h.hexdigest()==expected['sha256'];seen.add(member.name)
     if member.name in WANTED:result['retained'].append(dict(original=member.name,path=str(p.relative_to(R)),bytes=n,sha256=h.hexdigest()));put('SELECTED_PROGRESS.json',result)
     if len(result['retained'])==2:break
   assert {r['original']for r in result['retained']}==WANTED
   for row in result['retained']:
    destination=R/row['original'];destination.parent.mkdir(parents=True,exist_ok=True);assert not destination.exists()
    with destination.open('xb')as f:f.write((R/row['path']).read_bytes())
    assert sha(destination)==row['sha256']
   result.update(passed=True,decoded_members_SHA_verified=len(seen),accessed_parts_all_SHA_verified=reader.parts,restored_original_paths_exact=True)
  except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
  finally:signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-start);put('RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
