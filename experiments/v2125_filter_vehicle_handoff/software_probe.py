"""Original-runtime fresh input/nominal/provenance without models or optimization."""
import copy,json,sys,types
from context import R,C,SOURCE,METHOD,read,sha,load
P=R/'runs/v2101_parallel_priest_vehicle/vehicle/actual'
receipt=read(P/'cycle_000000_origin.json')['receipt'];selected=read(P/'PRIEST_SELECTED_SEGMENT.json')
source=read(R/'runs/v2123_causal_footprint_filters/SOURCE_FREEZE.json')['files']
for p in C.glob('*.py'):source[str(p.relative_to(R))]=sha(p)
# A foreign resident geometry must never be consumed or permanently replaced.
foreign=types.ModuleType('geometry');original=sys.modules.get('geometry');sys.modules['geometry']=foreign
try:
 builder=load('FILTER_REAL_CURRENT_BUILDER',C/'current_request.py');frame=builder.build(None,receipt,{},selected,source,run_id='explicit_saved_software_fixture')
 assert sys.modules['geometry']is foreign and frame['current']['method']==METHOD and frame['current']['native']==0 and frame['current']['nominal_twist']==[.08,0.]
finally:
 if original is None:sys.modules.pop('geometry',None)
 else:sys.modules['geometry']=original
negatives=[]
def reject(name,fn):
 try:fn()
 except(AssertionError,ValueError,KeyError):negatives.append(name)
 else:raise AssertionError('SOFTWARE_NEGATIVE_ACCEPTED:'+name)
bad=dict(source);bad[str((C/'filter.py').relative_to(R))]='0'*64;reject('changed_filter_source',lambda:builder.build(None,receipt,{},selected,bad,run_id='software'))
shift=copy.deepcopy(selected);shift['poses'][0][0]+=.01;reject('foreign_nominal_origin',lambda:builder.build(None,receipt,{},shift,source,run_id='software'))
wrong=copy.deepcopy(receipt);wrong['packet']['body'][0]+=.01;reject('current_packet_tamper',lambda:builder.build(None,wrong,{},selected,source,run_id='software'))
reverse=copy.deepcopy(selected);reverse['gear']=-1;reject('opposite_nominal_gear',lambda:builder.build(None,receipt,{},reverse,source,run_id='software'))
print(json.dumps(dict(passed=True,method=METHOD,frame=frame,negative_cases=negatives,models=0,optimizer_queries=0,resident_foreign_geometry_restored=True)))
