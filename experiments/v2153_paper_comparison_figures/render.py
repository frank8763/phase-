"""Canonical72-task figure, no model/NLP or new physical audit."""
from pathlib import Path
import json,hashlib,os
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;OUT=R/'docs/paper_ras/working_20261126/figures';S=R/'runs/v2153_paper_comparison_figures'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert os.sched_getaffinity(0)=={1};assert not S.exists();S.mkdir();OUT.mkdir(exist_ok=True)
 p=R/'runs/v2130_common_results_readout/RESULT.json';x=json.loads(p.read_bytes());pins={str(p.relative_to(R)):sha(p)}
 for row in x['rows']:
  if row['result_path']is not None:assert sha(R/row['result_path'])==row['result_sha256']
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 import numpy as np
 from matplotlib.colors import ListedColormap,BoundaryNorm
 from matplotlib.patches import Patch
 methods=['RP-CCR','DWA','TEB','RPP','MPPI','SVG-MPPI','SCCR','PRIEST','PSF','PCBF'];tasks=[f'common_{i:02d}'for i in range(1,13)];classes=sorted({r['classification']for r in x['rows']});print(classes)
 values={'whole':0,'whole_arrival':0,'valid_refusal':1,'technical':2,'technical_censor':2,'unexecuted':3}
 # Explicitly bind the actual vocabulary rather than silently discarding rows.
 for row in x['rows']:assert row['classification']in values,row['classification']
 mat=np.full((12,10),-1)
 for row in x['rows']:mat[tasks.index(row['task_id']),methods.index(row['method'])]=values[row['classification']]
 assert(mat>=0).all()and (mat==0).sum()==7 and(mat==1).sum()==53 and(mat==2).sum()==12 and(mat==3).sum()==48
 colors=['#18755b','#dea947','#9273a9','#eeeeee'];cmap=ListedColormap(colors);norm=BoundaryNorm(np.arange(-.5,4),4)
 fig,ax=plt.subplots(figsize=(10.3,5.9));ax.imshow(mat,cmap=cmap,norm=norm,aspect='auto');ax.set_xticks(range(10),methods,rotation=25,ha='right');ax.set_yticks(range(12),[f'{i:02d}  '+('WE'if i<=4 else'NS'if i<=8 else'EW')for i in range(1,13)]);ax.set_ylabel('Locked common task and direction');ax.set_xticks(np.arange(-.5,10,1),minor=True);ax.set_yticks(np.arange(-.5,12,1),minor=True);ax.grid(which='minor',color='white',linewidth=2);ax.tick_params(which='minor',bottom=False,left=False)
 for(i,j),z in np.ndenumerate(mat):ax.text(j,i,['A','R','T','–'][int(z)],ha='center',va='center',fontsize=10,color='white'if z in[0,2]else'#333333')
 ax.legend(handles=[Patch(facecolor=c,label=t)for c,t in zip(colors,['Audited whole arrival (7)','Auditable refusal (53)','Technical censor (12)','Unexecuted (48)'])],loc='upper center',bbox_to_anchor=(.5,1.18),ncol=2,frameon=False,fontsize=9)
 fig.subplots_adjust(left=.13,bottom=.2,top=.84,right=.98)
 base=OUT/'common_120_disposition_20261127'
 for ext in ['png','pdf','svg']:fig.savefig(base.with_suffix('.'+ext),dpi=180,metadata={'Creator':'Phase canonical evidence figure'})
 plt.close(fig)
 provenance=dict(passed=True,canonical_records_SHA_verified=72,locked_denominator=120,counts=dict(whole=7,valid_refusal=53,technical=12,unexecuted=48),models=0,optimizer_calls=0,physics=0,replay=0,new_physical_audits=0,input_SHA256=pins,outputs={str(base.with_suffix('.'+ext).relative_to(R)):sha(base.with_suffix('.'+ext))for ext in ['png','pdf','svg']},source_sha256=sha(Path(__file__)),limitation='Disposition only, not fair-algorithm/statistical superiority evidence; development components excluded')
 (S/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n');assert sha(p)==pins[str(p.relative_to(R))];print(json.dumps(provenance))
if __name__=='__main__':main()
