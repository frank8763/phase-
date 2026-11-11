import json,sys
from pathlib import Path
def save(out,result):
 data=json.dumps(result,ensure_ascii=False,allow_nan=False)
 try:(Path(out)/'RESULT.json').write_text(data+'\n')
 except PermissionError:
  inner=Path(out)/'physics/paired/ENTRY_FAILURE_RESULT.json'
  print('ENTRY_FAILURE_RESULT '+data,file=sys.stderr,flush=True)
  inner.write_text(data+'\n')
