#!/usr/bin/env python3
"""Independent NumPy checks, not an execution of the user's Norm or QASM importer.

Reproduces the saved norm_ry operation sequence, verifies a replacement sequence,
and demonstrates exact-vs-global-phase and controlled-phase pitfalls.
Run: python math_checks.py --report math_check_results.json
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
Z = np.diag([1, -1]).astype(complex)


def rz(theta: float) -> np.ndarray:
    return np.diag([np.exp(-0.5j * theta), np.exp(0.5j * theta)])


def rx(theta: float) -> np.ndarray:
    return np.cos(theta / 2) * I - 1j * np.sin(theta / 2) * X


def ry(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def phase_gate(theta: float) -> np.ndarray:
    return np.diag([1, np.exp(1j * theta)])


def sequence(*gates: np.ndarray) -> np.ndarray:
    """Arguments are in execution order: first argument acts first."""
    answer = np.eye(gates[0].shape[0], dtype=complex)
    for gate in gates:
        answer = gate @ answer
    return answer


def controlled(gate: np.ndarray) -> np.ndarray:
    """Qiskit-style little-endian matrix: control q0, target q1."""
    p0 = np.diag([1, 0])
    p1 = np.diag([0, 1])
    return np.kron(I, p0) + np.kron(gate, p1)


def physical_equal(a: np.ndarray, b: np.ndarray, atol: float = 1e-10) -> bool:
    inner = np.vdot(a, b)
    if abs(inner) < atol:
        return False
    factor = inner / abs(inner)
    return bool(np.allclose(b, factor * a, atol=atol, rtol=atol))


def saved_ry_sequence(theta: float) -> np.ndarray:
    # Transcribed from the previously shared norm.py lines 42--53.
    return sequence(rz(math.pi), H, rz(math.pi / 2), H,
                    rz(theta + math.pi), H, rz(math.pi / 2), H,
                    rz(theta), H)


def corrected_ry_sequence(theta: float) -> np.ndarray:
    return sequence(rz(-math.pi / 2), H, rz(theta), H, rz(math.pi / 2))


def run() -> dict:
    angles = [0.0, 1e-6, 0.4, math.pi / 7, -math.pi / 3,
              math.pi / 2, math.pi, 2 * math.pi, 4 * math.pi, 23 * math.pi / 7]
    rows = []
    for theta in angles:
        target = ry(theta)
        bad = saved_ry_sequence(theta)
        good = corrected_ry_sequence(theta)
        assert np.allclose(target, good, atol=1e-12, rtol=1e-12)
        assert np.allclose(rx(theta), sequence(H, rz(theta), H), atol=1e-12, rtol=1e-12)
        rows.append({
            'theta': theta,
            'saved_sequence_exact': bool(np.allclose(target, bad, atol=1e-12, rtol=1e-12)),
            'saved_sequence_equivalent_up_to_phase': physical_equal(target, bad),
            'saved_sequence_normalized_trace_overlap': float(abs(np.vdot(target, bad)) / 2),
            'corrected_sequence_max_error': float(np.max(abs(target - good))),
        })
    assert not physical_equal(ry(0), saved_ry_sequence(0))
    phase_rows = []
    for name, theta in [('z', math.pi), ('s', math.pi / 2), ('sdg', -math.pi / 2),
                        ('t', math.pi / 4), ('tdg', -math.pi / 4)]:
        target = phase_gate(theta)
        plain = rz(theta)
        corrected = np.exp(0.5j * theta) * plain
        assert physical_equal(target, plain)
        assert not np.allclose(target, plain, atol=1e-12, rtol=1e-12)
        assert np.allclose(target, corrected, atol=1e-12, rtol=1e-12)
        phase_rows.append({'gate': name, 'rz_angle': theta, 'required_global_phase': theta / 2,
                           'without_phase_exact': False, 'without_phase_physical': True})
    assert physical_equal(rz(2 * math.pi), I)
    assert not np.allclose(rz(2 * math.pi), I)
    assert np.allclose(rz(4 * math.pi), I)
    assert not physical_equal(controlled(phase_gate(math.pi / 3)), controlled(rz(math.pi / 3)))
    assert not physical_equal(controlled(rx(2 * math.pi)), np.eye(4))
    return {
        'scope': 'Independent matrix checks of formulas transcribed from saved source; not QASM/Qiskit execution.',
        'ry_tests': rows, 'phase_tests': phase_rows,
        'additional_assertions': {
            'rx_equals_h_rz_h': True,
            'rz_2pi_is_minus_identity': True,
            'rz_4pi_is_identity': True,
            'cp_and_crz_are_not_equivalent_in_general': True,
            'controlled_rx_2pi_is_not_identity': True,
        },
        'assertions_passed': True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = run()
    text = json.dumps(result, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
