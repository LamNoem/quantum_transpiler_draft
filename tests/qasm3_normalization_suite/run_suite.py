#!/usr/bin/env python3
"""Test a user-supplied OpenQASM 3 normalizer without calling transpile().

Examples (from the extracted suite directory):
    python run_suite.py                              # IMPORT CHECKS ONLY
    python run_suite.py --project-root .. --normalizer norm:Norm
    python run_suite.py --project-root .. --normalizer norm:Norm --only '03_symbolic/*'
    python run_suite.py --project-root .. --pipeline adapters:normalize_and_restore

Normalizers receive a DAGCircuit and may return a DAGCircuit, QuantumCircuit,
an object exposing .normalized_dag, or None for in-place transformation.
Optional validators receive a QuantumCircuit; reject with ValueError or False.
A pipeline receives/returns a QuantumCircuit, including terminal measurements.
It must preserve logical wire order; placement and routing are NOT tested here.
"""
from __future__ import annotations

import argparse
import copy
import fnmatch
import importlib
from importlib.metadata import PackageNotFoundError, version
import io
import json
import math
from pathlib import Path
import sys
import time
import traceback
from collections import Counter
from contextlib import redirect_stderr
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
KNOWN_IMPORT_REJECTIONS = {
    'QASM3ImporterError', 'QASM3ParsingError', 'CircuitError', 'ConversionError'
}


def load_callable(spec: str | None) -> Callable[..., Any] | None:
    if spec is None:
        return None
    if ':' not in spec:
        raise ValueError(f'Use module:callable, not {spec!r}')
    module_name, object_name = spec.split(':', 1)
    obj = importlib.import_module(module_name)
    for part in object_name.split('.'):
        obj = getattr(obj, part)
    if not callable(obj):
        raise TypeError(f'{spec!r} is not callable')
    return obj


def parameters_for_reference(qc: Any, random_trials: int) -> list[dict[Any, float]]:
    """Bind by Parameter identity, not lexical position in a numeric vector."""
    params = sorted(qc.parameters, key=lambda p: p.name)
    if not params:
        return [{}]
    samples = [{p: x for p in params} for x in [0.0, math.pi / 2, math.pi, 2 * math.pi]]
    samples.append({p: (-1) ** i * (0.317 + 0.413 * i) for i, p in enumerate(params)})
    samples.append({p: (-1) ** (i + 1) * (1.137 + 0.227 * i) for i, p in enumerate(params)})
    rng = np.random.default_rng(20260930)
    for _ in range(random_trials):
        samples.append({p: float(rng.uniform(-2 * math.pi, 2 * math.pi)) for p in params})
    return samples


def split_body(qc: Any) -> tuple[Any, list[tuple[int, int]], int]:
    """Reference scaffolding, NOT a claim that the user's frontend was tested.

    Accepts gates, barriers, and unique final q-to-c measurements. Terminality is
    per wire, and any classical control, repeated readout, classical overwrite,
    reset or timing instruction is outside this helper's restricted contract.
    The separate policy-probe cases are not passed to this helper.
    """
    body = qc.copy_empty_like()
    body.global_phase = qc.global_phase
    measured: set[int] = set()
    destinations: set[int] = set()
    measurements: list[tuple[int, int]] = []
    barriers = 0
    for instruction in qc.data:
        op = instruction.operation
        qidx = [qc.find_bit(q).index for q in instruction.qubits]
        cidx = [qc.find_bit(c).index for c in instruction.clbits]
        if op.name == 'barrier':
            barriers += 1
            continue
        if op.name == 'measure':
            if len(qidx) != 1 or len(cidx) != 1:
                raise ValueError('This runner requires an explicit single-bit measurement destination.')
            if qidx[0] in measured:
                raise ValueError('Repeated measurements require an explicit policy; see policy probes.')
            if cidx[0] in destinations:
                raise ValueError('Classical destination overwrite requires an explicit policy.')
            measured.add(qidx[0])
            destinations.add(cidx[0])
            measurements.append((qidx[0], cidx[0]))
            continue
        if hasattr(op, 'blocks') or getattr(op, 'condition', None) is not None:
            raise ValueError('Classical control is outside the unitary-body contract.')
        if not isinstance(op, Gate) or cidx:
            raise ValueError(f'Non-unitary/directive operation {op.name!r} requires a frontend decision.')
        if measured.intersection(qidx):
            raise ValueError('A measured qubit is used by a later quantum operation.')
        body.append(copy.deepcopy(op), instruction.qubits, instruction.clbits)
    return body, measurements, barriers


