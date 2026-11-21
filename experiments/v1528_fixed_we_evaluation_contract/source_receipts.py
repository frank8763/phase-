"""Exact saved actual receipt reader, zero integration; never an actual capture."""
import hashlib,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def saved_prefix(*,journal,event_input,index,remote_proof,source_manifest):
 paths=[Path(x).resolve()for x in [journal,event_input,index,remote_proof]]
 assert all(p.is_relative_to(R/'runs')and p.is_file()and not p.is_symlink()for p in paths),'SAVED_RECEIPT_PATH'
 journal,event_input,index,remote_proof=paths;proof=read(remote_proof);assert proof['passed']and proof['every_member_SHA_and_link_text']and proof['recovery_index_download_SHA']
 members={v['path']:v for v in read(index)['files']};receipts=[]
 for p in [journal,event_input]:
  row=members[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];receipts.append(dict(path=str(p.relative_to(R)),bytes=row['bytes'],sha256=row['sha256']))
 current=read(event_input);copy=dict(current);identity=copy.pop('input_sha256');digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();assert digest(copy)==identity
 n=current['origin']['native_tick'];assert type(n)is int and 0<=n<=40000 and journal.stat().st_size<=32*1024**2
 normalizer=R/'experiments/v1423_integrated_route_audit/recorded.py';assert source_manifest[str(normalizer.relative_to(R))]==sha(normalizer)
 spec=importlib.util.spec_from_file_location('explicit_pure_saved_receipts',normalizer);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 with journal.open()as f:events=[json.loads(line)for line in f if line.strip()]
 rows=m.receipts(events,before_kind='BEFORE_ORIGINAL_PREFIX_NATIVE',after_kind='AFTER_ORIGINAL_PREFIX_NATIVE',bound_hash=False)
 assert [r['before_native']for r in rows]==list(range(len(rows)))and len(rows)>n,'SAVED_RECEIPT_COVERAGE'
 assert rows[n]['source_full_state_sha256']==current['full_state_sha256'],'SAVED_CURRENT_FULLSTATE_RECEIPT'
 assert rows[n]['body']==current['origin']['body']and rows[n]['last_ctrl']==current['origin']['controller_memory']['last_ctrl']and rows[n]['integral']==current['origin']['controller_memory']['integral'],'SAVED_CURRENT_PACKET_RECEIPT'
 prefix=rows[:n];assert all(r['applied']is True and len(r['request'])==3 for r in prefix)
 return current,prefix,dict(saved_actual_source_only=True,not_fresh_wire=True,actual_or_model_permission=False,raw_files=receipts,remote_index_sha256=sha(index),remote_proof_sha256=sha(remote_proof),normalizer_source_sha256=sha(normalizer),current_event_input_sha256=identity,applied_prefix_native=n,all_recorded_actual_rows=len(rows),current_receipt_fullstate_digest_bound=True,body_encoder_projection_recomputation_executed=False,independent_Allocator_recomputation_executed=False)
