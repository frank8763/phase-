"""Future query CLI; absent exact query authority refuses before numpy/algorithm load."""
from context import C,O,R,read,sha,load

def main():
 p=O/'CURRENT_QUERY_ADMISSION.json';assert p.is_file(),'SCCR_QUERY_NOT_ADMITTED'
 admission=read(p);assert admission.get('query_authorized')is True and admission.get('source_freeze_sha256')==sha(O/'SOURCE_FREEZE.json'),'SCCR_QUERY_NOT_ADMITTED'
 raise AssertionError('SCCR_REAL_QUERY_EXECUTION_NOT_QUALIFIED_BY_SOURCE_ONLY_ROUND')
if __name__=='__main__':main()
