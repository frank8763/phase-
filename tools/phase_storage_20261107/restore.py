"""Restore one selected archive on demand; verify parts and prevent path escape."""
import argparse,hashlib,json,os,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
BASE='https://github.com/frank8763/phase-/releases/download/phase-essential-records-20261107/'
R=Path(__file__).resolve().parents[2]

def safe_path(root,name):
    p=Path(name);assert not p.is_absolute()and '..'not in p.parts,'UNSAFE_ARCHIVE_PATH';out=(root/p).resolve();assert out.is_relative_to(root.resolve()),'ARCHIVE_ESCAPE';return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('group',nargs='?');ap.add_argument('--list',action='store_true');a=ap.parse_args()
    with urllib.request.urlopen(BASE+'RECORD_INDEX.json',timeout=60)as f:index=json.load(f)
    if a.list:
        print(json.dumps([{k:v for k,v in x.items()if k!='parts'}for x in index['archives']],indent=2));return
    groups=[x for x in index['archives']if x['group']==a.group];assert len(groups)==1,'CHOOSE_GROUP_WITH_LIST';group=groups[0]
    cache=R/'runs/restore_cache';cache.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache)as temporary:
        temp=Path(temporary);parts=[];whole=hashlib.sha256()
        for row in group['parts']:
            p=temp/row['name'];h=hashlib.sha256();size=0
            with urllib.request.urlopen(BASE+row['name'],timeout=120)as source,p.open('wb')as out:
                for block in iter(lambda:source.read(1048576),b''):out.write(block);h.update(block);whole.update(block);size+=len(block)
            assert size==row['bytes']and h.hexdigest()==row['sha256'];parts.append(p)
        assert whole.hexdigest()==group['sha256']
        cat=subprocess.Popen(['cat',*map(str,parts)],stdout=subprocess.PIPE)
        process=subprocess.Popen(['zstd','-q','-d','-c'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close()
        try:
            with tarfile.open(fileobj=process.stdout,mode='r|')as archive:
                for member in archive:
                    target=safe_path(R,member.name)
                    if target.exists()or target.is_symlink():continue
                    target.parent.mkdir(parents=True,exist_ok=True)
                    if member.isfile():
                        with archive.extractfile(member)as source,target.open('xb')as out:shutil.copyfileobj(source,out,1048576)
                        target.chmod(member.mode&0o777)
                    elif member.isdir():target.mkdir(exist_ok=True)
                    elif member.islnk():
                        source=safe_path(R,member.linkname);assert source.is_file(),'RESTORE_HARDLINK_TARGET_FIRST';os.link(source,target)
                    elif member.issym():
                        destination=(target.parent/member.linkname).resolve();assert destination.is_relative_to(R),'EXTERNAL_SYMLINK_REJECTED';target.symlink_to(member.linkname)
                    else:raise RuntimeError('UNSUPPORTED_ARCHIVE_MEMBER')
            assert process.wait()==0 and cat.wait()==0
        finally:
            if process.poll()is None:process.terminate();process.wait()
            if cat.poll()is None:cat.terminate();cat.wait()
    print('RESTORED; temporary download cache removed. Remove restored raw data after the task and verified preservation.')
if __name__=='__main__':main()
