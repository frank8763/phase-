"""Same V1217 native and independent admission audit, isolated zero-model CLI."""
from native_audit_cli import entry
if __name__=='__main__':
    import sys
    sys.exit(entry.main())
