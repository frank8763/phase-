"""Independent saved-path/source scope diagnosis; never executes planner or vehicle code."""
import ast,csv,hashlib,importlib.abc,importlib.util,json,math,os,struct,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def same(a,b):return [f32(v)for v in a]==[f32(v)for v in b]
def angle(a,b):return math.atan2(math.sin(b-a),math.cos(b-a))
def percentile(values,p):
 v=sorted(values);x=(len(v)-1)*p/100;i=int(x);return v[i]*(1-(x-i))+v[min(i+1,len(v)-1)]*(x-i)
def metrics(path,start=0):
 vectors=[[b[j]-a[j]for j in range(2)]for a,b in zip(path,path[1:])];lengths=[math.hypot(*v)for v in vectors];assert min(lengths)>1e-8
 headings=[math.atan2(v[1],v[0])for v in vectors];rows=[]
 for j in range(1,len(path)-1):
  a,b=vectors[j-1],vectors[j];da,db=lengths[j-1],lengths[j];chord=math.hypot(a[0]+b[0],a[1]+b[1]);assert chord>1e-8
  turn=angle(headings[j-1],headings[j]);circle=2*(a[0]*b[1]-a[1]*b[0])/(da*db*chord)
  rows.append(dict(vertex=start+j,turn_rad=turn,abs_turn_rad=abs(turn),previous_segment_m=da,next_segment_m=db,signed_circumcircle_curvature_per_m=circle,original_style_abs_curvature_per_m=abs(turn)/max((da+db)/2,1e-5),raw_center_steering_rad=math.atan(.6*circle)))
 return dict(points=len(path),rows=rows,minimum_segment_m=min(lengths),max_abs_turn_rad=max(v['abs_turn_rad']for v in rows),p95_original_style_curvature=percentile([v['original_style_abs_curvature_per_m']for v in rows],95),max_original_style_curvature=max(v['original_style_abs_curvature_per_m']for v in rows),max_abs_center_steering_rad=max(abs(v['raw_center_steering_rad'])for v in rows))