def check_basis(qc: Any) -> list[str]:
    """Check actual gate semantics/classes, not just a potentially custom name."""
    allowed = {'h': (HGate, 1, 0), 'x': (XGate, 1, 0),
               'rz': (RZGate, 1, 1), 'cx': (CXGate, 2, 0)}
    problems = []
    for index, instruction in enumerate(qc.data):
        op = instruction.operation
        if op.name not in allowed:
            problems.append(f'operation {index}: non-basis gate {op.name!r}')
            continue
        gate_class, nqubits, nparams = allowed[op.name]
        if getattr(op, 'base_class', type(op)) is not gate_class:
            problems.append(f'operation {index}: name {op.name!r} is not a canonical {gate_class.__name__}')
        if op.num_qubits != nqubits or len(op.params) != nparams or op.num_clbits:
            problems.append(f'operation {index}: malformed {op.name!r} arity')
        if op.name == 'cx' and getattr(op, 'ctrl_state', 1) != 1:
            problems.append(f'operation {index}: negative-control CX is not the internal positive-control CX')
    return problems


def call_normalizer(normalizer: Callable[..., Any], qc: Any) -> tuple[Any, dict[str, Any]]:
    dag = circuit_to_dag(copy.deepcopy(qc))
    input_snapshot = copy.deepcopy(dag)
    result = normalizer(dag)
    aliases = (hasattr(result, 'orig_dag') and hasattr(result, 'normalized_dag')
               and result.orig_dag is result.normalized_dag)
    if result is None:
        output = dag
    elif hasattr(result, 'normalized_dag'):
        output = result.normalized_dag
    else:
        output = result
    if isinstance(output, DAGCircuit):
        output = dag_to_circuit(output)
    if not isinstance(output, QuantumCircuit):
        raise TypeError('Normalizer must return a DAGCircuit, QuantumCircuit, .normalized_dag object, or None.')
    return copy.deepcopy(output), {
        'input_dag_mutated': dag != input_snapshot,
        'orig_and_normalized_dag_alias': bool(aliases),
    }


def same_wires(before: Any, after: Any) -> bool:
    return (before.num_qubits == after.num_qubits
            and before.num_clbits == after.num_clbits
            and before.qubits == after.qubits
            and before.clbits == after.clbits)


def matrix_checks(before: Any, after: Any, args: argparse.Namespace,
                  oracle: str | None = None) -> dict[str, Any]:
    extra = set(after.parameters) - set(before.parameters)
    if extra:
        return {'ok': False, 'reason': 'NEW_PARAMETER_IDENTITIES',
                'details': 'Normalization introduced new/recreated Parameters: ' + ', '.join(p.name for p in extra)}
    # Removal of genuinely cancelled parameters is legitimate.
    if before.num_qubits > args.max_qubits:
        return {'ok': None, 'reason': 'MATRIX_CHECK_NOT_RUN_TOO_WIDE'}
    all_exact = True
    all_physical = True
    worst_error = 0.0
    first_mismatch = None
    assignments = parameters_for_reference(before, args.random_bindings)
    for mapping in assignments:
        a = before.assign_parameters(mapping, inplace=False, strict=False)
        b = after.assign_parameters(mapping, inplace=False, strict=False)
        if a.parameters or b.parameters:
            return {'ok': False, 'reason': 'UNBOUND_PARAMETERS_AFTER_TEST_BINDING'}
        reference = Operator(a)
        actual = Operator(b)
        if not np.isfinite(reference.data).all() or not np.isfinite(actual.data).all():
            return {'ok': False, 'reason': 'NONFINITE_OPERATOR'}
        if oracle == 'identity':
            eye = np.eye(reference.data.shape[0], dtype=complex)
            if not np.allclose(reference.data, eye, atol=args.atol, rtol=args.rtol):
                return {'ok': False, 'reason': 'REFERENCE_IDENTITY_ORACLE_FAILED',
                        'details': 'The imported input disagrees with an analytic identity; inspect importer semantics or the test.'}
        exact = bool(np.allclose(reference.data, actual.data, atol=args.atol, rtol=args.rtol))
        physical = bool(reference.equiv(actual, atol=args.atol, rtol=args.rtol))
        error = float(np.max(np.abs(reference.data - actual.data)))
        worst_error = max(worst_error, error)
        all_exact = all_exact and exact
        all_physical = all_physical and physical
        if first_mismatch is None and (not physical or (args.phase == 'exact' and not exact)):
            first_mismatch = {p.name: value for p, value in mapping.items()}
    return {'ok': all_exact if args.phase == 'exact' else all_physical,
            'reason': 'OPERATOR_MISMATCH' if not all_physical else ('GLOBAL_PHASE_LOST' if not all_exact else 'EQUIVALENT'),
            'exact_equal': all_exact, 'equivalent_up_to_global_phase': all_physical,
            'max_absolute_matrix_error': worst_error, 'bindings_checked': len(assignments),
            'first_failing_binding': first_mismatch}


