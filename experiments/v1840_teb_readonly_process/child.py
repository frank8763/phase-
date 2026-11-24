import os,sys,json
assert sys.stdin.buffer.read()==b''
try:
 open('FORBIDDEN_CHILD_WRITE','wb')
except OSError:
 print(json.dumps(dict(passed=True,stdin_eof=True,readonly_namespace=True,models=0,optimizer_calls=0)),flush=True)
else:raise AssertionError('NATIVE_FIXTURE_MUST_BE_READONLY')
