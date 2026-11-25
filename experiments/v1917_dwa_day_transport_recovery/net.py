"""Phase Release transport via verified gh HTTP1, bounded read fallback."""
import json,os,subprocess,time,urllib.request,urllib.error,urllib.parse
from pathlib import Path

class Client:
    def __init__(self,root,guard,receipt):
        self.root=Path(root);self.guard=guard;self.receipt=receipt;self.release_id=None;self.read_attempts=0;self.calls=0
        self.binary=str(self.root/'tools/phase_storage_20261107/vendor/gh')
        self.env=dict(os.environ,GODEBUG='http2client=0')
        self._token=None
    def request(self,method,url,data=None,content_type='application/json',timeout=60,missing_ok=False):
        self.guard();u=urllib.parse.urlparse(url)
        assert u.scheme=='https'and u.netloc=='api.github.com'and u.path.startswith('/repos/frank8763/phase-/releases'),'ONLY_PHASE_RELEASE_API'
        endpoint=u.path.lstrip('/')+('?' +u.query if u.query else'')
        self.calls+=1;call=self.calls
        for i in range(6 if method=='GET'else 1):
            self.guard();self.read_attempts+=int(method=='GET');assert self.read_attempts<=36,'READONLY_TOTAL_CAP'
            begin=time.monotonic();error=None
            try:
                if i in {2,5} and method=='GET':
                    # Alternate only READS. Token stays in memory, never logs.
                    if self._token is None:self._token=subprocess.check_output([self.binary,'auth','token'],cwd=self.root,text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
                    req=urllib.request.Request(url,headers={'Authorization':'Bearer '+self._token,'Accept':'application/vnd.github+json','User-Agent':'PhaseEvidenceRecovery'})
                    try:
                        with urllib.request.urlopen(req,timeout=min(10,timeout))as r:raw=r.read(8*1024**2+1)
                    except urllib.error.HTTPError as e:
                        if missing_ok and e.code==404:return None
                        raise
                    assert len(raw)<=8*1024**2,'HTTP_METADATA_CAP'
                else:
                    args=[self.binary,'api',endpoint]
                    if method!='GET':args+=['--method',method,'--input','-']
                    p=subprocess.run(args,cwd=self.root,env=self.env,input=data,capture_output=True,timeout=min(15 if method=='GET'else 60,timeout))
                    if missing_ok and p.returncode and b'404'in p.stderr:return None
                    assert p.returncode==0,'GH_HTTP1_NONZERO_'+str(p.returncode)
                    raw=p.stdout;assert len(raw)<=8*1024**2,'HTTP_METADATA_CAP'
                value=json.loads(raw);self.guard()
                self.receipt(dict(call=call,attempt=i+1,method=method,transport='urllib_readonly'if i in {2,5}else'gh_HTTP1',passed=True,wall_s=time.monotonic()-begin))
                return value
            except (AssertionError,subprocess.TimeoutExpired,urllib.error.URLError,TimeoutError,ConnectionError,OSError)as e:
                error=type(e).__name__
                if isinstance(e,AssertionError)and str(e)in {'READONLY_TOTAL_CAP','HTTP_METADATA_CAP'}:raise
                self.receipt(dict(call=call,attempt=i+1,method=method,passed=False,error_type=error,wall_s=time.monotonic()-begin))
                if method!='GET'or i==5:raise AssertionError('GITHUB_TRANSFER_FAILED '+error)from None
                self.guard();time.sleep(min(8,2**i));self.guard()
        raise AssertionError('READ_BUDGET_EXHAUSTED')
    def gh(self,args,timeout=120,output=None):
        assert output is None
        if args[:1]==['api']and '--method'not in args:
            assert len(args)==2
            return json.dumps(self.request('GET','https://api.github.com/'+args[1],timeout=timeout))
        assert args[:2]==['release','upload']and len(args)==6 and args[4:]==['--repo','frank8763/phase-']and self.release_id is not None
        path=Path(args[3]);assert path.is_relative_to(self.root/'runs')and path.is_file()and not path.is_symlink()and path.stat().st_size<=32*1024**2
        self.guard()
        p=subprocess.run([self.binary,*args],cwd=self.root,env=self.env,capture_output=True,timeout=min(timeout,120))
        self.guard();assert p.returncode==0,'GITHUB_TRANSFER_FAILED UPLOAD_NONZERO_'+str(p.returncode)
        return p.stdout.decode()
