"""Fresh native0 current filter query; no old packet or actor data permitted."""
from context import R,C,SOURCE,O,METHOD,read,load,digest,sha

def build(np,receipt,fullstate,selected,source,*,run_id):
 known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')
 for path in[C/'request.py',C/'filter.py',C/'geometry.py',C/'kinematics.py',C/'nominal.py',R/'experiments/v855_renewal_worker/KNOWN_FIELD.json']:
  assert source[str(path.relative_to(R))]==sha(path),'FILTER_SOURCE_IDENTITY_CHANGED'
 observation=load('filter_original_observation',C/'observation.py');p=observation.verify(receipt,0,0.)
 assert p['native_tick']==0 and not p['dynamic_discovered'],'FILTER_COMPONENT_FRESH_T0_ONLY'
 nominal=load('filter_shared_nominal',C/'nominal.py').command(p,selected)
 deps=load('filter_source_scoped_dependencies',C/'filter_scope.py')
 with deps.scope(source)as math_modules:clean=math_modules.request.build(receipt,known,nominal['request'][:2],selected['gear'])
 clean.update(schema='FRESH_CURRENT_FILTER_PROPOSAL_INPUT_V1',run_id=run_id,method=METHOD,nominal_source=nominal,source_manifest_sha256=digest({str(x.relative_to(R)):sha(x)for x in[C/'filter.py',C/'geometry.py',C/'kinematics.py',C/'nominal.py']}))
 clean['input_sha256']=digest(clean)
 request=dict(schema='FILTER_CURRENT_NLP_REQUEST_V1',run_id=run_id,method=METHOD,input_sha256=clean['input_sha256'],origin_native=0,origin_sim_time=0.,case=dict(pose=clean['pose'],gear=clean['gear'],nominal=clean['nominal_twist'],causal=None,sim_time=0.),public_known=known,model_identity='EXPLICIT_IDEAL_KINEMATIC_ONLY',physical_authority=False)
 request['request_sha256']=digest(request);return dict(current=clean,request=request)
