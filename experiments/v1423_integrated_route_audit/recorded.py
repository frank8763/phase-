"""Lossless receipt normalization; no plant/model imports or state changes."""
import copy
import hashlib
import json
from pathlib import Path

def read(path):return json.loads(Path(path).read_text())
def lines(path):return [json.loads(s)for s in Path(path).read_text().splitlines()if s]
def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(encode(value).encode()).hexdigest()

def receipts(events,*,before_kind,after_kind,bound_hash):
 before={};after={}
 for event in events:
  if event['kind']not in {before_kind,after_kind}:continue
  row=event['row'];tick=row['before_native'];assert type(tick)is int
  if event['kind']==before_kind:
   assert row['applied']is False and tick not in before
   if bound_hash:assert digest(row)==event['source_row_sha256']
   before[tick]=(copy.deepcopy(row),event.get('source_row_sha256'))
  else:
   assert row['applied']is True and tick in before and tick not in after
   initial,identity=before[tick]
   for key,value in initial.items():
    if key!='applied':assert row[key]==value,'APPLIED_ROW_SOURCE_CHANGED'
   if bound_hash:assert event['source_row_sha256']==identity
   after[tick]=copy.deepcopy(row)
 assert set(before)==set(after),'INCOMPLETE_NATIVE_RECEIPT'
 return [after[i]for i in sorted(after)]

def collect(output):
 out=Path(output);root=lines(out/'ACTUAL_OWNER_JOURNAL.jsonl');rows=receipts(root,before_kind='BEFORE_ORIGINAL_PREFIX_NATIVE',after_kind='AFTER_ORIGINAL_PREFIX_NATIVE',bound_hash=False);events=[]
 for folder in sorted((out/'bridge_events').glob('event*'))if(out/'bridge_events').exists()else []:
  assert folder.is_dir()and not folder.is_symlink()
  current=read(folder/'CURRENT_INPUT.json');closure=read(folder/'TRANSACTION_CLOSED.json');assert closure['closed']
  actual=folder/'actual'
  if not actual.exists():
   assert closure['passed']is False;events.append(dict(folder=folder,current=current,applied=[],admitted=False));continue
  index=read(actual/'EVIDENCE_INDEX.json');assert index['closed']and index['incomplete_receipt_native']is None
  assert hashlib.sha256((actual/'APPLIED_JOURNAL.jsonl').read_bytes()).hexdigest()==index['journal_sha256']
  applied=receipts(lines(actual/'APPLIED_JOURNAL.jsonl'),before_kind='BEFORE_NATIVE',after_kind='AFTER_NATIVE',bound_hash=True)
  assert len(applied)==index['before_native_rows']==index['after_native_rows']
  rows.extend(applied);events.append(dict(folder=folder,current=current,applied=applied,admitted=closure['passed'],evidence_index=index))
 rows.sort(key=lambda x:x['before_native']);assert [x['before_native']for x in rows]==list(range(len(rows))),'NATIVE_JOURNAL_GAP_OR_DUPLICATE'
 return rows,events,root
