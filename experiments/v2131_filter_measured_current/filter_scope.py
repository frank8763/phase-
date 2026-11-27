"""Exact local mathematical dependencies, temporary names restored in finally."""
from context import R,C,load,sha
import contextlib,sys,types
@contextlib.contextmanager
def scope(source):
 names=['common','geometry','kinematics','oracle','request','filter'];prior={n:sys.modules.get(n)for n in names};values={}
 try:
  for n in names:
   p=C/(n+'.py');assert source[str(p.relative_to(R))]==sha(p),'FILTER_LOCAL_DEPENDENCY_SOURCE_CHANGED'
   m=load('FILTER_EXACT_LOCAL_'+n,p);assert __import__('pathlib').Path(m.__file__).resolve()==p.resolve();sys.modules[n]=m;values[n]=m
  yield types.SimpleNamespace(**values)
 finally:
  for n in names:
   if prior[n]is None:sys.modules.pop(n,None)
   else:sys.modules[n]=prior[n]
def snapshot(source):
 with scope(source)as m:return m
