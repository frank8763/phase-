"""ELF pins stay exact; named nonexecuting middleware shared data separated."""
import re
WAIT={'/dev/shm/lttng-ust-wait-8','/dev/shm/lttng-ust-wait-8-1000'}
def classify(name,row,magic,pins,uid):
 if magic==b'\x7fELF':
  assert pins.get(name)==row['sha256'],'UNPINNED_NATIVE_ELF:'+name
  return 'exact_SHA_ELF'
 assert name in WAIT or re.fullmatch(r'/dev/shm/fastrtps_(?:port[0-9]{1,5}|[0-9a-f]{16})',name),'UNKNOWN_NON_ELF_MAPPING:'+name
 assert row['permissions']and all(p in {'rw-s','r--s'}for p in row['permissions']),'EXECUTABLE_OR_PRIVATE_SHM:'+name
 assert row['regular']is True and row['symlink']is False and row['uid']==uid and 0<row['bytes']<=16*1024**2,'SHM_IDENTITY_OR_SIZE:'+name
 return 'nonexecuting_middleware_shared_data'
