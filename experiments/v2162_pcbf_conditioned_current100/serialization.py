"""Strict finite JSON for native replies and error/close console, no numerical imports."""
import json

def _default(value):
 method=getattr(value,'tolist',None)
 if method is None:raise TypeError('UNSUPPORTED_NATIVE_JSON_TYPE:'+type(value).__name__)
 return method()

def dumps(value,**options):
 assert options.get('allow_nan',False)is False,'FINITE_NATIVE_JSON_REQUIRED'
 options['allow_nan']=False
 options.setdefault('separators',(',',':'))
 assert 'default'not in options
 return json.dumps(value,default=_default,**options)
