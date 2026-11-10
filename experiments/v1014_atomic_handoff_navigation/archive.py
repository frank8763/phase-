"""Bounded streaming archives: no duplicate combined file or full readback copy."""
import hashlib,json,os,subprocess,tarfile,threading,time
from pathlib import Path
CHUNK=32*1024**2
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()
def walk(root):
    root=Path(root)
    for base,dirs,names in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if d!='__pycache__'and not Path(base,d).is_symlink()]
        for name in names:
            p=Path(base,name)
            if p.is_file()and not p.is_symlink():yield p
def verify(record,inventory,provider):
    catalog={x['path']:x for x in inventory};seen=set();errors=[];total=hashlib.sha256()
    process=subprocess.Popen(['zstd','-q','-dc'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    def feed():
        try:
            for part in record['parts']:
                path,remove=provider(part)
                assert path.stat().st_size==part['bytes']and sha(path)==part['sha256'],'PART_SHA'
                with path.open('rb')as f:
                    for block in iter(lambda:f.read(1024**2),b''):total.update(block);process.stdin.write(block)
                if remove:path.unlink()
        except BaseException as e:errors.append(e)
        finally:process.stdin.close()
    thread=threading.Thread(target=feed,daemon=True);thread.start()
    try:
        with tarfile.open(fileobj=process.stdout,mode='r|')as tar:
            for member in tar:
                assert member.isfile()and member.name in catalog and member.name not in seen,'ARCHIVE_MEMBER'
                row=catalog[member.name];h=hashlib.sha256();stream=tar.extractfile(member)
                for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
                assert member.size==row['bytes']and h.hexdigest()==row['sha256'],'MEMBER_SHA '+member.name
                seen.add(member.name)
        while process.stdout.read(1024**2):pass
        thread.join(timeout=600);assert not thread.is_alive()and not errors,repr(errors)
        assert process.wait(timeout=10)==0 and seen==set(catalog)and total.hexdigest()==record['archive_sha256']
    finally:
        if process.poll()is None:process.kill();process.wait()
def package(root,files,out,group,budget_check=lambda:True):
    root=Path(root);out=Path(out);out.mkdir(exist_ok=False);files=sorted(set(Path(p)for p in files))
    catalog=[]
    for p in files:
        assert p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(root)
        catalog.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)))
    inventory=out/(group+'.INVENTORY.json');inventory.write_text(json.dumps(dict(files=catalog),indent=2)+'\n')
    listing=out/(group+'.FILES.nul');listing.write_bytes(b''.join(str(p.relative_to(root)).encode()+b'\0'for p in files))
    tar=subprocess.Popen(['tar','-C',str(root),'--null','-T',str(listing),'-cf','-'],stdout=subprocess.PIPE)
    zstd=subprocess.Popen(['zstd','-q','-T1','-3','-c'],stdin=tar.stdout,stdout=subprocess.PIPE);tar.stdout.close()
    splitter=subprocess.Popen(['split','-b',str(CHUNK),'-d','-a','3','-',str(out/(group+'.tar.zst.part'))],stdin=zstd.stdout);zstd.stdout.close()
    jobs=[tar,zstd,splitter]
    try:
        while any(p.poll()is None for p in jobs):
            assert budget_check(),'ARCHIVE_TEMPORARY_BUDGET_EXHAUSTED_RAW_RETAINED'
            time.sleep(.05)
        assert all(p.returncode==0 for p in jobs),'ARCHIVE_PROCESS_FAILED'
    finally:
        for p in reversed(jobs):
            if p.poll()is None:p.kill();p.wait()
    listing.unlink();parts=[];total=hashlib.sha256();size=0
    for p in sorted(out.glob(group+'.tar.zst.part*')):
        parts.append(dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)));size+=p.stat().st_size
        with p.open('rb')as f:
            for block in iter(lambda:f.read(1024**2),b''):total.update(block)
    record=dict(group=group,source_files=len(files),raw_bytes=sum(x['bytes']for x in catalog),archive_bytes=size,archive_sha256=total.hexdigest(),parts=parts)
    verify(record,catalog,lambda part:(out/part['name'],False))
    record.update(source_sha_and_decompressed_member_sha_verified=True,part_reassembly_sha_verified=True)
    return record,catalog
