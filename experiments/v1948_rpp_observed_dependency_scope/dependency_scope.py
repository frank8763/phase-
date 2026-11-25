"""Exact ELF inventory plus two non-executable ROS tracing wait objects."""
WAIT_FILES=frozenset({'/dev/shm/lttng-ust-wait-8-1000','/dev/shm/lttng-ust-wait-8'})
def validate_new_mapping(name,row,magic,allowed):
 if magic==b'\x7fELF':
  assert name in allowed and row['sha256']==allowed[name],'UNPINNED_RPP_NATIVE_DEPENDENCY:'+name
  return 'exact_SHA_ELF'
 assert name in WAIT_FILES,'UNDECLARED_NON_ELF_MAPPING:'+name
 assert row.get('permissions')and all('x'not in p for p in row['permissions']),'EXECUTABLE_TRACING_MAPPING:'+name
 return 'non_executable_tracing_wait'
