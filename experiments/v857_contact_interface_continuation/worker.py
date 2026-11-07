"""One serialization-interface continuation, no changed science or thresholds."""
import importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v857_assembly_contact';OUT=R/'runs/v857_assembly_contact/interface01';sys.path.insert(0,str(C))
spec=importlib.util.spec_from_file_location('serialization_contacts',R/'experiments/v857_saved_audit/contacts.py');semantic=importlib.util.module_from_spec(spec);spec.loader.exec_module(semantic)
import component
component.contact_equal=semantic.contact_equal;component.OUT=OUT
if __name__=='__main__':sys.exit(component.main())
