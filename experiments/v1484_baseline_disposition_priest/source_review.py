"""Inspect pinned author text through AST; never import its dependencies."""
import ast
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def read(path):return json.loads(Path(path).read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def inspect():
 acquisition=read(O/'ACQUISITION.json');tree=read(O/'TREE.json');entries={x['path']:x for x in tree['tree']if x['type']=='blob'}
 assert acquisition['HTTP_requests']<=12 and acquisition['downloaded_bytes']<=1048576
 assert tree['sha']==acquisition['tree']and not tree['truncated']
 records=[];parsed={}
 for record in acquisition['records']:
  if 'path'not in record:
   metadata=(O/(record['label']+'.json')).read_bytes()
   assert len(metadata)==record['bytes']and sha(metadata)==record['sha256'],'AUTHOR_METADATA_BYTES_CHANGED'
   if record['label']=='BRANCH':
    branch=json.loads(metadata);assert branch['commit']['sha']==acquisition['commit']and branch['commit']['commit']['tree']['sha']==acquisition['tree']
   continue
  path=record['path'];file=O/'upstream'/path;assert not file.is_symlink()
  raw=file.read_bytes();assert sha(raw)==record['sha256']and len(raw)==record['bytes']==entries[path]['size']
  blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert blob==record['git_blob_sha1']==entries[path]['sha']
  text=raw.decode('utf-8');node=ast.parse(text,filename=path)if path.endswith('.py')else None
  if node is not None:parsed[path]=node
  records.append(dict(path=path,bytes=len(raw),sha256=record['sha256'],git_blob_sha1=blob,url=record['url'],text_lines=len(text.splitlines()),parsed_not_executed=node is not None))
 planner=parsed['priest/src/planner_nonhol_dy.py'];solver=parsed['priest/src/mpc_non_dy.py']
 constants={}
 for node in ast.walk(planner):
  if isinstance(node,ast.Assign)and isinstance(node.value,ast.Constant):
   for t in node.targets:
    if isinstance(t,ast.Attribute)and isinstance(t.value,ast.Name)and t.value.id=='self':constants.setdefault(t.attr,[]).append(dict(line=node.lineno,value=node.value.value))
 scalar_fields=['v_max','v_min','a_max','t_fin','num','num_batch','maxiter','maxiter_cem','maxiter_mpc','a_obs_1','b_obs_1','a_obs_2','b_obs_2']
 locations={name:constants[name]for name in scalar_fields}
 calls=[]
 for node in ast.walk(planner):
  if isinstance(node,ast.Call):
   name=ast.unparse(node.func)
   if name in {'rospy.Publisher','rospy.Subscriber','message_filters.Subscriber','loadmat'}:
    calls.append(dict(line=node.lineno,function=name,first_argument=ast.unparse(node.args[0])if node.args else None))
 imports=sorted({node.module if isinstance(node,ast.ImportFrom)else alias.name for module in [planner,solver]for node in ast.walk(module)if isinstance(node,(ast.Import,ast.ImportFrom))for alias in(node.names if isinstance(node,ast.Import)else[node])})
 functions={node.name:dict(first_line=node.lineno,last_line=node.end_lineno)for node in ast.walk(solver)if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
 return dict(scope='PINNED_AUTHOR_SOURCE_STATIC_INSPECTION_NOT_RUNTIME_QUALIFICATION',author_repository='https://github.com/fatemeh-rastgar/PRIEST',commit=acquisition['commit'],tree=acquisition['tree'],source_members=records,planner_literals=locations,ROS_and_data_calls=calls,imports=imports,solver_function_locations=functions,source_modules_imported=False,models=0,ROS_nodes=0,optimizer_calls=0,physical_native=0,source_qualification_passed=None,runtime_or_model_admission=False)

if __name__=='__main__':print(json.dumps(inspect(),indent=2,allow_nan=False))
