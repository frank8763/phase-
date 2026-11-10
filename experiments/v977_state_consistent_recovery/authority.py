"""Source-only authorization. Explicitly deny every native/model entry."""
import hashlib
SCOPE='V977_SOURCE_AND_ZERO_MODEL_ONLY'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def authorized(*args,**kwargs):
    raise PermissionError('V977_NO_PHYSICAL_MODEL_AUTHORITY_USER_SELECTED_SOURCE_ONLY')

def ready_for_navigation(*args,**kwargs):
    return authorized()
