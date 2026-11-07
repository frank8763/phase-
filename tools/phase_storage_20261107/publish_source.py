"""Publish a compact snapshot descending from the existing public branch, no force push."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from plan import R,OUT,dump,walk,rel

def run(args,**kwargs):return subprocess.run(args,cwd=R,check=True,**kwargs)

def main():
    v=json.loads((OUT/'PLAN.json').read_text());files=set(v['core_git_files']);files.update(rel(p)for p in walk(R/'tools/phase_storage_20261107')if 'vendor'not in p.parts and p.suffix in {'.py','.md','.json'});files.update(rel(p)for p in walk(R/'records'))
    # Preserve the closed V855 report and small operation outcomes in the code repository.
    for name in ['AUTHORIZATION.json','PLAN_SUMMARY.json','LOCAL_UNPUBLISHED_COMMIT_HISTORY.txt']:
        files.add(rel(OUT/name))
    assert all((R/p).stat().st_size<90*1024**2 for p in files)
    previous=run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip();remote=run(['git','ls-remote','origin','refs/heads/main'],capture_output=True,text=True,timeout=30).stdout.split()[0]
    listing=OUT/'GIT_CORE_FILES.nul';listing.write_bytes(b''.join(os.fsencode(p)+b'\0'for p in sorted(files)));idx=R/'.git/storage-compact.index';env=dict(os.environ,GIT_INDEX_FILE=str(idx))
    run(['git','read-tree','--empty'],env=env);run(['git','--literal-pathspecs','add','-f','--pathspec-from-file='+str(listing),'--pathspec-file-nul'],env=env)
    tree=run(['git','write-tree'],env=env,capture_output=True,text=True).stdout.strip();message='Store essential research source, reports and cloud retention policy\n\nPreserves the existing public history. Consolidates unpublished source changes while omitting duplicate bulky intermediate archives. Selected physical records are preserved as verified Release assets.\n';commit=run(['git','commit-tree',tree,'-p',remote],env=env,input=message,text=True,capture_output=True).stdout.strip()
    hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest()for p in files if(R/p).is_file()and not(R/p).is_symlink()};dump(OUT/'SOURCE_SNAPSHOT.json',dict(commit=commit,tree=tree,parent_public_head=remote,previous_local_head=previous,files=len(files),sha256=hashes,public_history_rewritten=False))
    # Retain the unpublished branch locally until selected records are remotely verified.
    backup='refs/heads/local-before-storage-20261107';run(['git','update-ref',backup,previous]);run(['git','update-ref','refs/heads/storage-essential-20261107',commit]);print(json.dumps(dict(event='COMPACT_SOURCE_PREPARED',commit=commit,parent=remote,files=len(files))),flush=True)
    with(OUT/'SOURCE_PUSH.console').open('w')as stream:run(['git','-c','pack.threads=2','push','origin',commit+':refs/heads/main'],stdout=stream,stderr=subprocess.STDOUT,timeout=900)
    actual=run(['git','ls-remote','origin','refs/heads/main'],capture_output=True,text=True,timeout=30).stdout.split()[0];assert actual==commit;dump(OUT/'SOURCE_REMOTE_VERIFIED.json',dict(passed=True,commit=commit,tree=tree,remote_head=actual,files=len(files),public_history_rewritten=False));print(json.dumps(dict(event='SOURCE_REMOTE_VERIFIED',commit=commit)),flush=True)
if __name__=='__main__':main()
