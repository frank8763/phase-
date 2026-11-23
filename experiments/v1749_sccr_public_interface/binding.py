"""Bind original SCCR geometric core and exact helper bodies without environment construction."""
import ast,copy,hashlib,importlib.util,math,sys,__future__
from pathlib import Path
R=Path(__file__).resolve().parents[2]
PLANNER='runtime/mk-mini/navigation/phase22/continuous_corridor_planner.py'
V4='runtime/mk-mini/navigation/phase21/local_planners/phase21_v4_safe_detour.py'
V3='runtime/mk-mini/training/phase21_risk_switch_fusion_sac/envs/mkmini_phase21_v3_exact_pair_baseline.py'
V2='runtime/mk-mini/training/phase21_risk_switch_fusion_sac/envs/mkmini_phase21_v2_corridor_detect_control_failed.py'
HELPERS={V4:['_phase21_v4_densify','_phase21_v4_known_margin','_phase21_v4_path_metrics'],V3:['_phase21_v3_index_before','_phase21_v3_index_after'],V2:['_phase21_point_segment_distances']}
def checked(relative,source):
 p=R/relative;assert source[relative]==hashlib.sha256(p.read_bytes()).hexdigest(),'SCCR_SOURCE_CHANGED';return p.read_text()
def helper_tree(source):
 nodes=[];proof=[]
 for path,names in HELPERS.items():
  tree=ast.parse(checked(path,source))
  for name in names:
   found=[v for v in ast.walk(tree)if isinstance(v,ast.FunctionDef)and v.name==name];assert len(found)==1,'SCCR_HELPER_IDENTITY';node=copy.deepcopy(found[0]);nodes.append(node);proof.append(dict(path=path,name=name,original_function_AST_sha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()))
 klass=ast.ClassDef(name='OriginalGeometryHelpers',bases=[],keywords=[],body=nodes,decorator_list=[])
 return ast.fix_missing_locations(ast.Module(body=[klass],type_ignores=[])),proof
class NoPlant:
 def __init__(self,helpers,known,config,np):
  self._helpers=helpers;self._known=known;self._np=np;self._config=config
 def __getattr__(self,key):
  if key in self._config:return self._config[key]
  if key=='_phase21_v4_known_map_obstacles':return lambda:(self._np.asarray(self._known['known_rectangles'],dtype=self._np.float32).reshape(-1,4),self._np.asarray(self._known['known_circles'],dtype=self._np.float32).reshape(-1,3))
  if key in {n for names in HELPERS.values()for n in names}:
   raw=self._helpers.__dict__[key]
   return raw.__func__ if isinstance(raw,staticmethod)else raw.__get__(self,type(self))
  raise AssertionError('SCCR_PLANT_OR_TRUTH_ACCESS_FORBIDDEN:'+key)
def bind(np,source):
 tree,proof=helper_tree(source);scope=dict(np=np,math=math);exec(compile(tree,str(Path(__file__)),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),scope)
 path=R/PLANNER;checked(PLANNER,source);spec=importlib.util.spec_from_file_location('phase_original_sccr_geometric_core',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 assert Path(module.__file__).resolve()==path
 return module,scope['OriginalGeometryHelpers'],proof
