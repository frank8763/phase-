"""Exact CLOSED incremental upper bounds; no global baseline change or cleanup."""
from pathlib import Path
import hashlib,json
from context import R,SOURCE,read,sha
def validate():
 b=read(SOURCE/'BASELINE_DRAFT.json');p=SOURCE/'CLOSED_INCREMENT_INVENTORY.json';assert sha(p)==b['closed_increment_inventory_sha256'];v=read(p)
 assert v['passed']and v['no_deletion']and v['all_other_previous_increments_unchanged']and v['frozen_prior_baseline_bytes']==b['frozen_prior_baseline_bytes']==14873092096
 totals={'V2137_PLUS_SOFTWARE':0,'V2141':0};listed=set()
 for row in v['rows']:
  name=row['path'];assert name not in listed;listed.add(name);p=R/name;assert p.is_file()and not p.is_symlink();s=p.stat()
  assert (s.st_size,s.st_blocks*512,s.st_mtime_ns,s.st_dev,s.st_ino)==(row['size'],row['allocated'],row['mtime_ns'],row['device'],row['inode'])and sha(p)==row['sha256'],'CLOSED_CREDIT_FILE_CHANGED:'+name
  totals[row['group']]+=row['allocated']
 assert totals['V2137_PLUS_SOFTWARE']<=54*1024**2 and totals['V2141']<=26*1024**2
 assert b['prior_V2137_closed_and_V2138_metadata_upper_bytes']==54*1024**2 and b['prior_V2141_closed_evidence_upper_bytes']==26*1024**2
 room=b['limit_bytes']-(b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']+(272+512)*1024**2)
 assert room>=24_000_000,'ORIGINAL_INITIALIZER_AND_CLOSURE_RESERVE_NOT_AVAILABLE'
 return dict(passed=True,credited_closed_allocated_bytes=totals,original_272_IO_512_root_reserves_preserved=True,initial_own_room_bytes=room,frozen_baseline_unchanged=True,no_deletion=True)
