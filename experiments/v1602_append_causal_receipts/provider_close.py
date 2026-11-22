"""Attempt source close after stop-send failure; preserve first and secondary."""

def close(tracker, result, send_stop):
    def failure(stage,error):
        result['passed']=False
        result.setdefault('causal_source_secondary_errors',[]).append(dict(stage=stage,error=repr(error)))
        if 'error' not in result:result['error']=stage+':'+repr(error)
    try:send_stop()
    except BaseException as error:failure('STOP_SEND',error)
    try:
        proof=tracker.close()
        if not proof['passed']:
            result.update(passed=False,causal_source_close_gap=True)
            if 'error' not in result:result['error']='CAUSAL_SOURCE_JOURNAL_CLOSE_REFUSED'
        return proof
    except BaseException as error:
        failure('CAUSAL_SOURCE_CLOSE',error)
        return dict(passed=False,error=repr(error),closure_counts_unknown=True)
