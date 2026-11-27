"""Lossless charged JSON records; zero-length logical names commit last.

Only immutable cycle/query/chunk records use this representation. Authority,
progress, RESULT and the physical evidence retain their original JSON files.
The append index carries exact lengths, SHA and a chain; no record is omitted.
"""
from pathlib import Path
import hashlib,json,re,zlib
PACK='PSF_METADATA.pack';INDEX='PSF_METADATA_INDEX.jsonl';CAP=4*1024**2
_writers={};_indexes={}
def eligible(path):
 return bool(re.fullmatch(r'(cycle_\d{6}_.+|FILTER_QUERY_\d{3,4}_.+|FILTER_CONSOLE_CHUNK_\d{6})\.json',Path(path).name))
def h(raw):return hashlib.sha256(raw).hexdigest()
def serialized(value):
 def native(x):
  if hasattr(x,'tolist'):return x.tolist()
  if hasattr(x,'item'):return x.item()
  raise TypeError(type(x).__name__)
 return (json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False,default=native)+'\n').encode()
class Writer:
 def __init__(self,folder):
  self.root=Path(folder);self.pack=self.root/PACK;self.index=self.root/INDEX
  assert not self.pack.exists()and not self.index.exists()
  self.offset=0;self.chain='0'*64;self.names=set();self.poisoned=False
 def append(self,path,raw):
  path=Path(path);assert eligible(path)and path.parent==self.root and not path.exists()and path.name not in self.names and not self.poisoned,'METADATA_APPEND_IDENTITY_OR_POISON'
  assert isinstance(raw,bytes)and len(raw)<=CAP
  self.poisoned=True;self.names.add(path.name);compressed=zlib.compress(raw,1)
  row=dict(name=path.name,offset=self.offset,bytes=len(compressed),raw_bytes=len(raw),raw_sha256=h(raw),compressed_sha256=h(compressed),previous=self.chain)
  row['chain']=h(json.dumps(row,sort_keys=True,separators=(',',':')).encode())
  with self.pack.open('ab')as f:assert f.tell()==self.offset and f.write(compressed)==len(compressed);f.flush()
  with self.index.open('ab')as f:
   line=json.dumps(row,separators=(',',':')).encode()+b'\n';assert f.write(line)==len(line);f.flush()
  # Committed logical member appears only after both durable data and index.
  with path.open('xb')as f:f.flush()
  self.offset+=len(compressed);self.chain=row['chain'];self.poisoned=False
  _indexes.pop(str(self.root),None)
def write(path,value):
 path=Path(path);key=str(path.parent)
 if key not in _writers:_writers[key]=Writer(path.parent)
 return _writers[key].append(path,serialized(value))
def index(folder):
 folder=Path(folder);p=folder/INDEX;pack=folder/PACK;s=p.stat();signature=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,pack.stat().st_size)
 old=_indexes.get(str(folder))
 if old is not None and old[0]==signature:return old[1]
 rows={};offset=0;chain='0'*64
 with p.open('rb')as f:
  for line in f:
   assert len(line)<4096 and line.endswith(b'\n'),'METADATA_INDEX_TRUNCATED'
   row=json.loads(line);assert eligible(row['name'])and row['name']not in rows and row['offset']==offset and row['previous']==chain,'METADATA_INDEX_ORDER_OR_DUPLICATE'
   clean={k:v for k,v in row.items()if k!='chain'};assert row['chain']==h(json.dumps(clean,sort_keys=True,separators=(',',':')).encode()),'METADATA_INDEX_CHAIN'
   assert type(row['bytes'])is int and 0<row['bytes']<=CAP+4096 and type(row['raw_bytes'])is int and 0<=row['raw_bytes']<=CAP
   rows[row['name']]=row;offset+=row['bytes'];chain=row['chain']
 assert offset==pack.stat().st_size,'METADATA_PACK_TRAILING_OR_TRUNCATED'
 _indexes[str(folder)]=(signature,rows);return rows
def read_bytes(path):
 path=Path(path);assert eligible(path)and not path.is_symlink()and path.stat().st_size==0,'METADATA_NOT_LOGICAL_RECORD'
 row=index(path.parent)[path.name]
 with(path.parent/PACK).open('rb')as f:f.seek(row['offset']);data=f.read(row['bytes'])
 assert len(data)==row['bytes']and h(data)==row['compressed_sha256'],'METADATA_PACK_COMPRESSED_SHA'
 decoder=zlib.decompressobj();raw=decoder.decompress(data,CAP+1)
 assert len(raw)==row['raw_bytes']and decoder.eof and not decoder.unused_data and h(raw)==row['raw_sha256'],'METADATA_PACK_RAW_SHA'
 return raw
def verify_all(folder):
 folder=Path(folder);rows=index(folder)
 assert set(rows)=={p.name for p in folder.iterdir()if p.is_file()and p.stat().st_size==0 and eligible(p)},'METADATA_COMMITTED_NAME_COVERAGE'
 for name in rows:read_bytes(folder/name)
 return dict(records=len(rows),pack_bytes=(folder/PACK).stat().st_size,index_bytes=(folder/INDEX).stat().st_size,all_raw_bytes_SHA_verified=True)
