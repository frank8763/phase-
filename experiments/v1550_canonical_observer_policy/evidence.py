"""Complete or partial response arrays, before the geometry/comparison gate.

No compression bound is inferred from raw size; future admission must reserve
full evidence, headers, journal/metadata, archive, scratch and root space.
"""
import importlib.util
from pathlib import Path

R=Path(__file__).resolve().parents[2]
INTS={'modes','gear','native'}
WIDTHS=dict(states=8,memory=5,modes=3,gear=3,encoders=4,parked=2,
            ctrl=4,raw_rows=3,requested_body=2,applied_body=2,gear_proof=10)


class Branch:
    def __init__(self, trajectory):
        self.origin=trajectory.snapshot()
        self.rows=[]

    def advance(self, trajectory, raw):
        expected_native=self.origin['native']+len(self.rows)
        assert trajectory.native==expected_native
        row=trajectory.advance(raw)
        assert row['before']['native']==expected_native and row['after']['native']==expected_native+1
        self.rows.append(row)

    def arrays(self):
        import numpy as np
        snapshots=[self.origin]+[row['after']for row in self.rows]
        result={}
        for key,source in [('states','state'),('memory','memory'),('modes','modes'),('gear','gear'),('encoders','encoders')]:
            result[key]=np.asarray([s[source]for s in snapshots],dtype=np.int64 if key in INTS else np.float64)
        result['parked']=np.asarray([[int(s['parked_target'] is not None),0. if s['parked_target'] is None else s['parked_target']]for s in snapshots],dtype=np.float64)
        result['native']=np.asarray([s['native']for s in snapshots],dtype=np.int64)
        result['sim_time']=np.asarray([s['sim_time']for s in snapshots],dtype=np.float64)
        for key,source in [('ctrl','ctrl'),('raw_rows','raw'),('requested_body','requested'),('applied_body','applied')]:
            result[key]=np.asarray([row[source]for row in self.rows],dtype=np.float64).reshape((-1,WIDTHS[key]))
        modes={'UNCHANGED':0,'GEAR_BRAKE_HOLD':1,'GEAR_RELEASE_AT_MEASURED_REST':2}
        def numeric(p):
            return [p['requested_gear'],p['prior_gear'],p['drive_gear'],p['measured_body_gear'],
                    -1 if p['brake_start'] is None else p['brake_start'],int(p['measured_rest']),
                    p['braking_native'],modes[p['mode']],int(p['released']),int(p.get('reverse_zero_drive_restart_requires_rest',False))]
        result['gear_proof']=np.asarray([numeric(row['gear_proof'])for row in self.rows],dtype=np.float64).reshape((-1,10))
        return result


def save_before_gate(branch, *, folder, name, writer, method, expected_native, accounting, first_error=None):
    """Store acknowledged prefix even on refusal; counts stay separate from rows."""
    import hashlib
    import io
    import numpy as np
    assert folder.resolve().is_relative_to(R/'runs/v1550_canonical_observer_policy/model')
    assert Path(name).name==name and not name.endswith('.npz')
    spec=importlib.util.spec_from_file_location('v1550_existing_bounded_codec',R/'experiments/v1507_priest_response_evidence/branch_store.py')
    codec=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    arrays=branch.arrays()
    buffer=io.BytesIO()
    # Uncompressed NPZ avoids making an unjustified compressed-size guarantee.
    # Parent admission must reserve this complete known schema, including ZIP
    # headers, temporary allocation and archive/delivery peaks separately.
    np.savez(buffer,**arrays)
    data=buffer.getvalue()
    path=folder/(name+'.npz')
    codec.write_atomic(path,data,writer)
    with np.load(path,allow_pickle=False) as stored:
        assert set(stored.files)==set(arrays)
        assert all(stored[k].shape==v.shape and stored[k].dtype==v.dtype and stored[k].tobytes()==v.tobytes()for k,v in arrays.items())
    receipt=dict(complete=len(branch.rows)==expected_native,expected_native=expected_native,
                 acknowledged_saved_native=len(branch.rows),model_counts=accounting,
                 first_error=first_error,response_method_sha256=method['response_method_sha256'],
                 base_method_input_sha256=method['base_method_semantic_sha256'],
                 geometry_kind=method['geometry_kind'],causal_snapshot_sha256=method['causal_snapshot_sha256'],
                 arrays=dict(path=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()),
                 stored_before_safety_or_comparison_gate=True,physical_native=0,replay_native=0)
    codec.write_atomic(folder/(name+'.json'),codec.encoded(receipt),writer)
    return arrays,receipt
