"""Identical JSON values/order and atomic replace; whitespace only differs."""
import json
from pathlib import Path
def atomic(path,value):
 path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
 def native(v):
  if hasattr(v,'tolist'):return v.tolist()
  if hasattr(v,'item'):return v.item()
  raise TypeError(type(v).__name__)
 temporary.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False,default=native)+'\n');temporary.replace(path)
