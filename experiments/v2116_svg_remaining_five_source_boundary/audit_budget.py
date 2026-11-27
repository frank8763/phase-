"""Within existing1200 close: reserve60 for final evidence and source checks."""
def seconds(remaining):
 value=min(1000.,float(remaining)-60.)
 assert value>60,'AUDIT_CLOSURE_HEADROOM_EXHAUSTED'
 return value
