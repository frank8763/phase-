"""Independent saved-tree accounting. Never upgrades unresolved feasibility to PASS."""
import json,math
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v717_temporal_free_viability';details=[]
for path in sorted(root.glob('CHECKPOINT_*.json')):
 data=json.loads(path.read_text());nodes={row['id']:row for row in data['nodes']};pending=[];checks=[];safe=invalid=split=unresolved=0;leaf_volume=0.;classification={}
 for row in data['nodes']:
  lo=np.array(row['lower']);hi=np.array(row['upper']);assert np.all(hi>=lo)
  tag=row['classification'];classification[tag]=classification.get(tag,0)+1
  if tag!='SPLIT':
   leaf_volume+=float(np.prod(hi-lo));continue
  axis=row['axis'];mid=(lo[axis]+hi[axis])/2
  aa=hi.copy();aa[axis]=mid;bb=lo.copy();bb[axis]=mid
  expected=[(lo,aa),(bb,hi)]
  for child,(cl,ch)in zip(row['children'],expected):
   if child in nodes:
    saved=nodes[child];checks.append(saved['lower']==cl.tolist() and saved['upper']==ch.tolist())
   else:
    pending.append(dict(id=child,lower=cl.tolist(),upper=ch.tolist(),parent_id=row['id']))
    leaf_volume+=float(np.prod(ch-cl))
 root_volume=float(np.prod(np.array(data['root_upper'])-data['root_lower']));error=abs(root_volume-leaf_volume)
 pwidth=np.array([np.array(x['upper'])-x['lower']for x in pending])
 local=dict(exact_child_partitions=all(checks),root_node_saved=nodes[0]['lower']==data['root_lower']and nodes[0]['upper']==data['root_upper'],pending_count_exact=len(pending)==data['pending_nodes'],processed_count_exact=len(nodes)==data['processed_nodes'],no_missing_state_volume=error<=1e-10*max(1.,root_volume),no_false_certificate=data['passed']is False and data['status']=='INTERVAL_CERTIFICATE_UNRESOLVED'and len(pending)>0)
 details.append(dict(step=data['step'],checks=local,passed=all(local.values()),classifications=classification,pending_nodes=len(pending),root_volume=root_volume,leaf_plus_pending_volume=leaf_volume,volume_error=error,median_pending_state_widths=np.median(pwidth,axis=0).tolist(),maximum_pending_state_widths=np.max(pwidth,axis=0).tolist()))
 (root/('PENDING_STATE_PARTITION_%03d.json'%data['step'])).write_text(json.dumps(pending,indent=2)+'\n')
out=dict(status='ALL_UNRESOLVED_PARTITIONS_ACCOUNTED'if len(details)==3 and all(x['passed']for x in details)else'PARTITION_ACCOUNTING_FAILED',details=details,feasibility_passed=False,new_integrations=0,scope='Verifies no state mass was silently removed by the node cap; does not independently establish validity of each history/safety inequality or feasibility.')
(root/'INDEPENDENT_PARTITION_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['status']=='ALL_UNRESOLVED_PARTITIONS_ACCOUNTED'
