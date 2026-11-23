"""External speed explicitly declared; no dynamics or optimization here."""
import math

def rows(inp):
 assert len(inp['raw_author_controls'])==14 and inp['external_speed']==.08 and inp['native_per_control']==5 and inp['stop_native']==2200
 out=[]
 for delta in inp['raw_author_controls']:
  assert type(delta)in (int,float)and math.isfinite(delta)and abs(delta)<=.42722137342572125,'RAW_STEERING_REFUSAL_NO_CLIP'
  request=[.08,.08*math.tan(delta)/.6,False]
  out.extend([request.copy()for _ in range(5)])
 out.extend([[0.,0.,False]for _ in range(2200)])
 assert len(out)==2270
 return out
