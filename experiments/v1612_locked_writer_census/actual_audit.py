"""New content audit precedes the frozen integrated numerical-array audit."""
import hashlib
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def exact(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def integrated(task,result,*,components,source,check):
    # No import or call is made until an actual source-bound native owner
    # explicitly chooses this new wrapper. This function cannot authorize one.
    import numpy as np
    previous=exact('v1612_frozen_complete_actual_audit',C/'legacy_actual_audit.py',source)
    recorded=exact('v1612_frozen_actual_receipts',C/'recorded.py',source)
    binding=exact('v1612_actual_applied_content',C/'transition_binding.py',source)
    out=Path(task['output']);rows,events,_=recorded.collect(out,source=source)
    with np.load(out/'FULL_STATE_NPLUS1.npz',allow_pickle=False)as saved:
        full={key:saved[key].copy()for key in saved.files}
    proof=binding.verify(fullstate=full,rows=rows,events=events,method=components.method,check=check)
    answer=previous.integrated(task,result,components=components,source=source,check=check)
    return dict(answer,applied_fullstate_transition_content=proof)