def main():
 os.environ['MPLCONFIGDIR']=str(O/'mpl_cache')
 assert os.sched_getaffinity(0)=={4};start=time.monotonic();assert not(O/'MATH_TARGET_ONCE.json').exists();(O/'MATH_TARGET_ONCE.json').write_text('{}\n')
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'mujoco','torch','kernel','prediction','factory','vehicle','rclpy'}:raise AssertionError('SAVED_DIAGNOSIS_MODEL_IMPORT_FORBIDDEN:'+name)
 sys.meta_path.insert(0,Ban())
 spec=importlib.util.spec_from_file_location('v1760_immutable_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);guard.guard(O)
 inputs=read(C/'INPUTS.json')['files_SHA256'];assert all(sha(R/n)==h for n,h in inputs.items())
 original=read(R/'experiments/v1754_sccr_numpy_dependency/FIXED_FIXTURE.json')['public_route'];path=read(R/'runs/v1754_sccr_numpy_dependency/ORIGINAL_QUERY_RESPONSE.json')['selected_path'];old=read(R/'runs/v1757_sccr_path_vehicle_gate/QUERY_RESULT.json')
 prefix=0
 while prefix<min(len(path),len(original))and same(path[prefix],original[prefix]):prefix+=1
 suffix=0
 while suffix<min(len(path)-prefix,len(original)-prefix)and same(path[-1-suffix],original[-1-suffix]):suffix+=1
 assert prefix>=2 and suffix>=2
 begin=prefix-1;end=len(path)-suffix;local=path[begin:end+1];assert len(local)>=6 and same(local[0],original[begin])and same(local[-1],original[len(original)-suffix])
 full=metrics(path);inside=metrics(local,begin);straight=metrics(original);joins=[next(v for v in full['rows']if v['vertex']==index)for index in [begin,end]]
 first=next(v for v in full['rows']if v['vertex']==old['first_refusal']['vertex']);assert abs(first['raw_center_steering_rad']-old['first_refusal']['raw_center_steering_rad'])<1e-12
 assert abs(full['max_abs_center_steering_rad']-old['sampled_max_abs_center_steering_rad'])<1e-12
 tree=ast.parse((R/'runtime/mk-mini/navigation/phase22/continuous_corridor_planner.py').read_text());node=next(v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name=='_evaluate_candidate')
 calls=[v for v in ast.walk(node)if isinstance(v,ast.Call)and isinstance(v.func,ast.Attribute)and v.func.attr=='_phase21_v4_path_metrics'];assert len(calls)==1 and ast.dump(calls[0].args[0])=="Name(id='local_curve', ctx=Load())"
 cap=.42722137342572125;join_vertices={v['vertex']for v in joins};inner_exceed=[v['vertex']for v in inside['rows']if abs(v['raw_center_steering_rad'])>cap]
 h1=first['vertex']in join_vertices;h2=bool(inner_exceed);min_local=first['previous_segment_m'];min_next=first['next_segment_m']
 # Bound actual float32 coordinate quantization at the three vertices around first refusal.
 def ulp32(x):
  a=f32(abs(x));bits=struct.unpack('I',struct.pack('f',a))[0];return struct.unpack('f',struct.pack('I',bits+1))[0]-a
 coordinate_noise_bound=max(ulp32(x)for p in path[max(0,first['vertex']-1):first['vertex']+2]for x in p)/2
 quantization_turn_bound=math.asin(min(1.,2*math.sqrt(2)*coordinate_noise_bound/min_local))+math.asin(min(1.,2*math.sqrt(2)*coordinate_noise_bound/min_next));assert first['abs_turn_rad']>100*quantization_turn_bound
 result=dict(passed=True,closed=True,scope='INDEPENDENT_SAVED_SYNTHETIC_CANDIDATE_JOIN_DIAGNOSIS',models=0,original_planner_calls=0,Allocator_calls=0,physical_native=0,replay_native=0,new_independent_tasks=0,source_metric_scope='local_curve only, not active_path',source_scope_AST_verified=True,selected_path_points=len(path),original_path_points=len(original),reconstructed_curve_begin_vertex=begin,reconstructed_curve_end_vertex=end,reconstructed_local_curve_points=len(local),join_rows=joins,full_path_metrics=full,local_curve_metrics=inside,straight_path_metrics=straight,first_recorded_refusal_row=first,original_center_cap_rad=cap,Phase_curvature_cap_per_m=math.tan(cap)/.6,original_local_p95_curvature_cap=1.8,original_local_heading_delta_cap_rad=.24,local_curve_original_style_thresholds_satisfied=inside['p95_original_style_curvature']<=1.8 and inside['max_abs_turn_rad']<=.24,local_curve_phase_steering_cap_exceeded_vertices=inner_exceed,H1_first_spike_at_unchecked_join=h1,H2_interior_also_exceeds_Phase_steering=h2,H3_quantization_explanation_supported=False,float32_quantization_turn_error_bound_rad=quantization_turn_bound,float32_coordinate_half_ulp_bound_m=coordinate_noise_bound,first_spike_segments_m=[min_local,min_next],saved_gate_values_independently_matched=True,whole_navigation_passed=None,physical_feasibility_unknown=True,limitations='One already exposed synthetic candidate; sampled polyline metrics do not establish continuous BSpline or physical tracking feasibility. No old result rescoring or algorithm superiority. The original SCCR full SAC/fallback environment is not this geometric-core adaptation.',analysis_wall_s=time.monotonic()-start)
 put(O/'DIAGNOSIS.json',result)
 with(O/'CURVATURE_PROFILE.csv').open('w')as f:
  w=csv.DictWriter(f,fieldnames=list(full['rows'][0]));w.writeheader();w.writerows(full['rows'])
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
 axes[0].plot([p[0]for p in original],[p[1]for p in original],ls='--',c='#64748b',lw=1,label='Original straight path')
 axes[0].plot([p[0]for p in path],[p[1]for p in path],c='#2563eb',lw=1.5,label='Saved SCCR candidate')
 axes[0].scatter([path[v][0]for v in [begin,end]],[path[v][1]for v in [begin,end]],c='#dc2626',s=30,label='Joins');axes[0].set_aspect('equal');axes[0].set(xlabel='x (m)',ylabel='y (m)',title='One fixed synthetic candidate');axes[0].legend(fontsize=7)
 axes[1].plot([p[0]for p in path[:10]],[p[1]for p in path[:10]],'-o',c='#2563eb',ms=3)
 axes[1].scatter(*path[begin],s=50,c='#dc2626',zorder=5);axes[1].annotate(f"Join turn {math.degrees(first['abs_turn_rad']):.1f} deg",xy=path[begin],xytext=(.02,-.23),arrowprops=dict(arrowstyle='->',color='#dc2626'),fontsize=9);axes[1].set_aspect('equal');axes[1].set(xlabel='x (m)',ylabel='y (m)',title='Entry join excluded from local metric')
 xs=[v['vertex']for v in full['rows']];ys=[math.degrees(v['raw_center_steering_rad'])for v in full['rows']];axes[2].plot(xs,ys,c='#2563eb',lw=1)
 for sign in [-1,1]:axes[2].axhline(sign*math.degrees(cap),c='#dc2626',ls='--',lw=1)
 for index in [begin,end]:axes[2].axvline(index,c='#64748b',ls=':',lw=1)
 axes[2].set(xlabel='Saved path vertex',ylabel='Raw sampled steering (deg)',title='Sampled conversion vs original Phase cap')
 for ax in axes:ax.grid(alpha=.18)
 fig.suptitle('SCCR geometric-core compatibility diagnosis — saved synthetic input, zero vehicle steps',fontsize=11)
 fig.savefig(O/'sccr_join_diagnosis.png',dpi=200);fig.savefig(O/'sccr_join_diagnosis.pdf');plt.close(fig)
 text=f'''# SCCR geometric-core join diagnosis V1760\n\nOriginal source checks `local_curve` metrics and then returns the concatenated `active_path`. The saved118-point candidate has an inferred {len(local)}-point local curve, starting at vertex{begin} and ending at{end}; float32-exact original prefix/suffix determine these boundaries.\n\nThe first recorded Phase request rejection is precisely the entry join: independent turn {math.degrees(first['abs_turn_rad']):.6f} degrees, raw center steering {first['raw_center_steering_rad']:.9f}rad, original cap {cap:.9f}rad. The adjacent segments are {min_local:.6f}m/{min_next:.6f}m; coordinate half-ULP bound {coordinate_noise_bound:.3g}m. This is not explained by degenerate segments or floating-point jitter.\n\nIndependent local-curve p95 curvature {inside['p95_original_style_curvature']:.6f}/m (original local bound1.8), max heading increment {inside['max_abs_turn_rad']:.6f}rad (original bound.24). Phase center-steering-equivalent curvature cap {math.tan(cap)/.6:.6f}/m. Interior vertices exceeding that Phase cap: {len(inner_exceed)}. These two restrictions differ, so successful original geometric search alone does not qualify the Phase vehicle mapping.\n\nThis is an interpretable interface boundary on one already exposed synthetic candidate, not a new independent trial, physical safety/arrival result, full historical SCCR failure, or global infeasibility proof. Original V1754 PASS and V1757 sampled refusal remain immutable. No original planner, model, Allocator, physics, replay or SAC was executed here. The raw polyline-to-command gate also does not establish how a faithful controller would track the continuous curve.\n\nNext justified step: preregister a separately named Phase-compatible geometric-core adapter with explicit join and vehicle-envelope contract, keeping original SCCR comparison identity separate; validate its actual full-state retained-stop response before whole-task comparison. Do not silently smooth the old path, lower gates, retune old candidate, or replace the original SCCR action-fusion hierarchy. The next actual task and any tonight unattended batch await user review and explicit authorization.\n'''
 put(O/'FIGURE_PROVENANCE.json',dict(source_inputs_SHA256=inputs,models=0,new_physical_steps=0,new_planner_calls=0,analysis_valid_not_navigation_pass=True));(O/'REPORT.md').write_text(text)
 assert all(sha(R/n)==h for n,h in inputs.items())
 assert sum(p.stat().st_size for p in O.rglob('*')if p.is_file())<=8*1024**2
 print(json.dumps({k:result[k]for k in ['passed','H1_first_spike_at_unchecked_join','H2_interior_also_exceeds_Phase_steering','local_curve_original_style_thresholds_satisfied','analysis_wall_s']}))
if __name__=='__main__':main()
