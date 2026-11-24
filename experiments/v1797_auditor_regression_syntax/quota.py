"""Same15GiB/224MiB byte enforcement, one native writer/no ROS children."""
from context import R,load
base=load('v1624_original_held_quota',R/'experiments/v1615_private_namespace_scope/base_quota.py')
grant=load('v1624_original_granted_quota',R/'experiments/v1615_private_namespace_scope/quota.py')
def single_writer_measure(output,limits):
 assert limits['storage_limit_bytes']==15*1024**3
 return base.used(output),base.used(R/'runs')
# The counter census is unnecessary ONLY in this declared single-writer scope:
# no ROS/planner/model child and no renamed external role counter exists.
base.measure=single_writer_measure
grant.base.measure=single_writer_measure
EvidenceQuota=grant.EvidenceQuota
