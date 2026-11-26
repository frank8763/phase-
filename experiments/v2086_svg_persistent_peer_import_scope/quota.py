"""Original byte grants, own-output census and an existing reserved upper bound."""
from context import R,C,load,O,read
import os
base=load('v1624_original_held_quota',C/'base_quota.py')
grant=load('v1624_original_granted_quota',C/'granted_quota.py')
def measure(output,limits):
 from pathlib import Path
 assert Path(output).resolve()==O/'actual'and os.sched_getaffinity(0)=={2}
 assert limits['maximum_task_evidence_bytes']==24*1024**2
 reservation=load('SVG_reserved_component_space',C/'reservation.py').admission()
 own=base.used(output);upper=reservation['joint_peak_bytes']-(24+32+512)*1024**2+own
 return own,upper
base.measure=measure;grant.base.measure=measure
EvidenceQuota=grant.EvidenceQuota
