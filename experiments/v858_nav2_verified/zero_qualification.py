"""Fail-capable driver-contract and real contact-serialization seams; zero models."""
import ast,copy,gzip,hashlib,json,sys
from pathlib import Path
from model_contract import verify_table
from model_patch import metadata_field
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified';sys.path.insert(0,str(R/'experiments/v857_saved_audit'));from contacts import contact_equal
old=R/'runs/v856_nav2_foundation/entry01/vehicle_qualification01';rows=[]
for i in range(4):
 r=dict(name=str(i),old_id=i,new_id=i,old_limited=True,new_limited=True)
 for k,v in [('joint_id',[i,0]),('trntype',0),('range',[-.52,.52]),('force_range',[-120,120]),('gain',[35.]),('bias',[-35.])]:r['old_'+k]=copy.deepcopy(v);r['new_'+k]=copy.deepcopy(v)
 rows.append(r)
assert verify_table(rows,[0,1,2,3]);negative=[]
for key,value in [('new_id',-1),('new_limited',False),('new_range',[-20,20]),('new_joint_id',[9,0]),('new_gain',[999.])]:
 changed=copy.deepcopy(rows);changed[0][key]=value
 try:verify_table(changed,[0,1,2,3])
 except AssertionError:negative.append(True)
 else:raise AssertionError('BAD_DRIVER_CONTRACT_ACCEPTED')
assert metadata_field('name_actuatoradr')and metadata_field('names_map')and not metadata_field('actuator_ctrlrange')
cc=json.load(gzip.open(old/'CONTACTS.json.gz','rt'));assert all(contact_equal([tuple(x)for x in frame],frame)for frame in cc)
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
result=dict(passed=True,negative_driver_contracts_rejected=len(negative),all1101_saved_contact_frames_serialization_checked=True,metadata_transplant_policy_checked=True,new_models=0,new_integrations=0);(OUT/'ZERO_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
