"""Exercise actual request dispatch with a failed proxy and working direct route."""
from pathlib import Path
import importlib.util,json,os,subprocess,time,types,urllib.request,urllib.error,urllib.parse
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def scenario(path,*,writes=False,all_fail=False):
 m=load('isolated_actual_request_dispatch',path);env={'HTTPS_PROXY':'http://127.0.0.1:7897','HTTP_PROXY':'http://127.0.0.1:7897'};attempts=[];receipts=[];calls=[]
 def run(args,**kwargs):
  direct='--noproxy'in args or kwargs.get('env',env).get('NO_PROXY')=='*';attempts.append(dict(direct=direct,kind='curl'if args[0]=='curl'else'gh'))
  if direct and not all_fail:return types.SimpleNamespace(returncode=0,stdout=b'{"id":458891864}',stderr=b'')
  return types.SimpleNamespace(returncode=7,stdout=b'',stderr=b'controlled proxy connect failure')
 class Opener:
  def open(self,*args,**kwargs):attempts.append(dict(direct=env.get('NO_PROXY')=='*',kind='urllib'));raise urllib.error.URLError('controlled connect failure')
 m.subprocess=types.SimpleNamespace(run=run,check_output=lambda *a,**k:'SOFTWARE_TOKEN_NOT_A_CREDENTIAL',TimeoutExpired=subprocess.TimeoutExpired,DEVNULL=subprocess.DEVNULL)
 m.os=types.SimpleNamespace(environ=env);m.time=types.SimpleNamespace(monotonic=time.monotonic,sleep=lambda _:None)
 m.urllib=types.SimpleNamespace(parse=urllib.parse,error=urllib.error,request=types.SimpleNamespace(Request=urllib.request.Request,urlopen=Opener().open,build_opener=lambda *a:Opener(),ProxyHandler=urllib.request.ProxyHandler))
 client=m.Client(R,lambda:None,receipts.append);error=None;answer=None
 try:answer=client.request('POST'if writes else'GET','https://api.github.com/repos/frank8763/phase-/releases/458891864',data=b'{}'if writes else None)
 except AssertionError as e:error=str(e)
 return dict(answer=answer,error=error,attempts=attempts,receipts=receipts,read_attempts=client.read_attempts)
def main():
 os.sched_setaffinity(0,{5});assert not(D/'SOFTWARE_RESULT.json').exists()
 red=scenario(R/'experiments/v1940_content_addressed_runtime_recovery/net.py');assert red['answer']is None and len(red['attempts'])==6 and not any(x['direct']for x in red['attempts'])
 green=scenario(C/'net.py');assert green['answer']=={'id':458891864}and len(green['attempts'])==4 and green['attempts'][-1]['direct']and not any(x['direct']for x in green['attempts'][:3])
 capped=scenario(C/'net.py',all_fail=True);assert capped['answer']is None and len(capped['attempts'])==6 and capped['read_attempts']==6
 write=scenario(C/'net.py',writes=True);assert len(write['attempts'])==1 and write['answer']is None
 result=dict(passed=True,old_exact_failure_reproduced=red,new_failed_proxy_direct_fallback=green,both_routes_fail_still_six_attempt_cap=capped,uncertain_write_not_retried=write,actual_request_dispatch_tested=True,no_real_credentials_or_network=True,models=0,queries=0,physics=0)
 (D/'SOFTWARE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,old_red_attempts=6,new_green_attempts=4,both_fail_cap=6,write_no_retry=True,models=0)))
if __name__=='__main__':main()
