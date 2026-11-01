"""Reconstruct frozen warm-start conversion; no physics or gradient updates."""
import os,sys,json,copy,hashlib
from pathlib import Path
import numpy as np
import torch
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(repo/'experiments/v690_visible_eight_meter'))
from learned_proposer import Proposer
root=repo/'runs/v690_visible_eight_meter';old=Proposer(repo/'runs/v688_dynamic_distance_curriculum/training_6m/proposer.json');new=Proposer(root/'training_8m/proposer.json')
read=lambda p:json.loads(p.read_text())
t=read(root/'training_8m/TRAINING.json');rows=[json.loads(s)for s in(repo/t['teacher']/'geometry_memory/proposal_learning_samples.jsonl').read_text().splitlines()]
x=np.asarray([s['features']for s in rows]);y=np.asarray([s['target']for s in rows])/[.52,.52,20,20]
rounded=copy.deepcopy(old);maximum_change=0.;conversion=[]
for layer in rounded.parameters['layers']:
 for key in ['weight','bias']:
  full=np.asarray(layer[key]);tensor=torch.tensor(layer[key]);loaded=tensor.double().numpy();numpy_round=full.astype(np.float32).astype(np.float64)
  assert np.array_equal(loaded,numpy_round)
  maximum_change=max(maximum_change,float(np.max(abs(loaded-full))));layer[key]=loaded.tolist();conversion.append({'field':key,'tensor_dtype':str(tensor.dtype),'maximum_parameter_change':float(np.max(abs(loaded-full)))})
mse=lambda model:float(np.mean((np.asarray([model.predict(z)for z in x])/[.52,.52,20,20]-y)**2))
full_mse=mse(old);rounded_mse=mse(rounded);final_mse=mse(new)
src=repo/'experiments/v690_visible_eight_meter/train_proposer.py';source=src.read_text()
checks={'registered_loader_matches':"torch.tensor(layer['weight'])"in source and"torch.tensor(layer['bias'])"in source,'runtime_default_float32':torch.get_default_dtype()==torch.float32,'initial_logged_loss_matches_actual_conversion':abs(rounded_mse-t['initial_mse'])<=1e-12,'final_logged_loss_matches_frozen_model':abs(final_mse-t['final_mse'])<=1e-12,'original_full_precision_expectation_rejected':abs(full_mse-t['initial_mse'])>1e-12}
out={'status':'FROZEN_WARM_START_FLOAT32_CONVERSION_EXPLAINS_DIFFERENCE'if all(checks.values())else'UNRESOLVED','checks':checks,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'original_full_precision_mse':full_mse,'actual_float32_to_float64_warm_start_mse':rounded_mse,'logged_initial_mse':t['initial_mse'],'final_mse':final_mse,'maximum_loaded_parameter_rounding':maximum_change,'conversion':conversion,'original_failed_audit_preserved':'FINAL_ACCOUNT_AUDIT.json','gradient_updates':0,'integration_steps':0,'scope':'loader and loss arithmetic only; no checkpoint/source/result modification or rerun'}
(root/'INITIALIZATION_PRECISION_DIAGNOSIS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='conversion'},indent=2));assert out['status']!='UNRESOLVED'
