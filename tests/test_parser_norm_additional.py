"""

Usage from your repository root:
    python -m pytest -v tests/test_parser_norm_additional.py
"""

import importlib.util
import random

import numpy as np
import pytest
import qiskit.qasm3
from qiskit import QuantumCircuit
from qiskit.circuit import (
    AncillaRegister, ClassicalRegister, Instruction, Parameter, QuantumRegister
)
from qiskit.circuit.library import CXGate
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator


from parser_0.parse_validate_qasm3 import parser_0
from normalization_1.norm import Norm

####
from test_parser_norm_basic import parse_circuit, assert_exact_operator, wire_names, operation_names, barrier_qubits


# Avoid conflating missing optional import dependencies with a parser bug.
requires_qasm3_importer = pytest.mark.skipif(
    importlib.util.find_spec("qiskit_qasm3_import") is None,
    reason="Install qiskit-qasm3-import to run OpenQASM 3 integration tests",
)
# ============================================================================
# ADDITIONAL TESTS: PARSER BOUNDARIES AND STATE INTEGRITY
# ============================================================================


def test_one_qubit_empty_program_is_valid(monkeypatch):
    qc = QuantumCircuit(1)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.num_qubits == 1
    assert operation_names(parsed.DAG_circuit) == []
    assert parsed.final_measure_map == {}


def test_three_qubits_without_operations_is_valid(monkeypatch):
    qc = QuantumCircuit(3)
    parsed = parse_circuit(monkeypatch, qc)
    assert len(parsed.DAG_circuit.qubits) == 3
    assert parsed.final_measure_map == {}


def test_zero_qubits_is_rejected(monkeypatch):
    qc = QuantumCircuit()  # valid zero-qubit Qiskit circuit
    with pytest.raises(ValueError, match="qubits"):
        parse_circuit(monkeypatch, qc)


def test_three_qubits_at_maximum_are_accepted(monkeypatch):
    qc = QuantumCircuit(3)
    qc.cx(2, 0)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.num_qubits == 3
    assert operation_names(parsed.DAG_circuit) == ["cx"]


def test_many_unused_classical_bits_are_allowed(monkeypatch):
    # max_qubits is a *qubit* limit, not a clbit/register limit.
    qc = QuantumCircuit(1, 6)
    qc.measure(0, 5)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 5}
    assert len(parsed.DAG_circuit.clbits) == 6


def test_parser_does_not_remove_measurements_from_original_circuit(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.measure(0, 1)
    qc.measure(1, 0)
    before_names = [inst.operation.name for inst in qc.data]

    parsed = parse_circuit(monkeypatch, qc)
    assert [inst.operation.name for inst in qc.data] == before_names
    assert [inst.operation.name for inst in parsed.circuit.data] == before_names
    assert operation_names(parsed.DAG_circuit) == ["h"]


def test_parser_keeps_original_global_phase(monkeypatch):
    qc = QuantumCircuit(2)
    qc.global_phase = 0.317
    qc.ry(0.42, 1)
    parsed = parse_circuit(monkeypatch, qc)
    assert np.isclose(float(parsed.DAG_circuit.global_phase), 0.317)
    assert_exact_operator(qc, dag_to_circuit(parsed.DAG_circuit))


def test_noncontiguous_logical_qubits_map_to_classical_bits(monkeypatch):
    qc = QuantumCircuit(3, 5)
    qc.measure(2, 4)
    qc.measure(0, 1)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {2: 4, 0: 1}


def test_measurements_across_multiple_registers_use_flat_bit_indices(monkeypatch):
    qa = QuantumRegister(1, "qa")
    qb = QuantumRegister(2, "qb")
    ca = ClassicalRegister(2, "ca")
    cb = ClassicalRegister(2, "cb")
    qc = QuantumCircuit(qa, qb, ca, cb)
    qc.h(qb[1])
    qc.measure(qb[1], cb[0])  # flattened q2 -> flattened c2
    qc.measure(qa[0], ca[1])  # flattened q0 -> flattened c1
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {2: 2, 0: 1}
    assert operation_names(parsed.DAG_circuit) == ["h"]


def test_measure_all_is_accepted_and_preserves_its_barrier(monkeypatch):
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.measure_all()  # Qiskit inserts a full-width barrier by default.
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0, 1: 1, 2: 2}
    assert barrier_qubits(parsed.DAG_circuit) == [(0, 1, 2)]
    assert "measure" not in operation_names(parsed.DAG_circuit)


