"""Exact original analytical loop, extracted and checked before execution."""
import ast


def bind(original, namespace):
    fn = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == 'prove')
    # response.prove statements before the first geometry construction.
    body = fn.body[:4]
    assert ast.unparse(body[0]).startswith('np = q.np')
    # Original first source line parses as three individual statements.
    cutoff = next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign)
                  and any(isinstance(t,ast.Tuple) for t in n.targets))
    body = fn.body[:cutoff]
    assert any(isinstance(n, ast.For) for n in body)
    text = '\n'.join(ast.unparse(n) for n in body)
    assert 'predictor = q.model.Predictor(setup, origin)' in text
    assert "origin = dict(q.initial(packet), steering_load_episode=False)" in text
    # Keep initial, Predictor.step and all controller-memory accesses exact.
    tail = ast.parse("return dict(states=np.asarray(ss), controls=np.asarray(uu), memory=np.asarray(mm), requests=np.asarray(requests, float))").body
    new = ast.FunctionDef(name='reconstruct',args=fn.args,body=body+tail,decorator_list=[])
    code = ast.fix_missing_locations(ast.Module(body=[new],type_ignores=[]))
    assert ast.dump(ast.Module(body=body,type_ignores=[]),include_attributes=False) == ast.dump(ast.Module(body=fn.body[:cutoff],type_ignores=[]),include_attributes=False)
    scope = dict(namespace)
    exec(compile(code, '<source-bound-original-DWA-prediction-loop>', 'exec'),scope)
    return scope['reconstruct'], dict(original_statement_count=cutoff, original_model_loop_AST_exact=True,
                                      geometry_or_old_audit_called=False)
