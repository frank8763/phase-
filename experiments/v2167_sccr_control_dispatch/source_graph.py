"""Static C3 and method providers, no runtime imports or constructors."""
from pathlib import Path
import ast,hashlib
R=Path(__file__).resolve().parents[2];ROOT=R/'runtime/mk-mini';OBJECT=('EXTERNAL','object')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Graph:
 def __init__(self,choices=None):self.trees={};self.nodes={};self.mros={};self.choices=choices or {};self.conditional_candidates={}
 def tree(self,p):
  if p not in self.trees:self.trees[p]=ast.parse(p.read_text())
  return self.trees[p]
 def node(self,key):
  p,name=key
  if p=='EXTERNAL':return None
  if key not in self.nodes:self.nodes[key]=next(n for n in self.tree(p).body if isinstance(n,ast.ClassDef)and n.name==name)
  return self.nodes[key]
 def bases(self,key):
  p,name=key
  if p=='EXTERNAL':return []if name=='object'else[OBJECT]
  tree=self.tree(p);imports={}
  for n in ast.walk(tree):
   if isinstance(n,ast.ImportFrom):
    for a in n.names:imports.setdefault(a.asname or a.name,[]).append((n.module,a.name,n.level))
  local={n.name:n for n in tree.body if isinstance(n,ast.ClassDef)};out=[]
  for b in self.node(key).bases:
   text=ast.unparse(b)
   if isinstance(b,ast.Name)and b.id in local and b.id!=name:out.append((p,b.id));continue
   if isinstance(b,ast.Name)and b.id in imports:
    options=imports[b.id];index=self.choices.get((p,b.id),0);assert 0<=index<len(options)
    if len(options)>1:self.conditional_candidates[(p,b.id)]=options
    module,remote,level=options[index];assert level==0,('RELATIVE_CLASS_IMPORT',p,module);target=ROOT/(module.replace('.','/')+'.py');assert target.is_file(),target;out.append((target,remote));continue
   assert text in {'gym.Env','gymnasium.Env','object'},('UNRESOLVED_CLASS_BASE',key,text);out.append(('EXTERNAL',text))
  return out or[OBJECT]
 def mro(self,key):
  if key in self.mros:return self.mros[key]
  if key==OBJECT:return[OBJECT]
  bases=self.bases(key);seq=[self.mro(b)[:]for b in bases]+[bases[:]];answer=[key]
  while any(seq):
   seq=[s for s in seq if s];head=next((s[0]for s in seq if all(s[0]not in t[1:]for t in seq)),None);assert head is not None,('C3_CONFLICT',key,seq);answer.append(head)
   for s in seq:
    if s and s[0]==head:s.pop(0)
  self.mros[key]=answer;return answer
 def provider(self,key,method):
  for item in self.mro(key):
   n=self.node(item)
   if n is not None:
    fn=next((x for x in n.body if isinstance(x,ast.FunctionDef)and x.name==method),None)
    if fn:return item,fn
  return None,None
 def label(self,key):return key[0]+'::'+key[1]if key[0]=='EXTERNAL'else str(key[0].relative_to(R))+'::'+key[1]
