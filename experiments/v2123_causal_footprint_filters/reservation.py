"""Share the already charged four MiB component subgrant, never a new peak."""
from common import R,S,read
M=1024**2
def allocated(p):return sum(x.stat().st_blocks*512 for x in p.rglob('*')if x.is_file()and not x.is_symlink())
def admission():
 old=R/'runs/v2119_parallel_components_release_scope';base=R/'runs/v2116_svg_remaining_five_source_boundary';exclude={'runtime_archives','workers','round_reports','closed_cache','software_02'}
 other=sum(allocated(R/'runs'/n)for n in ['v2115_svg_remaining_five','v2117_parallel_ackermann_components','v2118_parallel_component_runtime_inputs'])+sum(x.stat().st_blocks*512 for x in base.rglob('*')if x.is_file()and x.relative_to(base).parts[0]not in exclude)
 assert read(base/'BASELINE_DRAFT.json')['preparation_bytes']==8*M
 assert allocated(old)+2*M<=4*M and allocated(S)<=2*M and other+4*M<=8*M,'SHARED_COMPONENT_SUBGRANT_EXHAUSTED'
 return dict(passed=True,joint_peak_bytes=16095019008,limit_bytes=16106127360,component_reserved_bytes=2*M,shared_existing_subgrant_bytes=4*M,old_component_actual_bytes=allocated(old),other_preparation_bytes=other,no_new_peak=True)
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*M
