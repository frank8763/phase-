"""Production branch classifier/dependency tests: all-next vs stop semantics."""
import copy
from component_context import O,dump
from relay_policy import classify,eligible


def main():
    checks=dict(fully_recorded=True,finite_all_states=True,time_monotonic=True,actual_clearance=True,full_self=True,actual_control_limits=True,actual_control_rates=True,bad_contacts_zero=True,own_full_replay=True,independent_allocation=True,complete_stop=True,component_functional=True,sources_unchanged=True,independent_whole_goal=True,independent_forward_progress=True)
    base=dict(native=dict(closed=True,passed=True,source_unchanged=True),ros=dict(passed=True,public_static_map_receipt={'passed':True}),audit=dict(passed=True,checks=checks))
    rows=[]
    def verify(name,row,expected):
        actual=classify(row);assert actual==expected,(name,actual,expected);rows.append(dict(name=name,passed=True))
    verify('all_pass',base,'PASSED')
    functional=copy.deepcopy(base);functional['native']['passed']=False;functional['ros']['passed']=False;functional['audit']['passed']=False
    for key in ['component_functional','independent_whole_goal','independent_forward_progress']:functional['audit']['checks'][key]=False
    verify('safe_full_functional_failure_continues',functional,'FUNCTIONAL_FAILURE_SAFE_COMPLETE')
    for key in ['actual_clearance','actual_control_rates','own_full_replay','fully_recorded','sources_unchanged','complete_stop']:
        row=copy.deepcopy(functional);row['audit']['checks'][key]=False;verify(key+'_stops',row,'SAFETY_CONTROL_OR_EVIDENCE_STOP')
    for key in ['native','ros','audit']:
        row=copy.deepcopy(base);row[key]=None;verify('missing_'+key,row,'EVIDENCE_OR_OPERATION_STOP')
    for owner in ['native','ros']:
        row=copy.deepcopy(base);row[owner]['error']='UNEXPECTED_OR_CONTROL_REJECTION';verify(owner+'_error',row,'CONTROL_SOURCE_OR_OPERATION_STOP')
    completed={('a','static','main'):'FUNCTIONAL_FAILURE_SAFE_COMPLETE'}
    assert not eligible(dict(branch='a',stage='static',role='repeat'),completed)
    assert not eligible(dict(branch='a',stage='dynamic',role='main'),completed)
    assert eligible(dict(branch='b',stage='static',role='main'),completed)
    completed={('a','static','main'):'PASSED',('a','static','repeat'):'PASSED'}
    assert eligible(dict(branch='a',stage='dynamic',role='main'),completed)
    assert not eligible(dict(branch='a',stage='dynamic',role='repeat'),completed)
    completed[('a','dynamic','main')]='PASSED'
    assert eligible(dict(branch='a',stage='dynamic',role='repeat'),completed)
    dump(O/'RELAY_POLICY_QUALIFICATION.json',dict(passed=True,classifications=rows,dependency_assertions=6,models=0,physical_native=0))
    print('RELAY_POLICY_PASS:13classifications+6dependencies,0models')


if __name__=='__main__':main()
