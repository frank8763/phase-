"""Bind the unmodified historical write_guard code to one immutable task OUT."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sys
import types
R=Path(__file__).resolve().parents[2]
ORIGINAL=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'

def bind_function(guard,output):
 output=Path(output).resolve()
 assert output.is_relative_to(R/'runs')and output.is_dir()and not Path(output).is_symlink()
 assert isinstance(guard,types.FunctionType)and guard.__name__=='write_guard'and guard.__closure__ is None,'UNKNOWN_INITIALIZER_AUDIT_HOOK'
 source=Path(guard.__code__.co_filename)
 assert source.is_file()and hashlib.sha256(source.read_bytes()).hexdigest()==hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),'ORIGINAL_WRITE_GUARD_SOURCE_CHANGED'
 # Verify the exact code from the source, not merely a forged filename/name.
 module_code=compile(ORIGINAL.read_text(),str(source),'exec',dont_inherit=True)
 expected=next(item for item in module_code.co_consts if isinstance(item,types.CodeType)and item.co_name=='write_guard')
 assert guard.__code__.co_code==expected.co_code and guard.__code__.co_consts==expected.co_consts and guard.__code__.co_names==expected.co_names and guard.__code__.co_flags==expected.co_flags,'ORIGINAL_WRITE_GUARD_CODE_CHANGED'
 namespace=dict(guard.__globals__);namespace['OUT']=output
 bound=types.FunctionType(guard.__code__,namespace,guard.__name__,guard.__defaults__)
 assert bound.__code__ is guard.__code__ and bound.__globals__ is not guard.__globals__
 return bound

@contextmanager
def bind_original_guard(output):
 original_add=sys.addaudithook;receipt=dict(installed_original_guard_count=0,output=str(Path(output).resolve()),original_source_sha256=hashlib.sha256(ORIGINAL.read_bytes()).hexdigest())
 def add(guard):
  assert receipt['installed_original_guard_count']==0,'MULTIPLE_INITIALIZER_WRITE_GUARDS'
  bound=bind_function(guard,output);original_add(bound);receipt['installed_original_guard_count']+=1
 sys.addaudithook=add
 try:yield receipt
 finally:sys.addaudithook=original_add
