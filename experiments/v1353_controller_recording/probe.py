"""The unchanged V1352 actual controller probe with structured result encoding."""
from types import SimpleNamespace
from common import base_module, json, plain


if __name__ == '__main__':
    probe = base_module('probe')
    probe.json = SimpleNamespace(dumps=lambda value, **kwargs: json.dumps(plain(value), **kwargs))
    raise SystemExit(probe.main())
