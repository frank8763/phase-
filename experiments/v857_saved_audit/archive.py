"""Closed V857 evidence archive, source/decompression SHA then public download verification."""
import fcntl,gzip,hashlib,json,os,shutil,subprocess,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v857_assembly_contact';OUT=ROOT/'cloud';OUT.mkdir(exist_ok=True);REC=R/'records/v857_20261107';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-v857-assembly-20261107'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def run(args,**kwargs):return subprocess.run(args,cwd=R,check=True,**kwargs)
def gh(args,**kwargs):return run([str(GH),*args],**kwargs)
def api(path):return json.loads(gh(['api',path],capture_output=True,text=True,timeout=45).stdout)
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 assert json.loads((ROOT/'ROUND_WINDOW.json').read_text())['round_closed'];assert json.loads((REC/'SAVED_INTERFACE_AUDIT.json').read_text())['passed'];lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 paths=[]
 for current,dirs,files in os.walk(ROOT,followlinks=False):
  dirs[:]=[x for x in dirs if x!='cloud'and not(Path(current)/x).is_symlink()]
  paths.extend(Path(current)/x for x in files if x not in ['driver.lock']and(Path(current)/x).is_file()and not(Path(current)/x).is_symlink())
 inventory=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(paths)];archive=OUT/'v857-evidence.tar.zst';assert not archive.exists()
 with archive.open('wb')as f:
  z=subprocess.Popen(['zstd','-q','-3','-T1','-c'],stdin=subprocess.PIPE,stdout=f)
  with tarfile.open(fileobj=z.stdin,mode='w|')as tar:
   for row in inventory:tar.add(R/row['path'],arcname=row['path'],recursive=False)
  z.stdin.close();assert z.wait(timeout=60)==0
 expected={r['path']:r for r in inventory};seen=set();z=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE)
 with tarfile.open(fileobj=z.stdout,mode='r|')as tar:
  for m in tar:
   assert m.name in expected and m.name not in seen and m.isfile();seen.add(m.name);h=hashlib.sha256();f=tar.extractfile(m)
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
   assert h.hexdigest()==expected[m.name]['sha256']and m.size==expected[m.name]['bytes']
 assert z.wait(timeout=30)==0 and len(seen)==len(expected)
 index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',archive_name=archive.name,archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),source_files=len(paths),raw_bytes=sum(x['bytes']for x in inventory),files=inventory,source_and_decompressed_sha_verified=True,scientific_outcome='STOPPED_SERIALIZATION_INTERFACE_ONE_OLD_NATIVE_REPLAY_STEP_NO_CORRECTED_MODEL_MOTION',required_old_inputs_release='https://github.com/frank8763/phase-/releases/tag/phase-nav2-v856-20261107');dump(REC/'RECORD_INDEX.json',index);dump(OUT/'RECORD_INDEX.json',index)
 existing=[x for x in api(f'repos/{REPO}/releases?per_page=30')if x['tag_name']==TAG]
 if existing:release=existing[0]
 else:
  notes=OUT/'RELEASE_NOTES.md';notes.write_text('V857 assembly-contact model qualification. Exact two-body-pair contact change, physical parameters preserved, external collision negative fixtures retained. Original-model replay stopped after one exact native state step because of a tuple/list contact comparator error. Corrected-model motion and all navigation unexecuted. Full frozen failure and zero-model semantic-contact regression audit preserved. Not an algorithm or dynamic acceptance success.\n');head=run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip();gh(['release','create',TAG,'--repo',REPO,'--target',head,'--draft','--title','Phase V857 assembly model qualification and preserved interface failure','--notes-file',str(notes)],capture_output=True,text=True,timeout=60)
  # Query by tag directly after creation rather than racing the list cache.
  release=api(f'repos/{REPO}/releases/tags/{TAG}')
 results=[]
 for p in [archive,OUT/'RECORD_INDEX.json']:
  assets=api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100');found=[a for a in assets if a['name']==p.name]
  if not found:gh(['release','upload',TAG,str(p),'--repo',REPO],capture_output=True,text=True,timeout=180);found=[a for a in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')if a['name']==p.name]
  a=found[0];digest=sha(p);assert a['size']==p.stat().st_size and a['digest']=='sha256:'+digest
  h=hashlib.sha256();size=0
  with(OUT/(p.name+'.download.console')).open('w')as err:
   proc=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',p.name,'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=err)
   for b in iter(lambda:proc.stdout.read(1048576),b''):h.update(b);size+=len(b)
   assert proc.wait(timeout=10)==0
  assert h.hexdigest()==digest and size==p.stat().st_size;results.append(dict(name=p.name,bytes=size,sha256=digest,server_digest=a['digest'],streamed_download_sha_verified=True));print(json.dumps(results[-1]),flush=True)
 proof=dict(passed=True,release_id=release['id'],release_url=index['release_url'],assets=results,all_server_and_download_sha_verified=True,status='VERIFIED_DRAFT_AWAITING_SOURCE_PUBLICATION',verified_unix=time.time());dump(REC/'REMOTE_VERIFIED.json',proof);dump(OUT/'REMOTE_VERIFIED.json',proof)
if __name__=='__main__':main()
