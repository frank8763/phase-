"""This candidate contains source qualification only, never physical authority."""


def authorized(*args,**kwargs):
    raise PermissionError('V990_SOURCE_ONLY_NO_PHYSICAL_ENTRY_OR_WINDOW')
