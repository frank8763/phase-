"""Resource-only close grant before error or phase receipts; no action rights."""

def prepare(quota):
    retired=quota.retire_grant()
    grant=quota.prepare_grant(32*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',
        valid_for_s=300,external_writers=quota.external_writers)
    return dict(retired=retired,prepared=grant,action_or_source_authority_granted=False,
        physical_safety_and_source_clocks_unchanged=True)
