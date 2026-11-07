"""One final bounded Phase-only Git sync. Never retries or removes raw evidence."""
import datetime,hashlib,json,os,signal,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];out=repo/'runs/global_dynamic_overnight_20261103/GIT_SYNC_RESULT.json'
assert not out.exists(),'FINAL_SYNC_ALREADY_CLAIMED_OR_EXECUTED';assert(repo/'REVIEW_PENDING').exists()
def local(args,input=None):return subprocess.run(args,cwd=repo,input=input,capture_output=True,timeout=20,check=True).stdout
origin=local(['git','remote','get-url','origin']).decode().strip();assert origin in['https://github.com/frank8763/phase-.git','git@github.com:frank8763/phase-.git']
commit=local(['git','rev-parse','HEAD']).decode().strip();objects=local(['git','rev-list','--objects','--no-object-names','origin/main..HEAD']);sizes=local(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],objects).decode().splitlines();too_large=[]
for row in sizes:
 bits=row.split()
 if len(bits)==3 and bits[1]=='blob'and int(bits[2])>=100*1024*1024:too_large.append(dict(oid=bits[0],bytes=int(bits[2])))
result=dict(status='CLAIMED_NO_RETRY',local_scientific_commit=commit,started_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),push_limit_s=30,readback_limit_s=5,unpublished_oversized_blobs=too_large,push_attempted=False,readback_attempted=False,raw_deleted=False)
def save():out.write_text(json.dumps(result,indent=2)+'\n')
save();env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0')
def bounded(args,cap,label):
 started=time.monotonic();p=subprocess.Popen(args,cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);timed_out=False
 try:stdout,stderr=p.communicate(timeout=cap)
 except subprocess.TimeoutExpired:
  timed_out=True;os.killpg(p.pid,signal.SIGTERM)
  try:stdout,stderr=p.communicate(timeout=1)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
 (out.parent/(label+'.stdout')).write_bytes(stdout);(out.parent/(label+'.stderr')).write_bytes(stderr)
 return dict(exit_code=p.returncode,timed_out=timed_out,wall_s=time.monotonic()-started,stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest()),stdout
if too_large:result['push_skipped_reason']='UNPUBLISHED_BLOB_OVER_100MIB_NO_HISTORY_REWRITE';save()
else:
 result['push_attempted']=True;save();result['push'],_=bounded(['git','-c','pack.threads=1','push','origin','HEAD:main'],30,'final_push');save()
result['readback_attempted']=True;save();result['readback'],raw=bounded(['git','ls-remote','origin','refs/heads/main'],5,'final_remote_readback')
lines=raw.decode(errors='replace').splitlines();remote=lines[0].split()[0]if lines and len(lines[0].split())==2 else None
result.update(remote_main=remote,remote_exactly_matches_scientific_commit=remote==commit,finished_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat());result['status']='REMOTE_SCIENTIFIC_COMMIT_VERIFIED'if remote==commit else'REMOTE_DIFFERENT_OR_UNVERIFIED_NO_RETRY';save();print(json.dumps(result,indent=2))
