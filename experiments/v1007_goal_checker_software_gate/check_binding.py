"""Resolve the configured BT and reject ambiguous FollowPath checker bindings."""
import copy,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1007_goal_checker_software_gate'
def check(config,xml):
    plugins=config['controller_server']['ros__parameters']['goal_checker_plugins']
    assert plugins and len(set(plugins))==len(plugins),'INVALID_CHECKER_PLUGIN_LIST'
    root=ET.fromstring(xml);rows=[]
    for node in root.iter('FollowPath'):
        name=node.attrib.get('goal_checker_id','')
        if not name:
            assert len(plugins)==1,'AMBIGUOUS_EMPTY_GOAL_CHECKER_ID'
            name=plugins[0]
        assert name in plugins,'UNKNOWN_GOAL_CHECKER_ID'
        rows.append(dict(goal_checker_id=name))
    assert rows,'NO_FOLLOWPATH_NODE_CHECKED'
    return dict(passed=True,checked_followpath_nodes=len(rows),bindings=rows)
if __name__=='__main__':
    red=json.loads((C/'red_original.PARAMS.json').read_text());green=json.loads((C/'green_explicit.PARAMS.json').read_text())
    oldpath=Path(red['bt_navigator']['ros__parameters']['default_nav_to_pose_bt_xml']);newpath=Path(green['bt_navigator']['ros__parameters']['default_nav_to_pose_bt_xml'])
    try:check(red,oldpath.read_text())
    except AssertionError as e:assert str(e)=='AMBIGUOUS_EMPTY_GOAL_CHECKER_ID';red_result=dict(rejected=True,error=str(e))
    else:raise AssertionError('ACTUAL_CONFIGURED_BINDING_DEFECT_MISSED')
    good=check(green,newpath.read_text())
    a=copy.deepcopy(red);b=copy.deepcopy(green)
    a['bt_navigator']['ros__parameters'].pop('default_nav_to_pose_bt_xml');b['bt_navigator']['ros__parameters'].pop('default_nav_to_pose_bt_xml')
    assert a==b,'OTHER_PARAMETERS_CHANGED'
    before=ET.fromstring(oldpath.read_text());after=ET.fromstring(newpath.read_text());diffs=[]
    for x,y in zip(before.iter(),after.iter()):
        assert x.tag==y.tag
        if x.attrib!=y.attrib:diffs.append(dict(tag=x.tag,before=x.attrib,after=y.attrib))
    assert len(diffs)==1 and diffs[0]['tag']=='FollowPath'
    negatives=[]
    for name,config,xml in [
        ('wrong_checker',green,newpath.read_text().replace('goal_checker_id="general_goal_checker"','goal_checker_id="not_registered"')),
        ('checker_not_registered',dict(green,controller_server=dict(ros__parameters=dict(goal_checker_plugins=['recovery_goal_checker']))),newpath.read_text()),
        ('duplicate_plugins',dict(green,controller_server=dict(ros__parameters=dict(goal_checker_plugins=['general_goal_checker','general_goal_checker']))),newpath.read_text())]:
        try:check(config,xml)
        except AssertionError as e:negatives.append(dict(name=name,rejected=True,error=str(e)))
        else:raise AssertionError('BINDING_NEGATIVE_NOT_REJECTED '+name)
    probe=json.loads((O/'RESULTS.json').read_text());assert not probe['passed']and len(probe['rows'])==1
    result=dict(static_contract_passed=True,original_binding_rejected=red_result,proposal=good,negative_cases=negatives,
        exact_one_xml_port_change=diffs,other_model_controller_safety_parameters_unchanged=True,models=0,vehicle_native_integrations=0,
        installed_end_to_end_software_qualified=False,software_probe_not_reached_controller='Synthetic short-goal global planner returned207, so the red probe did not exercise the failing FollowPath seam; green real-server probe was not started.',
        actual_V1006_empty_checker_error_preserved=True,physical_authority=False,full_route_passed=False)
    (O/'STATIC_BINDING_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
