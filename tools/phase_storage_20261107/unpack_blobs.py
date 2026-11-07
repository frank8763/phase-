"""Restore selected content-addressed legacy evidence without touching existing files."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
from restore import R,safe_path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('inventory',type=Path);a=ap.parse_args();v=json.load(gzip.open(a.inventory,'rt'));base=safe_path(R,v['blob_root'])
    for row in v['rows']:
        target=safe_path(R,row['path'])
        if target.exists():continue
        source=safe_path(base,row['blob']);target.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();size=0
        with(source.open('rb')if row['encoding']=='identity'else gzip.open(source,'rb'))as stream,target.open('xb')as out:
            for block in iter(lambda:stream.read(1048576),b''):out.write(block);h.update(block);size+=len(block)
        assert size==row['bytes']and h.hexdigest()==row['sha256'],'RESTORED_BLOB_HASH_MISMATCH'
    print('Selected historical actual records restored. Full candidate prediction caches were intentionally pruned.')
if __name__=='__main__':main()
