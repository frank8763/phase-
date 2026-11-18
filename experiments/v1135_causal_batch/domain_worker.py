"""Build then independently verify every nonnegative dual bound certificate."""
import sys,json,time,signal,hashlib,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(C));from joint_domain import Domain,NORMALS
from geometry import OriginalTimed
import numpy as np

def main():
 O=Path(sys.argv[1]);O.mkdir();start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('DOMAIN600')));signal.alarm(600);x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());d=Domain(x['source']['periodic']['vertices']);n=256;width=2*np.pi/.32/n;centers=(np.arange(n)+.5)*width;upper,dual,residual=d.table(centers);margin=.08*(width/2+.075)+2e-7;bounds=upper+margin;directions=[]
 for t in centers:
  s=np.sin(.32*t);c=np.cos(.32*t);directions.append(np.array([[nx,nx*s,nx*c,ny,ny*s,ny*c]for nx,ny in NORMALS]))
 directions=np.array(directions);reconstructed=directions-np.einsum('tnj,jk->tnk',dual,d.A);certificate=np.einsum('tnj,j->tn',dual,d.b)+np.where(reconstructed>=0,reconstructed*d.upper,reconstructed*d.lower).sum(axis=2)+1e-8;assert np.all(dual>=0)and abs(certificate-upper).max()<=1e-9,'DUAL_CERTIFICATE_READBACK_FAILURE';assert abs(reconstructed-residual).max()<1e-10;assert np.all(d.A@d.witness<=d.b+1e-7)
 np.savez_compressed(O/'JOINT_TABLE.npz',bounds=bounds,centers=centers,upper=upper,dual=dual,residual=residual,A=d.A,b=d.b,lower=d.lower,upper_box=d.upper,witness=d.witness);raw=np.load(O/'JOINT_TABLE.npz');assert np.array_equal(raw['bounds'],bounds);signal.alarm(0);answer={'passed':True,'models':0,'physical_integrations':0,'dynamics_integrations':0,'phase_bins':n,'support_directions':16,'support_lp_count':n*16,'lp_calls':d.calls,'inequalities':len(d.b),'all_dual_certificates_verified':True,'max_dual_residual':d.max_residual,'motion_lipschitz_m_s':.08,'interval_half_guard_s':width/2+.075,'interval_position_guard_m':margin,'source_input_sha256':hashlib.sha256((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_bytes()).hexdigest(),'wall_s':time.monotonic()-start};dump(O/'RESULT.json',answer);print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
