"""Qualified Phase Python software preview; no model or optimizer imports."""
from context import R,C,SOURCE,read,sha,load
import copy,json
P=R/'runs/v2101_parallel_priest_vehicle/vehicle/actual';current=read(P/'PRIEST_CURRENT_INPUT.json');candidate=read(P/'PRIEST_NATIVE_RESULT.json')['answer']['candidate']
source=read(R/'runs/v2119_parallel_components_release_scope/SOURCE_FREEZE.json')['files'];source[str((C/'tracking.py').relative_to(R))]=sha(C/'tracking.py')
api=load('new_geometric_preview_software',C/'preview_adapter.py');p=api.OriginPreview(current,candidate,source,saved_software_only=True);answer=p.preview(current['origin']);expected=read(R/'runs/v2119_parallel_components_release_scope/priest/SAVED_POLYNOMIAL_PREVIEW.json')['preview']['request'];assert answer['raw_request']==expected
negatives=[]
def reject(name,fn):
 try:fn()
 except(AssertionError,ValueError):negatives.append(name)
 else:raise AssertionError('INVALID_PREVIEW_ACCEPTED:'+name)
reject('second_use',lambda:p.preview(current['origin']));p.close()
foreign=copy.deepcopy(current['origin']);foreign['body'][0]+=.001;q=api.OriginPreview(current,candidate,source,saved_software_only=True)
reject('foreign_origin',lambda:q.preview(foreign));reject('poison_after_failure',lambda:q.preview(current['origin']));q.close()
bad=dict(source);bad[str((C/'tracking.py').relative_to(R))]='0'*64;reject('changed_tracker_source',lambda:api.OriginPreview(current,candidate,bad,saved_software_only=True))
print(json.dumps(dict(passed=True,raw_request=answer['raw_request'],negative_cases=negatives,models=0,optimizer_calls=0,original_Phase_runtime=True)))
