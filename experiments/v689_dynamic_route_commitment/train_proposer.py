"""Finite supervised learning from a passed teacher episode; zero physical integrations."""
import os,sys,json,hashlib,time,signal,argparse
from pathlib import Path
import numpy as np
import torch
from learned_proposer import Proposer
p=argparse.ArgumentParser();p.add_argument('--teacher',required=True);p.add_argument('--output',required=True);p.add_argument('--initial');a=p.parse_args()
torch.set_num_threads(1);torch.use_deterministic_algorithms(True);torch.manual_seed(688);np.random.seed(688)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FINITE_BC_60S')));signal.alarm(60)
started=time.time();root=Path(a.teacher);out=Path(a.output);out.mkdir(exist_ok=False)
r=json.loads((root/'geometry_memory/result.json').read_text());audit=json.loads((root/'INDEPENDENT_CANONICAL_AUDIT.json').read_text())
assert r['strict_safe_arrival']and audit['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'
file=root/'geometry_memory/proposal_learning_samples.jsonl';rows=[json.loads(s)for s in file.read_text().splitlines()];assert len(rows)>=100
x=np.asarray([t['features']for t in rows]);y=np.asarray([t['target']for t in rows])/[.52,.52,20.,20.]
mean=x.mean(axis=0);std=np.maximum(x.std(axis=0),.05)
net=torch.nn.Sequential(torch.nn.Linear(12,32),torch.nn.Tanh(),torch.nn.Linear(32,32),torch.nn.Tanh(),torch.nn.Linear(32,4),torch.nn.Tanh()).double()
if a.initial:
    old=Proposer(a.initial);mean=old.mean;std=old.std
    with torch.no_grad():
        for linear,layer in zip([m for m in net if isinstance(m,torch.nn.Linear)],old.parameters['layers']):linear.weight.copy_(torch.tensor(layer['weight']));linear.bias.copy_(torch.tensor(layer['bias']))
xx=torch.tensor(np.clip((x-mean)/std,-5,5),dtype=torch.float64);yy=torch.tensor(y,dtype=torch.float64)
optimizer=torch.optim.Adam(net.parameters(),lr=.001)
initial=float(torch.mean((net(xx)-yy)**2).detach())
for step in range(512):
    ids=torch.randint(len(xx),(min(128,len(xx)),));loss=torch.mean((net(xx[ids])-yy[ids])**2)
    optimizer.zero_grad();loss.backward();optimizer.step()
final=float(torch.mean((net(xx)-yy)**2).detach());layers=[]
for module in net:
    if isinstance(module,torch.nn.Linear):layers.append({'weight':module.weight.detach().numpy().tolist(),'bias':module.bias.detach().numpy().tolist()})
model={'kind':'behavior_cloned_actuator_target_proposer','mean':mean.tolist(),'std':std.tolist(),'layers':layers,'gradient_updates':512,'teacher_distance_m':r['course_distance_m'],'teacher_sample_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'teacher_role':'passed same-task development teacher','scope':'supervised proposal learning; not SAC, no independent generalization result'}
path=out/'proposer.json';path.write_text(json.dumps(model,indent=2)+'\n');loaded=Proposer(path)
with torch.no_grad():expected=net(xx).numpy()*[.52,.52,20.,20.]
errors=max(float(np.max(abs(loaded.predict(row)-target)))for row,target in zip(x,expected));assert errors<=1e-10 and final<initial
report={'status':'FINITE_BC_TRAINED','gradient_updates':512,'samples':len(rows),'initial_mse':initial,'final_mse':final,'numpy_torch_max_difference':errors,'model_sha256':loaded.sha256,'teacher':str(root),'teacher_distance_m':r['course_distance_m'],'source_sample_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'integrations':0,'sac_updates':0,'elapsed_s':time.time()-started,'evaluation_split':'separate post-freeze episodes; no within-episode random split used as generalization'}
(out/'TRAINING.json').write_text(json.dumps(report,indent=2)+'\n');signal.alarm(0);print(json.dumps(report,indent=2))
