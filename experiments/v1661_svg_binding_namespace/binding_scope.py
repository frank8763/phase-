"""Import exact frozen binding under its own context, then restore namespace."""
import sys
from context import R,load,sha

def load_bound(source,loader=load):
 directory=R/'experiments/v1656_svg_solver_interface'
 for name in ['context.py','binding.py']:
  path=directory/name;assert source[str(path.relative_to(R))]==sha(path),'EXACT_BINDING_SOURCE_MISMATCH'
 old=loader('v1661_exact_v1656_context',directory/'context.py')
 sentinel=object();previous=sys.modules.get('context',sentinel)
 try:
  sys.modules['context']=old
  bound=loader('v1661_exact_v1656_binding',directory/'binding.py')
  assert bound.O==R/'runs/v1656_svg_solver_interface','EXACT_BINDING_OUTPUT_ROOT'
  assert bound.read.__code__.co_filename==str(directory/'context.py'),'EXACT_BINDING_READ_ORIGIN'
  return bound
 finally:
  if previous is sentinel:sys.modules.pop('context',None)
  else:sys.modules['context']=previous
