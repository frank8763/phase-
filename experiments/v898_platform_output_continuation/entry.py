"""Original frozen platform program, sole legal output-root binding."""
import importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v858_nav2_verified/v898_platform'
def main():
    root=R/'runs/v896_overnight_20261108'
    approval=json.loads((root/'ENTRY_CONTINUATION_APPROVAL.json').read_text())
    assert approval.get('approved')is True,'ENTRY_REPAIR_NOT_APPROVED'
    assert approval['deadline_unix']==1794182400.,'NO_NEW_WINDOW'
    spec=importlib.util.spec_from_file_location('v896_original_frozen_platform',R/'experiments/v896_overnight_platform/qualify_native.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.O=O
    return module.main()
if __name__=='__main__':sys.exit(main())