def test_repeated_measurements_three_times_still_produce_one_mapping(monkeypatch):
    qc = QuantumCircuit(1, 1)
    for _ in range(3):
        qc.measure(0, 0)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert operation_names(parsed.DAG_circuit) == []


def test_repeated_measurements_of_one_qubit_mixed_with_another(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.measure(0, 1)
    qc.measure(1, 0)
    qc.measure(0, 1)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 1, 1: 0}


def test_barrier_only_circuit_is_preserved(monkeypatch):
    qc = QuantumCircuit(3)
    qc.barrier(2)
    qc.barrier(0, 1)
    parsed = parse_circuit(monkeypatch, qc)
    barriers = barrier_qubits(parsed.DAG_circuit)
    assert len(barriers) == 2
    assert set(barriers) == {(2,), (0, 1)}
    assert parsed.final_measure_map == {}


def test_measurement_then_barrier_on_different_qubit_is_final(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.barrier(1)
    qc.h(1)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert wire_names(parsed.DAG_circuit, 1) == ["barrier", "h"]


def test_partial_barrier_following_a_measurement_on_same_qubit_is_final(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.barrier(0)
    qc.h(1)  # this should not prevent q0's measurement from being final
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert barrier_qubits(parsed.DAG_circuit) == [(0,)]


def test_measurement_followed_by_shared_barrier_and_nonfinal_gate_is_rejected(monkeypatch):
    # Conservative policy of calc_final_ops: a shared barrier that is not
    # terminal on ALL its qubits prevents extracting the preceding measure.
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.barrier(0, 1)
    qc.h(1)
    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_circuit(monkeypatch, qc)


def test_measurement_after_terminal_barrier_is_final(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.h(0)
    qc.barrier(0, 1)
    qc.measure(0, 0)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert barrier_qubits(parsed.DAG_circuit) == [(0, 1)]


def test_measurement_followed_by_rotation_on_other_qubit_is_final(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.h(0)
    qc.measure(0, 0)
    qc.ry(0.8, 1)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert set(operation_names(parsed.DAG_circuit)) == {"h", "ry"}


def test_measurement_after_other_qubit_gates_remains_final(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.h(1)
    qc.cx(1, 0)
    qc.measure(0, 0)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert operation_names(parsed.DAG_circuit) == ["h", "cx"]


def test_measurement_followed_by_entangling_gate_with_measured_target_is_rejected(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.cx(1, 0)  # measured qubit is the target
    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_circuit(monkeypatch, qc)


def test_measurement_followed_by_measurement_then_gate_is_rejected(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.measure(0, 0)
    qc.measure(1, 1)
    qc.h(0)
    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_circuit(monkeypatch, qc)


@pytest.mark.parametrize("duration, unit", [(0, "dt"), (1, "dt"), (100, "dt"), (10, "ns")])
def test_delays_are_rejected_regardless_of_duration(monkeypatch, duration, unit):
    qc = QuantumCircuit(1)
    qc.delay(duration, 0, unit=unit)
    with pytest.raises(ValueError, match="delay"):
        parse_circuit(monkeypatch, qc)


def test_reset_after_normal_gate_is_rejected(monkeypatch):
    qc = QuantumCircuit(1)
    qc.h(0)
    qc.reset(0)
    with pytest.raises(ValueError, match="reset"):
        parse_circuit(monkeypatch, qc)


def test_control_flow_is_rejected_even_with_no_measurements(monkeypatch):
    qc = QuantumCircuit(1)
    with qc.for_loop(range(2)):
        qc.h(0)
    with pytest.raises(ValueError, match="control flow"):
        parse_circuit(monkeypatch, qc)


def test_while_loop_control_flow_is_rejected(monkeypatch):
    qc = QuantumCircuit(1, 1)
    with qc.while_loop((qc.clbits[0], 1)):
        qc.x(0)
    with pytest.raises(ValueError, match="control flow"):
        parse_circuit(monkeypatch, qc)


def test_normal_classical_register_bits_are_not_counted_as_variables(monkeypatch):
    # num_vars != num_clbits. Ordinary measurement storage is supported.
    qc = QuantumCircuit(2, 3)
    qc.measure(1, 2)
    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {1: 2}


# ============================================================================
# ADDITIONAL TESTS: NORMALIZER MATHEMATICS AND GLOBAL PHASE
# ============================================================================


@pytest.mark.parametrize("name, add_gate", [
    ("z", lambda qc: qc.z(1)),
    ("s", lambda qc: qc.s(1)),
    ("sdg", lambda qc: qc.sdg(1)),
    ("t", lambda qc: qc.t(1)),
    ("tdg", lambda qc: qc.tdg(1)),
    ("u", lambda qc: qc.u(0.67, -0.48, 1.21, 1)),
    ("rx", lambda qc: qc.rx(0.23, 1)),
    ("ry", lambda qc: qc.ry(-0.7, 1)),
    ("open_cx", lambda qc: qc.append(CXGate(ctrl_state=0), [1, 0])),
])
def test_normalizer_preserves_exact_unitary_including_global_phase(name, add_gate):
    # Operator.equiv used in the original tests is NOT enough for this test.
    qc = QuantumCircuit(2)
    qc.global_phase = 0.123
    qc.h(1)
    add_gate(qc)
    qc.cx(1, 0)
    result = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert set(inst.operation.name for inst in result.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    assert_exact_operator(qc, result)


@pytest.mark.parametrize("angle", [0.0, np.pi / 2, -np.pi, 2 * np.pi, -2.6, 13.9])
@pytest.mark.parametrize("gate", ["rx", "ry", "rz"])
def test_rotation_normalization_across_edge_case_angles(angle, gate):
    qc = QuantumCircuit(2)
    qc.h(0)
    getattr(qc, gate)(angle, 0)
    qc.cx(0, 1)
    result = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert_exact_operator(qc, result)


@pytest.mark.parametrize("angles", [
    (0.0, 0.0, 0.0),
    (np.pi / 2, np.pi, -np.pi),
    (-0.62, 2.31, -1.1),
    (2 * np.pi, -np.pi / 3, np.pi / 7),
])
def test_u_gate_edge_cases_including_phase(angles):
    qc = QuantumCircuit(1)
    qc.u(*angles, 0)
    result = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert_exact_operator(qc, result)


def test_sum_of_multiple_global_phase_contributions_is_preserved():
    qc = QuantumCircuit(2)
    qc.global_phase = np.pi / 8
    qc.z(0)
    qc.t(1)
    qc.sdg(0)
    qc.u(0.3, 0.4, 0.5, 1)
    qc.tdg(0)
    result = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert_exact_operator(qc, result)


def test_symbolic_parameters_survive_normalization_and_bind_correctly():
    theta = Parameter("theta")
    phi = Parameter("phi")
    qc = QuantumCircuit(3)
    qc.global_phase = phi / 9
    qc.rx(theta, 0)
    qc.ry(2 * theta - phi, 2)
    qc.u(theta / 2, phi, -theta, 1)
    qc.cx(2, 0)
    normalized = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)

    assert {p.name for p in normalized.parameters} == {"theta", "phi"}
    assert set(inst.operation.name for inst in normalized.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    for theta_val, phi_val in [(0.0, 0.0), (0.3, 0.8), (-1.2, 2.3)]:
        parameters = {theta: theta_val, phi: phi_val}
        assert_exact_operator(
            qc.assign_parameters(parameters),
            normalized.assign_parameters(parameters),
        )


def test_reusing_one_symbolic_parameter_in_multiple_gates():
    theta = Parameter("theta")
    qc = QuantumCircuit(2)
    qc.ry(theta, 1)
    qc.rx(-theta, 0)
    qc.u(theta, theta / 2, -theta, 1)
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert {p.name for p in out.parameters} == {"theta"}
    for val in [-0.3, 0, 1.6]:
        assert_exact_operator(qc.assign_parameters({theta: val}),
                              out.assign_parameters({theta: val}))


def test_parameterized_nested_custom_gate_binds_correctly():
    angle = Parameter("angle")
    inner = QuantumCircuit(2, name="parameterized_custom")
    inner.ry(angle, 0)
    inner.cx(0, 1)
    inner.u(angle / 2, -angle, angle + 0.1, 1)
    inner_gate = inner.to_gate()

    qc = QuantumCircuit(3)
    qc.append(inner_gate, [2, 0])
    qc.h(1)
    normalized = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)

    assert {p.name for p in normalized.parameters} == {"angle"}
    assert set(inst.operation.name for inst in normalized.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    for val in [0.0, -0.75, 1.94]:
        binding = {angle: val}
        assert_exact_operator(qc.assign_parameters(binding),
                              normalized.assign_parameters(binding))


# ============================================================================
# ADDITIONAL TESTS: RECURSION, TARGET WIRES, AND NORMALIZER INVARIANTS
# ============================================================================


@pytest.mark.parametrize("name, add_gate, qubits", [
    ("y", lambda qc: qc.y(0), 1),
    ("sx", lambda qc: qc.sx(0), 1),
    ("sxdg", lambda qc: qc.sxdg(0), 1),
    ("phase", lambda qc: qc.p(0.31, 0), 1),
    ("cz", lambda qc: qc.cz(0, 1), 2),
    ("swap", lambda qc: qc.swap(0, 1), 2),
    ("cp", lambda qc: qc.cp(0.42, 0, 1), 2),
    ("crz", lambda qc: qc.crz(-0.7, 0, 1), 2),
    ("ccx", lambda qc: qc.ccx(0, 1, 2), 3),
])
def test_standard_composite_gates_recursively_reach_internal_basis(
    name, add_gate, qubits
):
    # These rely on the documented *definition fallback*, not on
    # KNOWN_NORM entries. CCX tests deep recursive decomposition.
    qc = QuantumCircuit(qubits)
    qc.h(0)
    add_gate(qc)
    qc.x(qubits - 1)
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert set(inst.operation.name for inst in out.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    assert_exact_operator(qc, out)


def test_nested_user_defined_gate_requires_multiple_recursion_passes():
    inner = QuantumCircuit(1, name="inner")
    inner.ry(0.6, 0)
    inner.t(0)
    inner_gate = inner.to_gate()

    outer = QuantumCircuit(2, name="outer")
    outer.append(inner_gate, [1])
    outer.cx(1, 0)
    outer.append(inner_gate.inverse(), [0])
    outer_gate = outer.to_gate()

    qc = QuantumCircuit(3)
    qc.h(2)
    qc.append(outer_gate, [2, 0])  # deliberately not (0, 1)
    qc.cx(2, 1)

    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert set(inst.operation.name for inst in out.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    assert_exact_operator(qc, out)


def test_custom_gate_definition_global_phase_is_not_dropped():
    inner = QuantumCircuit(1, name="with_phase")
    inner.global_phase = np.pi / 7
    inner.z(0)
    inner.ry(0.42, 0)

    qc = QuantumCircuit(2)
    qc.global_phase = -np.pi / 11
    qc.append(inner.to_gate(), [1])
    qc.cx(1, 0)
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert_exact_operator(qc, out)


def test_swap_on_non_adjacent_qubits_keeps_correct_wire_mapping():
    # Two operands of a substituted gate aren't necessarily q0/q1.
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.ry(0.21, 2)
    qc.swap(2, 0)
    qc.cx(2, 1)
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert_exact_operator(qc, out)


def test_reversed_cx_control_target_not_accidentally_swapped():
    qc = QuantumCircuit(3)
    qc.h(2)
    qc.cx(2, 0)
    qc.ry(0.31, 0)
    qc.cx(0, 2)
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert_exact_operator(qc, out)
    cx_qubits = [
        tuple(out.find_bit(q).index for q in inst.qubits)
        for inst in out.data if inst.operation.name == "cx"
    ]
    assert cx_qubits == [(2, 0), (0, 2)]


def test_normalization_across_quantum_register_boundaries():
    r0 = QuantumRegister(1, "left")
    r1 = QuantumRegister(2, "right")
    qc = QuantumCircuit(r0, r1)
    qc.h(r1[1])
    qc.cz(r1[1], r0[0])
    qc.swap(r0[0], r1[0])
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert out.num_qubits == 3
    assert [reg.name for reg in out.qregs] == ["left", "right"]
    assert_exact_operator(qc, out)


def test_normalizer_preserves_number_of_qubits_including_idle_qubits():
    qc = QuantumCircuit(3)
    qc.ry(0.19, 0)  # q1 and q2 remain idle
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert out.num_qubits == 3
    assert_exact_operator(qc, out)


def test_normalizer_handles_empty_dag():
    qc = QuantumCircuit(2)
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert out.num_qubits == 2
    assert len(out.data) == 0
    assert_exact_operator(qc, out)


def test_normalizer_preserves_internal_gates_without_rewriting_them():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.rz(0.4, 1)
    qc.x(2)
    qc.cx(2, 0)
    before = [inst.operation.name for inst in qc.data]
    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert [inst.operation.name for inst in out.data] == before
    assert_exact_operator(qc, out)


def test_normalizing_twice_is_idempotent():
    qc = QuantumCircuit(2)
    qc.global_phase = 0.13
    qc.ry(0.4, 0)
    qc.cz(1, 0)
    qc.t(1)
    first = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    second = dag_to_circuit(Norm(circuit_to_dag(first)).normalized_dag)
    assert [inst.operation.name for inst in first.data] == [
        inst.operation.name for inst in second.data
    ]
    assert np.isclose(float(first.global_phase), float(second.global_phase))
    assert_exact_operator(first, second)
    assert_exact_operator(qc, second)


def test_orig_dag_keeps_pre_normalized_instructions():
    qc = QuantumCircuit(1)
    qc.ry(0.58, 0)
    norm = Norm(circuit_to_dag(qc))
    assert operation_names(norm.orig_dag) == ["ry"]
    assert "ry" not in operation_names(norm.normalized_dag)
    assert_exact_operator(dag_to_circuit(norm.orig_dag),
                          dag_to_circuit(norm.normalized_dag))


def test_normalization_preserves_partial_barriers_and_wire_order():
    qc = QuantumCircuit(2)
    qc.rx(0.3, 0)
    qc.barrier(0)
    qc.ry(-0.4, 0)
    qc.rx(0.2, 1)
    out = Norm(circuit_to_dag(qc)).normalized_dag
    assert barrier_qubits(out) == [(0,)]
    assert wire_names(out, 0) == [
        "h", "rz", "h", "barrier", "rz", "h", "rz", "h", "rz"
    ]
    assert_exact_operator(qc, dag_to_circuit(out))


def test_multiple_barriers_stay_separate_and_ordered_on_shared_wire():
    qc = QuantumCircuit(2)
    qc.barrier(0)
    qc.ry(0.31, 0)
    qc.barrier(0, 1)
    qc.z(1)
    qc.barrier(0)
    out = Norm(circuit_to_dag(qc)).normalized_dag
    assert barrier_qubits(out) == [(0,), (0, 1), (0,)]
    assert wire_names(out, 0).count("barrier") == 3


def test_normalizer_rejects_unknown_instruction_without_definition():
    qc = QuantumCircuit(1)
    qc.append(Instruction("opaque_unrecognized", 1, 0, []), [0])
    with pytest.raises(ValueError, match="Does not support"):
        Norm(circuit_to_dag(qc))


@pytest.mark.parametrize("invalid_operation", ["delay", "reset", "measure"])
def test_normalizer_rejects_standalone_nonunitary_instruction(invalid_operation):
    qc = QuantumCircuit(1, 1)
    if invalid_operation == "delay":
        qc.delay(25, 0, unit="dt")
    elif invalid_operation == "reset":
        qc.reset(0)
    else:
        qc.measure(0, 0)
    with pytest.raises(ValueError, match="Does not support"):
        Norm(circuit_to_dag(qc))


# ============================================================================
# ADDITIONAL TESTS: DETERMINISTIC MIXED-CIRCUIT REGRESSIONS
# ============================================================================


@pytest.mark.parametrize("seed", list(range(12)))
def test_seeded_mixed_circuits_preserve_exact_unitary(seed):
    """Catches interactions the single-gate tests cannot anticipate.

    12 deterministic 3-qubit, 18-operation circuits. Every failing seed is
    reproducible, and no simulator backend is required (8x8 matrices only).
    """
    rng = random.Random(seed)
    qc = QuantumCircuit(3)
    qc.global_phase = rng.uniform(-np.pi, np.pi)
    pool = (
        "h", "x", "rz", "rx", "ry", "u", "s", "sdg", "t", "tdg",
        "cx", "open_cx", "cz", "swap", "ccx", "barrier"
    )

    for _ in range(18):
        gate = rng.choice(pool)
        q = rng.randrange(3)
        angle = rng.uniform(-3.1, 3.1)
        if gate in {"h", "x", "s", "sdg", "t", "tdg"}:
            getattr(qc, gate)(q)
        elif gate in {"rz", "rx", "ry"}:
            getattr(qc, gate)(angle, q)
        elif gate == "u":
            qc.u(angle, rng.uniform(-2, 2), rng.uniform(-2, 2), q)
        elif gate in {"cx", "open_cx", "cz", "swap"}:
            a, b = rng.sample(range(3), 2)
            if gate == "open_cx":
                qc.append(CXGate(ctrl_state=0), [a, b])
            else:
                getattr(qc, gate)(a, b)
        elif gate == "ccx":
            a, b, target = rng.sample(range(3), 3)
            qc.ccx(a, b, target)
        else:
            # Random partial/full barriers, preserved throughout normalization.
            affected = rng.sample(range(3), rng.randrange(1, 4))
            qc.barrier(*affected)

    out = dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)
    assert out.num_qubits == 3
    assert set(inst.operation.name for inst in out.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    assert_exact_operator(qc, out)


# ============================================================================
# ADDITIONAL TESTS: REAL OPENQASM 3 INTEGRATION
# ============================================================================


def write_qasm(tmp_path, body, *, n_qubits=2, n_bits=2, filename="test.qasm"):
    text = (
        'OPENQASM 3.0;\ninclude "stdgates.inc";\n'
        f'qubit[{n_qubits}] q;\nbit[{n_bits}] c;\n'
        f'{body}\n'
    )
    path = tmp_path / filename
    path.write_text(text, encoding="utf-8")
    return path


@requires_qasm3_importer
@pytest.mark.parametrize("unsupported_line, error_fragment", [
    ("reset q[0];", "reset"),
    ("delay[100ns] q[0];", "delay"),
])
def test_real_qasm3_unsupported_nonunitary_operations_are_rejected(
    tmp_path, unsupported_line, error_fragment
):
    path = write_qasm(tmp_path, unsupported_line)
    with pytest.raises(ValueError, match=error_fragment):
        parser_0(str(path))


@requires_qasm3_importer
def test_real_qasm3_gate_normalization_with_parameters_as_literals(tmp_path):
    path = write_qasm(
        tmp_path,
        "rx(pi/3) q[0]; ry(-pi/4) q[1]; U(0.3, 0.7, -0.2) q[0]; "
        "cx q[1], q[0]; c[0] = measure q[1]; c[1] = measure q[0];"
    )
    parsed = parser_0(str(path))
    assert parsed.final_measure_map == {1: 0, 0: 1}
    original_unitary = dag_to_circuit(parsed.DAG_circuit)
    normalized_unitary = dag_to_circuit(Norm(parsed.DAG_circuit).normalized_dag)
    assert set(inst.operation.name for inst in normalized_unitary.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    assert_exact_operator(original_unitary, normalized_unitary)


@requires_qasm3_importer
def test_real_qasm3_symbolic_input_survives_to_normalizer(tmp_path):
    qasm = (
        'OPENQASM 3.0;\ninclude "stdgates.inc";\n'
        'input float[64] theta;\nqubit[2] q;\n'
        'ry(theta) q[0]; cx q[0], q[1];\n'
    )
    path = tmp_path / "symbolic.qasm"
    path.write_text(qasm, encoding="utf-8")

    parsed = parser_0(str(path))
    original = dag_to_circuit(parsed.DAG_circuit)
    normalized = dag_to_circuit(Norm(parsed.DAG_circuit).normalized_dag)
    assert {p.name for p in original.parameters} == {"theta"}
    assert {p.name for p in normalized.parameters} == {"theta"}
    for value in [0.0, 0.5, -1.8]:
        assert_exact_operator(
            original.assign_parameters({"theta": value}),
            normalized.assign_parameters({"theta": value}),
        )


@requires_qasm3_importer
def test_real_qasm3_three_qubit_custom_gate_definition(tmp_path):
    # Important integration test: parser retains a definition that Norm
    # subsequently expands, rather than relying on a full transpile().
    path = write_qasm(tmp_path, """
gate my_gate(a) x, y { ry(a) x; cx x, y; }
my_gate(pi/3) q[2], q[0];
c[1] = measure q[2];
""", n_qubits=3)
    parsed = parser_0(str(path))
    assert parsed.final_measure_map == {2: 1}
    original = dag_to_circuit(parsed.DAG_circuit)
    actual = dag_to_circuit(Norm(parsed.DAG_circuit).normalized_dag)
    assert_exact_operator(original, actual)
    assert set(inst.operation.name for inst in actual.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }


@requires_qasm3_importer
def test_real_qasm3_three_qubits_accepted_four_rejected(tmp_path):
    path_ok = write_qasm(tmp_path, "h q[2];", n_qubits=3, filename="three.qasm")
    assert parser_0(str(path_ok)).num_qubits == 3
    path_bad = write_qasm(tmp_path, "h q[3];", n_qubits=4, filename="four.qasm")
    with pytest.raises(ValueError, match="3 qubits"):
        parser_0(str(path_bad))


@requires_qasm3_importer
def test_real_qasm3_partial_barrier_not_expanded_to_full_width(tmp_path):
    path = write_qasm(tmp_path, "h q[0]; barrier q[1]; ry(0.4) q[0];")
    parsed = parser_0(str(path))
    assert barrier_qubits(parsed.DAG_circuit) == [(1,)]
    out = Norm(parsed.DAG_circuit).normalized_dag
    assert barrier_qubits(out) == [(1,)]


@requires_qasm3_importer
@pytest.mark.parametrize("invalid_body", [
    "h q[9];",               # out-of-range operand
    "mystery_gate q[0];",    # unknown gate
    "cx q[0], ;",           # malformed syntax
])
def test_real_qasm3_import_errors_are_wrapped(tmp_path, invalid_body):
    path = write_qasm(tmp_path, invalid_body)
    with pytest.raises(ValueError, match="Initial load into qiskit failed"):
        parser_0(str(path))


@requires_qasm3_importer
def test_real_qasm3_file_not_found_is_wrapped(tmp_path):
    missing = tmp_path / "does_not_exist.qasm"
    with pytest.raises(ValueError, match="Initial load into qiskit failed"):
        parser_0(str(missing))


# ============================================================================
# KNOWN GAPS / NEXT DESIGN DECISIONS: EXPECTED FAILURES (XFAIL)
# ============================================================================
# Your current parser checks only top-level circuit.data operations. If a
# composite Instruction has a *definition* containing a forbidden operation,
# the parser accepts it. These cases SHOULD fail validation under a strict
# "no delays, resets, hidden measurements" policy; they xfail until fixed.


# @pytest.mark.xfail(strict=True, reason="Parser does not recursively check instruction definitions")
@pytest.mark.parametrize("unsupported", ["delay", "reset"])
def test_parser_rejects_unsupported_instruction_hidden_in_definition(monkeypatch, unsupported):
    inner = QuantumCircuit(1, name="hidden_" + unsupported)
    if unsupported == "delay":
        inner.delay(50, 0, unit="dt")
    else:
        inner.reset(0)
    outer = QuantumCircuit(1)
    outer.append(inner.to_instruction(), [0])
    with pytest.raises(ValueError, match=unsupported):
        parse_circuit(monkeypatch, outer)


# @pytest.mark.xfail(strict=True, reason="Parser does not inspect measurement operations inside instruction definitions")
def test_parser_rejects_measurement_hidden_in_definition(monkeypatch):
    inner = QuantumCircuit(1, 1, name="hidden_measurement")
    inner.measure(0, 0)
    outer = QuantumCircuit(1, 1)
    outer.append(inner.to_instruction(), [0], [0])
    with pytest.raises(ValueError, match="measurement"):
        parse_circuit(monkeypatch, outer)