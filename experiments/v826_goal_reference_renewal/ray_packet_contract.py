"""Strict JSON N-by-7 ray observations, including the valid empty observation."""
import math
import numpy as np

class RayPacketSchemaError(ValueError):
    pass

def decode_saved_rays(payload):
    """Decode seven-field rows; only [] carries an implicit empty column count."""
    if type(payload) is not list:
        raise RayPacketSchemaError('RAYS_MUST_BE_JSON_ARRAY')
    if not payload:
        return np.empty((0,7),dtype=np.float64)
    for row in payload:
        if type(row) is not list or len(row)!=7:
            raise RayPacketSchemaError('EACH_RAY_MUST_HAVE_SEVEN_FIELDS')
        for value in row:
            if type(value) not in (int,float):
                raise RayPacketSchemaError('RAY_FIELDS_MUST_BE_NUMBERS_NOT_BOOL_OR_STRING')
            try:finite=math.isfinite(value)
            except (OverflowError,TypeError,ValueError):finite=False
            if not finite:
                raise RayPacketSchemaError('RAY_FIELDS_MUST_BE_FINITE_FLOAT64_NUMBERS')
            if type(value) is int and int(float(value))!=value:
                raise RayPacketSchemaError('INTEGER_RAY_FIELD_NOT_EXACTLY_REPRESENTABLE')
    values=np.asarray(payload,dtype=np.float64)
    if values.ndim!=2 or values.shape[1]!=7 or not np.isfinite(values).all():
        raise RayPacketSchemaError('INVALID_N_BY_SEVEN_RAY_ARRAY')
    return values

def saved_rays_equal(reconstructed,payload):
    """Exact numeric equality after strict validation; no allclose or broadcasting."""
    observed=np.asarray(reconstructed)
    if observed.ndim!=2 or observed.shape[1]!=7 or observed.dtype.kind not in 'fiu' or not np.isfinite(observed).all():
        raise RayPacketSchemaError('RECONSTRUCTED_RAYS_MUST_BE_FINITE_N_BY_SEVEN')
    return bool(np.array_equal(observed,decode_saved_rays(payload)))
