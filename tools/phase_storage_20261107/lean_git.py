"""Replace only local Git cache with a verified shallow partial fetch of published source."""
import json,os,shutil,subprocess,time
from pathlib import Path
from plan import R,OUT,dump
GH=R/'tools/phase_storage_20261107/vendor/gh'

def main():
    assert json.loads((OUT/'CLEANUP_RESULT.json').read_text())['passed'];proof=json.loads((OUT/'SOURCE_REMOTE_VERIFIED.json').read_text());commit=proof['commit'];old=R/'.git';thin=R/'.git-thin-tmp';backup=R/'.git-pre-cleanup';assert not thin.exists()and not backup.exists()
    def oldgit(*args):return subprocess.run(['git',*args],cwd=R,check=True,text=True,capture_output=True).stdout.strip()
    identity={key:oldgit('config','--get',key)for key in ['user.name','user.email']};previous=oldgit('rev-parse','HEAD');before=shutil.disk_usage(R).free
    subprocess.run(['git','init','--bare',str(thin)],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    def git(*args,**kwargs):return subprocess.run(['git','--git-dir='+str(thin),*args],cwd=R,check=True,**kwargs)
    git('config','remote.origin.url','https://github.com/frank8763/phase-.git');git('config','remote.origin.fetch','+refs/heads/main:refs/remotes/origin/main');git('config','credential.https://github.com.helper','');git('config','--add','credential.https://github.com.helper','!'+str(GH)+' auth git-credential')
    for key,value in identity.items():git('config',key,value)
    with(OUT/'LEAN_GIT_FETCH.console').open('wb')as log:git('fetch','--depth=1','--filter=blob:none','--no-tags','origin','refs/heads/main:refs/heads/main',stdout=log,stderr=subprocess.STDOUT,timeout=300)
    actual=git('rev-parse','refs/heads/main',capture_output=True,text=True).stdout.strip();assert actual==commit,'REMOTE_HEAD_CHANGED_BEFORE_LOCAL_CACHE_RESET'
    git('symbolic-ref','HEAD','refs/heads/main');git('config','core.bare','false');git('config','core.worktree',str(R));git('read-tree',commit)
    verified=json.loads((OUT/'SOURCE_SNAPSHOT.json').read_text());paths=sorted(verified['sha256']);assert all('\n'not in p and '\r'not in p for p in paths)
    git('hash-object','-w','--no-filters','--stdin-paths',input='\n'.join(paths)+'\n',text=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    old.rename(backup)
    try:
        thin.rename(old)
        subprocess.run(['git','update-index','--refresh'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
        assert oldgit('rev-parse','HEAD')==commit;assert not oldgit('diff','--name-only')
    except BaseException:
        if old.exists():old.rename(thin)
        backup.rename(old);raise
    # All current source and selected data are already published; only the old local
    # unpublished object cache and duplicate archival history are discarded.
    shutil.rmtree(backup);after=shutil.disk_usage(R).free;dump(OUT/'LEAN_GIT_RESULT.json',dict(passed=True,published_commit=commit,previous_local_head=previous,public_history_rewritten=False,unpublished_source_preserved_in_compact_snapshot=True,old_local_object_cache_removed=True,actual_filesystem_bytes_freed=after-before,new_cache_bytes=sum(p.stat().st_size for p in old.rglob('*')if p.is_file()),models=0))
    print(json.dumps(json.loads((OUT/'LEAN_GIT_RESULT.json').read_text())),flush=True)
if __name__=='__main__':main()
