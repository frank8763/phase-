"""Stream only selected evidence into bounded zstd parts, without a giant extra tar."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from plan import R,OUT,dump
PART=512*1024**2

def main():
    plan=json.loads((OUT/'PLAN.json').read_text());assets=OUT/'assets';assets.mkdir(exist_ok=True);archives=[]
    for group,info in plan['groups'].items():
        done=OUT/(group+'.PACKED.json')
        if done.exists():
            prior=json.loads(done.read_text());assert all((assets/x['name']).stat().st_size==x['bytes']for x in prior['parts']);archives.append(prior);continue
        paths=info['files'];assert paths
        listing=OUT/(group+'.FILES.nul');listing.write_bytes(b''.join(os.fsencode(p)+b'\0'for p in paths));before={p:(R/p).stat().st_mtime_ns for p in paths};parts=[];whole=hashlib.sha256();total=0;started=time.time()
        with(OUT/(group+'.tar.console')).open('wb')as te,(OUT/(group+'.zstd.console')).open('wb')as ze:
            tar=subprocess.Popen(['tar','--no-recursion','--null','--verbatim-files-from','-T',str(listing),'-cf','-'],cwd=R,stdout=subprocess.PIPE,stderr=te)
            zstd=subprocess.Popen(['zstd','-q','-T2','-3','-c'],stdin=tar.stdout,stdout=subprocess.PIPE,stderr=ze);tar.stdout.close();index=0;target=None;size=0;digest=None
            try:
                while True:
                    block=zstd.stdout.read(1048576)
                    if not block:break
                    if target is None:
                        name=f'{group}.tar.zst.part{index:03d}';file=assets/name;assert not file.exists();target=file.open('xb');size=0;digest=hashlib.sha256()
                    target.write(block);size+=len(block);digest.update(block);whole.update(block);total+=len(block)
                    if size>=PART:
                        target.close();parts.append(dict(name=name,bytes=size,sha256=digest.hexdigest()));target=None;index+=1
                        dump(OUT/'PACK_PROGRESS.json',dict(group=group,compressed_bytes=total,parts=len(parts),elapsed_s=time.time()-started));print(json.dumps(dict(event='PART_PACKED',group=group,bytes=size,part=name)),flush=True)
                if target is not None:target.close();target=None;parts.append(dict(name=name,bytes=size,sha256=digest.hexdigest()))
                assert zstd.wait()==0 and tar.wait()==0,'TAR_OR_ZSTD_FAILED'
            finally:
                if target is not None:target.close()
                for process in [tar,zstd]:
                    if process.poll()is None:process.terminate();process.wait()
        assert all((R/p).stat().st_mtime_ns==m for p,m in before.items()),'SELECTED_INPUT_CHANGED_DURING_ARCHIVE'
        item=dict(group=group,files=len(paths),source_logical_bytes=info['bytes'],compressed_bytes=total,sha256=whole.hexdigest(),parts=parts,compression='zstd-concatenated-parts',packing_s=time.time()-started);item.update({k:info[k]for k in ['scope','blob_inventory']if k in info});dump(done,item);archives.append(item);print(json.dumps(dict(event='ARCHIVE_PACKED',group=group,compressed_bytes=total,files=len(paths))),flush=True)
    manifest=dict(schema=1,repository='frank8763/phase-',tag='phase-essential-records-20261107',scope='Selected essential records only; obsolete intermediate pools and duplicate archives omitted by user request.',archives=archives,total_compressed_bytes=sum(x['compressed_bytes']for x in archives),original_failure_outcomes_retained=True)
    dump(OUT/'RECORD_INDEX.json',manifest);print(json.dumps(dict(event='ALL_PACKED',bytes=manifest['total_compressed_bytes'],parts=sum(len(x['parts'])for x in archives))),flush=True)
if __name__=='__main__':main()
