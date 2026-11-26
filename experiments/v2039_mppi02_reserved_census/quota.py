"""Same15GiB/224MiB byte enforcement, one evidence writer; read-only ROS peer emits pipe messages only."""
from context import R,C,load
base=load('v1624_original_held_quota',C/'base_quota.py')
grant=load('v1624_original_granted_quota',C/'granted_quota.py')
def single_writer_measure(output,limits):
 assert limits['storage_limit_bytes']==15*1024**3
 from reserved_census import measure
 return measure(output,limits)
# The counter census is unnecessary ONLY in this declared single-writer scope:
# native ROS peer has read-only repository/runs mounts and returns pipe bytes only;
# all persistent component evidence is written and precharged by this parent.
base.measure=single_writer_measure
grant.base.measure=single_writer_measure
EvidenceQuota=grant.EvidenceQuota
