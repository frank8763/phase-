"""Source-only repair; all physical and navigation entry is denied."""
def authorized(*args,**kwargs):
    raise PermissionError('V984_SOURCE_ONLY_NO_NEW_MODEL_WINDOW')
ready_for_navigation=authorized