def validate_with_user(validator: Callable[..., Any], qc: Any) -> tuple[bool, str]:
    try:
        result = validator(copy.deepcopy(qc))
    except ValueError as exc:
        return False, f'{type(exc).__name__}: {exc}'
    # Other exception types propagate as errors; a broken validator must not
    # receive credit for an expected rejection. Adapt custom domain exceptions
    # to ValueError in a thin user adapter.
    if result is False:
        return False, 'validator returned False'
    return True, 'validator accepted'


def run_case(case: dict[str, Any], args: argparse.Namespace,
             normalizer: Callable[..., Any] | None,
             validator: Callable[..., Any] | None,
             pipeline: Callable[..., Any] | None) -> dict[str, Any]:
    start = time.perf_counter()
    result: dict[str, Any] = {'id': case['id'], 'kind': case['kind'],
                              'purpose': case['purpose'], 'file': case['file']}
    def finish(status: str, detail: str = '') -> dict[str, Any]:
        result.update(status=status, detail=detail, seconds=round(time.perf_counter() - start, 6))
        return result

    kind = case['kind']
    parse_stderr = io.StringIO()
    try:
        with redirect_stderr(parse_stderr):
            original = qasm3.load(str(ROOT / case['file']))
    except Exception as exc:
        result['import_error'] = f'{type(exc).__name__}: {exc}'
        if parse_stderr.getvalue():
            result['import_stderr'] = parse_stderr.getvalue()
        if type(exc).__name__ not in KNOWN_IMPORT_REJECTIONS:
            return finish('ERROR_IMPORT', result['import_error'])
        if kind == 'invalid_qasm':
            return finish('PASS_INVALID_REJECTED', result['import_error'])
        if kind in {'feature_probe', 'policy_probe', 'reject_policy'}:
            return finish('BLOCKED_IMPORT', result['import_error'])
        return finish('FAIL_IMPORT_REQUIRED', result['import_error'])

    result['imported_operations'] = dict(original.count_ops())
    result['num_qubits'] = original.num_qubits
    result['num_clbits'] = original.num_clbits
    result['parameters'] = sorted(p.name for p in original.parameters)
    if kind == 'invalid_qasm':
        # The optional validator may perform semantic validation missed by the importer.
        if validator is not None:
            try:
                accepted, detail = validate_with_user(validator, original)
            except Exception as exc:
                return finish('ERROR_VALIDATOR', f'{type(exc).__name__}: {exc}')
            if not accepted:
                return finish('PASS_INVALID_REJECTED_BY_VALIDATOR', detail)
        return finish('FAIL_INVALID_ACCEPTED', 'Importer accepted intentionally invalid source; add/check semantic validation.')

    if kind == 'reject_policy':
        if validator is None:
            return finish('NOT_TESTED_POLICY', 'Connect --validator module:function; importer acceptance does not test your input policy.')
        try:
            accepted, detail = validate_with_user(validator, original)
        except Exception as exc:
            return finish('ERROR_VALIDATOR', f'{type(exc).__name__}: {exc}')
        return finish('FAIL_POLICY_ACCEPTED' if accepted else 'PASS_POLICY_REJECTED', detail)

    if kind == 'policy_probe':
        if validator is None:
            return finish('DECISION_NEEDED', case['note'] or case['purpose'])
        try:
            accepted, detail = validate_with_user(validator, original)
        except Exception as exc:
            return finish('ERROR_VALIDATOR', f'{type(exc).__name__}: {exc}')
        return finish('POLICY_ACCEPTED' if accepted else 'POLICY_REJECTED', detail)

    if validator is not None:
        try:
            accepted, detail = validate_with_user(validator, original)
        except Exception as exc:
            return finish('ERROR_VALIDATOR', f'{type(exc).__name__}: {exc}')
        if not accepted:
            return finish('UNSUPPORTED_POLICY' if kind == 'feature_probe' else 'FAIL_VALID_REJECTED', detail)

    if normalizer is None and pipeline is None:
        return finish('IMPORT_OK_ONLY', 'No normalizer/pipeline connected; normalization was NOT tested.')

    try:
        body, measurement_map, barrier_count = split_body(original)
        frozen_reference = copy.deepcopy(body)
        result['reference_measurement_map'] = measurement_map
        result['barriers_in_input'] = barrier_count
    except Exception as exc:
        return finish('SCAFFOLD_UNSUPPORTED' if kind == 'feature_probe' else 'ERROR_REFERENCE_PREFLIGHT', f'{type(exc).__name__}: {exc}')

    try:
        if pipeline is not None:
            output = pipeline(copy.deepcopy(original))
            if not isinstance(output, QuantumCircuit):
                raise TypeError('--pipeline callable must return a QuantumCircuit.')
            if not same_wires(original, output):
                return finish('FAIL_WIRES', 'Pipeline changed logical wire identities/order or dropped declared bits.')
            after, actual_measurement_map, _ = split_body(output)
            # All auto-accepted measurement tests have distinct sources/destinations,
            # so reordering independent final measurements is harmless. Overwrites
            # and repeated measurements are separate decision probes.
            if sorted(measurement_map) != sorted(actual_measurement_map):
                result['actual_measurement_map'] = actual_measurement_map
                return finish('FAIL_MEASUREMENT_MAP', 'Terminal measurements were lost, added, or rewired.')
            result['measurement_handling_scope'] = 'user_pipeline_checked'
        else:
            after, diagnostic = call_normalizer(normalizer, body)
            result.update(diagnostic)
            result['measurement_handling_scope'] = 'scaffold_stripped; user restoration NOT tested'
    except ValueError as exc:
        return finish('UNSUPPORTED_LOWERING' if kind == 'feature_probe' else 'FAIL_NORMALIZE', f'{type(exc).__name__}: {exc}')
    except RecursionError as exc:
        return finish('FAIL_RECURSION', 'Unbounded lowering recursion: ' + str(exc))
    except Exception as exc:
        result['traceback'] = traceback.format_exc()
        return finish('ERROR_NORMALIZE', f'{type(exc).__name__}: {exc}')

    if not same_wires(frozen_reference, after):
        return finish('FAIL_WIRES', 'Normalizer changed logical bit identities/order or dropped idle wires.')
    result['output_operations'] = dict(after.count_ops())
    problems = check_basis(after)
    # Matrix comparison is also attempted when there are non-basis gates:
    # semantically correct but incomplete lowering is a different problem.
    try:
        equivalence = matrix_checks(frozen_reference, after, args, case.get('oracle'))
        result['equivalence'] = equivalence
    except Exception as exc:
        result['equivalence_error'] = f'{type(exc).__name__}: {exc}'
        if not problems:
            return finish('ERROR_EQUIVALENCE', result['equivalence_error'])
        equivalence = {'ok': None}
    if problems:
        result['basis_errors'] = problems
        return finish('FAIL_NOT_NORMALIZED', '; '.join(problems[:5]))
    if equivalence['ok'] is False:
        return finish('FAIL_EQUIVALENCE', equivalence['reason'])

    if normalizer is not None and not args.skip_repeat_checks:
        try:
            again, _ = call_normalizer(normalizer, after)
            fresh, _ = call_normalizer(normalizer, copy.deepcopy(frozen_reference))
            if circuit_to_dag(after) != circuit_to_dag(again):
                return finish('FAIL_NOT_IDEMPOTENT', 'A second normalization changes an already-normalized DAG.')
            if circuit_to_dag(after) != circuit_to_dag(fresh):
                return finish('FAIL_NOT_REPEATABLE', 'Fresh normalization gives a different DAG; check shared/cached state.')
        except Exception as exc:
            return finish('ERROR_REPEAT_CHECK', f'{type(exc).__name__}: {exc}')
    if equivalence['ok'] is None:
        return finish('STRUCTURE_ONLY', equivalence['reason'])
    if not equivalence['exact_equal']:
        return finish('PASS_UP_TO_GLOBAL_PHASE', 'Exact-phase preservation failed, but --phase physical permits it.')
    return finish('PASS', 'Basis, wires, and operator agree at every tested binding.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    hooks = parser.add_mutually_exclusive_group()
    hooks.add_argument('--normalizer', help='module:callable receiving DAGCircuit, e.g. norm:Norm')
    hooks.add_argument('--pipeline', help='module:callable receiving/returning QuantumCircuit including measurements')
    parser.add_argument('--validator', help='module:callable; reject with ValueError or False')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), help='Directory from which your project modules can be imported')
    parser.add_argument('--only', action='append', help='Case-ID glob; repeat to select multiple groups, e.g. 03_symbolic/*')
    parser.add_argument('--kinds', nargs='+', choices=['normalize','feature_probe','policy_probe','reject_policy','invalid_qasm'])
    parser.add_argument('--phase', choices=['exact','physical'], default='exact')
    parser.add_argument('--random-bindings', type=int, default=8, help='Additional independent seeded bindings; six fixed samples are always included')
    parser.add_argument('--max-qubits', type=int, default=6, help='Above this width, report matrix checks as not run')
    parser.add_argument('--atol', type=float, default=1e-9)
    parser.add_argument('--rtol', type=float, default=1e-9)
    parser.add_argument('--skip-repeat-checks', action='store_true')
    parser.add_argument('--report', type=Path, default=Path('results.json'))
    args = parser.parse_args()
    if args.random_bindings < 0 or args.max_qubits < 0 or args.atol < 0 or args.rtol < 0:
        parser.error('Counts and tolerances must be nonnegative.')

    # Lazy dependency loading keeps --help usable on a machine without Qiskit.
    global np, qasm3, QuantumCircuit, Gate, DAGCircuit
    global HGate, XGate, RZGate, CXGate, circuit_to_dag, dag_to_circuit, Operator
    try:
        import numpy as np
        from qiskit import qasm3, QuantumCircuit
        from qiskit.circuit import Gate
        from qiskit.circuit.library import HGate, XGate, RZGate, CXGate
        from qiskit.dagcircuit import DAGCircuit
        from qiskit.converters import circuit_to_dag, dag_to_circuit
        from qiskit.quantum_info import Operator
        import qiskit_qasm3_import  # Fail immediately rather than falsely passing negative tests.
    except ImportError as exc:
        print(f'Missing dependency: {exc}\nInstall into your test environment with:\n'
              '  python -m pip install -r requirements.txt', file=sys.stderr)
        return 2

    sys.path.insert(0, str(args.project_root.resolve()))
    try:
        normalizer = load_callable(args.normalizer)
        validator = load_callable(args.validator)
        pipeline = load_callable(args.pipeline)
    except Exception as exc:
        print(f'Cannot load project hook: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    cases = [c for c in manifest['cases']
             if (not args.only or any(fnmatch.fnmatchcase(c['id'], glob) for glob in args.only))
             and (not args.kinds or c['kind'] in args.kinds)]
    if not cases:
        parser.error('No cases match your filters.')
    versions = {}
    for package in ['qiskit', 'qiskit-qasm3-import', 'openqasm3', 'numpy']:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = 'unknown'
    print(json.dumps({'versions': versions, 'phase': args.phase, 'case_count': len(cases)}, indent=2))
    if normalizer is None and pipeline is None:
        print('\nIMPORT-ONLY MODE: this run cannot establish that normalization works.\n')
    elif normalizer is not None:
        print('\nUNITARY-BODY MODE: the scaffold strips measurements/barriers; your restoration code is NOT tested.\n')
    if validator is None:
        print('No validator connected: compiler-policy rejection tests will be marked NOT_TESTED_POLICY.\n')

    results = []
    for case in cases:
        result = run_case(case, args, normalizer, validator, pipeline)
        results.append(result)
        detail = result['detail'].replace('\n', ' ')
        print(f"{result['status']:31s} {case['id']}  {detail[:150]}")
    counts = Counter(r['status'] for r in results)
    report = {
        'mode': 'pipeline' if pipeline else ('unitary_body' if normalizer else 'import_only'),
        'versions': versions, 'phase_mode': args.phase,
        'atol': args.atol, 'rtol': args.rtol,
        'normalizer': args.normalizer, 'pipeline': args.pipeline, 'validator': args.validator,
        'counts': dict(counts), 'results': results,
        'limitations': [
            'Symbolic equivalence is sampled, not proved for all parameter values.',
            'Reference semantics are supplied by the selected Qiskit importer; the suite is not an independent certification of that importer.',
            'No state-initialization-only or probability-only checks substitute for full operator checks.',
            'No Qiskit transpile() or transpiler pass is called by this runner.',
            'Barrier scheduling/fence preservation is not tested by unitary comparison.',
            'Policy and importer blocks are distinct from normalizer failures.',
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('\nSummary:', json.dumps(dict(counts), indent=2))
    print(f'Report: {args.report.resolve()}')
    failures = sum(v for k, v in counts.items() if k.startswith(('FAIL_', 'ERROR_')))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
