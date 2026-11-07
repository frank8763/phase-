"""Rechunk compressed archives to64MiB upload assets; original streamSHA unchanged."""
import hashlib,json
from pathlib import Path
from plan import R,OUT,dump
SIZE=64*1024**2

def main():
    index=json.loads((OUT/'RECORD_INDEX.json').read_text());assets=OUT/'assets';archives=[]
    for group in index['archives']:
        destination=[];whole=hashlib.sha256();handle=None;size=0;digest=None;number=0
        for old in group['parts']:
            p=assets/old['name'];h=hashlib.sha256();count=0
            with p.open('rb')as source:
                while True:
                    block=source.read(1048576)
                    if not block:break
                    h.update(block);count+=len(block)
                    if handle is None:
                        name=f'{group["group"]}.chunk{number:03d}.tar.zst';handle=(assets/name).open('xb');digest=hashlib.sha256();size=0
                    handle.write(block);digest.update(block);whole.update(block);size+=len(block)
                    if size>=SIZE:
                        handle.close();handle=None;destination.append(dict(name=name,bytes=size,sha256=digest.hexdigest()));number+=1
            assert count==old['bytes']and h.hexdigest()==old['sha256'];p.unlink()
        if handle is not None:handle.close();destination.append(dict(name=name,bytes=size,sha256=digest.hexdigest()))
        assert whole.hexdigest()==group['sha256'];group['parts']=destination;archives.append(group);dump(OUT/(group['group']+'.PACKED64.json'),group)
    index['archives']=archives;dump(OUT/'RECORD_INDEX.json',index);print(json.dumps(dict(bytes=index['total_compressed_bytes'],assets=sum(len(x['parts'])for x in archives),all_stream_sha_unchanged=True)),flush=True)
if __name__=='__main__':main()
