"""Small component outputs use unspent current8MiB preparation allowance."""
from common import R,S,read
def allocated(root):return sum(p.stat().st_blocks*512 for p in root.rglob('*')if p.is_file()and not p.is_symlink())
def admission():
 b=read(R/'runs/v2116_svg_remaining_five_source_boundary/BASELINE_DRAFT.json')
 assert b['preparation_bytes']==8*1024**2 and read(S/'AUTHORIZATION.json')['component_total_storage_reservation']==4*1024**2
 excluded={'runtime_archives','workers','round_reports','closed_cache','software_02'}
 base=R/'runs/v2116_svg_remaining_five_source_boundary'
 prep=allocated(R/'runs/v2118_parallel_component_runtime_inputs')+allocated(R/'runs/v2117_parallel_ackermann_components')+sum(p.stat().st_blocks*512 for p in base.rglob('*')if p.is_file()and p.relative_to(base).parts[0]not in excluded)+allocated(R/'runs/v2115_svg_remaining_five')
 assert prep+4*1024**2<=8*1024**2 and allocated(S)<=4*1024**2,'SMALL_PARALLEL_COMPONENT_STORAGE_STOP'
 return dict(passed=True,joint_peak_bytes=16095019008,limit_bytes=16106127360,within_current_preparation_grant=True,measured_other_preparation_bytes=prep,component_reserved_bytes=4*1024**2)
def transport_current_upper():
 admission();return 16095019008-(32+512)*1024**2
