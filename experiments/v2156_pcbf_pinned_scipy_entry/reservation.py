"""<=1MiB new metadata inside current shared8MiB, no physical grant change."""
from context import R,ROOT,P,read
import subprocess
P=R/'runs/v2151_psf_wrapper_identity_binding'
M=1024**2
def admission():
 b=read(P/'BASELINE_DRAFT.json');assert b['metadata_bytes']==8*M and b['old_joint_peak_upper_bytes']==16095019008
 own=int(subprocess.check_output(['du','-sx','-B1',str(ROOT)],timeout=10).split()[0]);assert own<1*M
 assert b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']+(224+64+32+512)*M<=b['old_joint_peak_upper_bytes']
 # SOURCE/current metadata excluding plant evidence is<4MiB; preserve other4.
 actual=P/'components/PSF/actual';meta=sum(p.stat().st_blocks*512 for p in P.rglob('*')if p.is_file()and not p.is_symlink()and not p.is_relative_to(actual));assert meta+own<4*M
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],math_own_bytes=own,parent_metadata_bytes=meta,new_math_maximum_bytes=1*M,shared_metadata_bytes=8*M,models_authorized=False)
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*M
