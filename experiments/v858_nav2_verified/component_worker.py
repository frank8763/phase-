"""Frozen physical component with corrected model metadata and audited contact serialization."""
import importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified/component01';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(C));import model_patch
spec=importlib.util.spec_from_file_location('contacts_semantic',R/'experiments/v857_saved_audit/contacts.py');semantic=importlib.util.module_from_spec(spec);spec.loader.exec_module(semantic)
spec=importlib.util.spec_from_file_location('physical_component',R/'experiments/v857_assembly_contact/component.py');component=importlib.util.module_from_spec(spec);spec.loader.exec_module(component);component.OUT=OUT;component.C=C;component.contact_equal=semantic.contact_equal
if __name__=='__main__':sys.exit(component.main())
