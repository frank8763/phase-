"""Pre-model independent XML mutation and saved-evidence seam checks."""
import ast,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from model_patch import make_xml,PAIRS
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v857_assembly_contact';OLD=R/'runs/v856_nav2_foundation/entry01/vehicle_qualification01'
def main():
    # No MuJoCo import: test exact source XML, output scope and semantic mutation.
    original=OLD/'paired/assets/isolated_indoor.xml';target=OUT/'ZERO_TEST_MODEL.xml';assets=R/'runtime/mk-mini/training/assets/mkmini_real/meshes_fixed';make_xml(original,target,assets)
    old=ET.parse(original).getroot();new=ET.parse(target).getroot();pairs=[(x.get('body1'),x.get('body2'))for x in new.find('contact')];assert pairs==PAIRS
    new.remove(new.find('contact'));new.find('compiler').set('meshdir',old.find('compiler').get('meshdir'));assert ET.tostring(new)==ET.tostring(old),'UNDECLARED_XML_MUTATION'
    expected=json.loads((R/'records/nav2_v856_20261107/DIAGNOSIS.json').read_text())['inputs']
    for p,digest in expected.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==digest
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    result=dict(passed=True,new_models=0,new_integrations=0,exact_two_pair_xml_mutation=True,old_saved_inputs_sha_verified=True,unmodified_controller_sha256=hashlib.sha256((R/'experiments/v856_nav2_foundation/vehicle_control.py').read_bytes()).hexdigest(),asset_files_exist=all((assets/name).is_file()for name in ['mkmini_chassis_fixed.stl','mkmini_wheel_fixed.stl']))
    assert result['asset_files_exist'];(OUT/'ZERO_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
