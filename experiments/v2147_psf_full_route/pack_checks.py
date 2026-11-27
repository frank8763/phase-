"""Production append/resolve/corruption tests with exact saved JSON, no models."""
import json,os,copy,hashlib,sys
from pathlib import Path
from context import R,C,SOURCE as S,load,put

def main():
 assert os.sched_getaffinity(0)=={4}
 mod=load('new_exact_json_pack',C/'metadata_pack.py');root=S/'pack_software';root.mkdir()
 old=R/'runs/v2137_psf_progress_control/components/PSF/actual';count=0;raw_total=0
 for pattern in ['cycle_*_origin.json','cycle_*_shadow.json','cycle_*_admission_0.json','FILTER_QUERY_*_RESULT.json']:
  for p in sorted(old.glob(pattern))[:32]:
   value=json.loads(p.read_text());name=f'FILTER_QUERY_{count:04d}_RECORD.json';raw=mod.serialized(value);mod.write(root/name,value);assert mod.read_bytes(root/name)==raw;count+=1;raw_total+=len(raw)
 proof=mod.verify_all(root);neg=[]
 def reject(name,fn):
  try:fn()
  except (AssertionError,ValueError,KeyError):neg.append(name)
  else:raise AssertionError('PACK_NEGATIVE_ACCEPTED:'+name)
 reject('duplicate_committed_logical_name',lambda:mod.write(root/'FILTER_QUERY_0000_RECORD.json',{}))
 reject('foreign_name_not_packed',lambda:mod.read_bytes(root/'RESULT.json'))
 # New independent small folders preserve every original corrupt fixture byte.
 for label,mutation in [('truncated_pack',lambda p:p.write_bytes(p.read_bytes()[:-1])),('bitflip_pack',lambda p:p.write_bytes(bytes([p.read_bytes()[0]^1])+p.read_bytes()[1:])),('index_reorder',None)]:
  d=S/('pack_negative_'+label);d.mkdir();mod.write(d/'cycle_000000_origin.json',{'x':1});mod.write(d/'cycle_000005_origin.json',{'x':2})
  if mutation:mutation(d/mod.PACK)
  else:
   p=d/mod.INDEX;lines=p.read_bytes().splitlines(keepends=True);p.write_bytes(b''.join(reversed(lines)))
  reject(label,lambda d=d:mod.verify_all(d))
 # Short-write writer poisoning: production class, no partial commit.
 d=S/'pack_negative_shortwrite';d.mkdir();w=mod.Writer(d);op=Path.open
 class Short:
  def __enter__(self):return self
  def __exit__(self,*_):return False
  def tell(self):return 0
  def write(self,data):return len(data)-1
 def patched(p,*a,**k):return Short()if p==d/mod.PACK else op(p,*a,**k)
 try:
  Path.open=patched;reject('short_write',lambda:w.append(d/'cycle_000000_origin.json',b'{}'))
 finally:Path.open=op
 reject('poison_after_short_write',lambda:w.append(d/'cycle_000005_origin.json',b'{}'))
 assert not(d/'cycle_000000_origin.json').exists()
 put(S/'PACK_SOFTWARE_PROOF.json',dict(passed=True,exact_saved_records=count,raw_serialized_bytes=raw_total,verification=proof,negative_cases=neg,models=0,optimizer_queries=0,physics=0,replay=0));print('PACK PASS',count)
if __name__=='__main__':main()
