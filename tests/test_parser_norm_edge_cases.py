"""Focused specification tests for quantum-compiler parser_0 and Norm.

Install as: tests/test_parser_norm_edge_cases.py
Run:        python -m pytest tests/test_parser_norm_edge_cases.py -vv

These are STRICT tests of the supported-front-end contract.  There are no
xfail/skip markers: if a required behaviour is missing, the test must FAIL.

Assumptions (matching the agreed compiler design):
* Parser accepts 1..3 qubits, no ancillas, terminal measurements only.
* Identical terminal measurements collapse into one logical->classical entry.
* Distinct qubits may not write to one classical bit; one qubit may not write
  to several classical bits.  Barriers are preserved.
* Reset, delay, classical control/variables, and non-final or nested
  measurements are forbidden, even inside custom instruction definitions.
* Norm emits H, X, RZ, ordinary CX; barriers stay as non-unitary directives.
* Every supported rewrite preserves the *exact* unitary (including phase),
  logical wire identities and register structure, and free symbolic parameters.

Modify the two project imports below if your modules live in a package.
"""

import math

import numpy as np
import pytest
import qiskit.qasm3
from qiskit import QuantumCircuit
from qiskit.circuit import ClassicalRegister, Instruction, Parameter, QuantumRegister
from qiskit.circuit.library import CXGate
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator

from parser_0.parse_validate_qasm3 import parser_0
from normalization_1.norm import Norm

INTERNAL_NAMES = {"h", "x", "rz", "cx"}
DIRECTIVE_NAMES = {"barrier"}


def parse_qc(monkeypatch, qc):
    """Test parser policies without relying on OpenQASM3 serialization."""
    monkeypatch.setattr(qiskit.qasm3, "load", lambda unused_path: qc)
    return parser_0("in-memory.qasm")


def normalize(qc):
    return dag_to_circuit(Norm(circuit_to_dag(qc)).normalized_dag)


def assert_exact_operator(expected, actual, *, atol=1e-10):
    """Compare complex matrices; unlike .equiv(), global phase matters."""
    np.testing.assert_allclose(
        Operator(actual).data,
        Operator(expected).data,
        atol=atol,
        rtol=1e-10,
        err_msg="Normalization changed the operator, possibly its global phase",
    )


def assert_same_phase_mod_2pi(actual, expected):
    # Qiskit may canonicalize angles modulo 2*pi.
    np.testing.assert_allclose(
        np.exp(1j * float(actual)),
        np.exp(1j * float(expected)),
        atol=1e-10,
        rtol=0,
    )


def op_names(dag):
    return [node.op.name for node in dag.topological_op_nodes()]


def circuit_op_names(qc):
    return [instruction.operation.name for instruction in qc.data]


def barrier_operands(dag):
    return [
        tuple(dag.find_bit(q).index for q in node.qargs)
        for node in dag.topological_op_nodes()
        if node.op.name == "barrier"
    ]


def wire_ops(dag, index):
    qubit = dag.qubits[index]
    return [
        node.op.name for node in dag.topological_op_nodes()
        if qubit in node.qargs
    ]


def cx_operands(qc):
    return [
        tuple(qc.find_bit(q).index for q in item.qubits)
        for item in qc.data
        if item.operation.name == "cx"
    ]


def assert_internal_basis(qc):
    for item in qc.data:
        op = item.operation
        assert op.name in INTERNAL_NAMES | DIRECTIVE_NAMES, (
            f"Unexpected normalized operation: {op.name}"
        )
        if isinstance(op, CXGate):
            assert op.ctrl_state == 1, "An open-control CX survived normalization"


def assert_preserved_registers(expected, actual):
    assert expected.num_qubits == actual.num_qubits
    assert expected.num_clbits == actual.num_clbits
    assert [(r.name, r.size) for r in expected.qregs] == [
        (r.name, r.size) for r in actual.qregs
    ]
    assert [(r.name, r.size) for r in expected.cregs] == [
        (r.name, r.size) for r in actual.cregs
    ]


# ==========================================================================
# 1. EXACT UNITARY / GLOBAL PHASE
# ==========================================================================


def test_matrix_comparison_detects_phase_error_that_equiv_misses():
    reference = QuantumCircuit(1)
    wrong = QuantumCircuit(1)
    wrong.global_phase = math.pi / 3
    assert Operator(reference).equiv(Operator(wrong))
    with pytest.raises(AssertionError):
        assert_exact_operator(reference, wrong)


@pytest.mark.parametrize(
    "gate_name, apply_gate",
    [
        ("z", lambda qc: qc.z(1)),
        ("s", lambda qc: qc.s(1)),
        ("sdg", lambda qc: qc.sdg(1)),
        ("t", lambda qc: qc.t(1)),
        ("tdg", lambda qc: qc.tdg(1)),
        ("rx", lambda qc: qc.rx(-0.43, 1)),
        ("ry", lambda qc: qc.ry(0.71, 1)),
        ("u", lambda qc: qc.u(0.29, 0.83, -0.51, 1)),
        ("open_cx", lambda qc: qc.append(CXGate(ctrl_state=0), [1, 0])),
    ],
)
def test_exact_global_phase_for_each_decomposition(gate_name, apply_gate):
    qc = QuantumCircuit(2)
    qc.global_phase = 0.31
    qc.h(0)
    apply_gate(qc)
    qc.cx(1, 0)

    out = normalize(qc)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


@pytest.mark.parametrize(
    "angles",
    [(0.0, 0.0, 0.0), (0.39, -0.92, 1.41),
     (-math.pi, math.pi / 2, -2.0), (2 * math.pi, -math.pi, math.pi)],
)
def test_u_gate_exact_phase_at_varied_angles(angles):
    qc = QuantumCircuit(1)
    qc.u(*angles, 0)
    assert_exact_operator(qc, normalize(qc))


def test_phase_contributions_from_several_gates_accumulate():
    qc = QuantumCircuit(2)
    qc.global_phase = 0.19
    qc.z(0)                 # +pi/2
    qc.s(1)                 # +pi/4
    qc.t(0)                 # +pi/8
    qc.u(0.2, 0.8, -0.3, 1)  # +(phi + lambda)/2
    qc.sdg(0)               # -pi/4
    expected_phase = 0.19 + math.pi / 2 + math.pi / 4 + math.pi / 8 + 0.25 - math.pi / 4

    out = normalize(qc)
    assert_same_phase_mod_2pi(out.global_phase, expected_phase)
    assert_exact_operator(qc, out)


@pytest.mark.parametrize("angle", [0, -math.pi, math.pi, 2 * math.pi, -2 * math.pi, 9.3])
def test_rx_ry_periodic_edge_angles_preserve_exact_operator(angle):
    qc = QuantumCircuit(2)
    qc.rx(angle, 0)
    qc.ry(angle, 1)
    assert_exact_operator(qc, normalize(qc))


# ==========================================================================
# 2. RECURSIVE DECOMPOSITION
# ==========================================================================


@pytest.mark.parametrize(
    "operation",
    ["swap", "ccx", "cz", "y", "sx", "p", "cp", "crz"],
)
def test_qiskit_defined_gates_recursively_reduce_to_internal_basis(operation):
    qc = QuantumCircuit(3)
    qc.h(2)
    if operation == "swap":
        qc.swap(2, 0)
    elif operation == "ccx":
        qc.ccx(2, 0, 1)
    elif operation == "cz":
        qc.cz(2, 0)
    elif operation == "y":
        qc.y(0)
    elif operation == "sx":
        qc.sx(2)
    elif operation == "p":
        qc.p(-0.72, 2)
    elif operation == "cp":
        qc.cp(0.29, 2, 0)
    elif operation == "crz":
        qc.crz(-0.35, 0, 2)
    qc.cx(2, 1)

    out = normalize(qc)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_nested_user_gates_require_multiple_expansion_passes():
    leaf = QuantumCircuit(1, name="leaf")
    leaf.ry(0.47, 0)
    leaf.t(0)

    middle = QuantumCircuit(2, name="middle")
    middle.append(leaf.to_gate(), [1])
    middle.swap(1, 0)

    outer = QuantumCircuit(2, name="outer")
    outer.append(middle.to_gate(), [0, 1])
    outer.u(0.31, -0.2, 0.87, 1)

    qc = QuantumCircuit(3)
    qc.append(outer.to_gate(), [2, 0])  # nonconsecutive, reversed wire order
    qc.cx(2, 1)

    out = normalize(qc)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_reused_multi_layer_custom_gate_normalizes_every_occurrence():
    leaf = QuantumCircuit(1, name="spin")
    leaf.rx(0.61, 0)
    leaf.z(0)

    qc = QuantumCircuit(3)
    gate = leaf.to_gate()
    qc.append(gate, [2])
    qc.append(gate.inverse(), [0])
    qc.append(gate, [1])

    out = normalize(qc)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_nested_gate_definition_global_phase_is_retained():
    leaf = QuantumCircuit(1, name="phase_leaf")
    leaf.global_phase = math.pi / 11
    leaf.ry(0.48, 0)

    middle = QuantumCircuit(1, name="phase_middle")
    middle.global_phase = -math.pi / 13
    middle.append(leaf.to_gate(), [0])
    middle.z(0)

    qc = QuantumCircuit(2)
    qc.global_phase = math.pi / 17
    qc.append(middle.to_gate(), [1])
    out = normalize(qc)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_unsupported_opaque_instruction_fails_without_definition():
    qc = QuantumCircuit(1)
    qc.append(Instruction("unrecognized_black_box", 1, 0, []), [0])
    with pytest.raises(ValueError, match="Does not support"):
        normalize(qc)


# ==========================================================================
# 3. SYMBOLIC PARAMETERS (NO PREMATURE BINDING)
# ==========================================================================


@pytest.mark.parametrize("angle", [-2.4, -0.1, 0, 0.41, 2.35])
def test_parameterized_rx_ry_preserve_symbol_and_bind_correctly(angle):
    theta = Parameter("theta")
    qc = QuantumCircuit(2)
    qc.rx(theta, 1)
    qc.ry(2 * theta - math.pi / 7, 0)
    qc.cx(1, 0)

    out = normalize(qc)
    assert_internal_basis(out)
    assert {p.name for p in out.parameters} == {"theta"}
    assert_exact_operator(qc.assign_parameters({theta: angle}),
                          out.assign_parameters({theta: angle}))


@pytest.mark.parametrize("theta_value, phi_value", [(0.0, 0.0), (0.3, -0.9), (-1.1, 2.1)])
def test_symbolic_u_parameters_and_global_phase_bind_correctly(theta_value, phi_value):
    theta, phi = Parameter("theta"), Parameter("phi")
    qc = QuantumCircuit(2)
    qc.global_phase = theta / 3
    qc.u(theta / 2, phi, -theta + phi, 1)
    qc.rx(phi, 0)
    qc.ry(theta - phi, 1)

    out = normalize(qc)
    assert_internal_basis(out)
    assert {p.name for p in out.parameters} == {"theta", "phi"}
    binding = {theta: theta_value, phi: phi_value}
    assert_exact_operator(qc.assign_parameters(binding), out.assign_parameters(binding))


def test_parameterized_custom_gate_with_nonconsecutive_wires():
    alpha = Parameter("alpha")
    small = QuantumCircuit(2, name="param_layer")
    small.rx(alpha, 0)
    small.crz(2 * alpha, 0, 1)

    qc = QuantumCircuit(3)
    qc.append(small.to_gate(), [2, 0])
    qc.ry(-alpha, 1)
    out = normalize(qc)

    assert {p.name for p in out.parameters} == {"alpha"}
    assert_internal_basis(out)
    for value in [0.0, math.pi / 4, -1.73]:
        assert_exact_operator(qc.assign_parameters({alpha: value}),
                              out.assign_parameters({alpha: value}))


def test_symbolic_parameters_are_not_replaced_with_numeric_values():
    theta = Parameter("theta")
    qc = QuantumCircuit(2)
    qc.ry(theta, 0)
    qc.rx(theta, 1)
    out = normalize(qc)
    assert out.num_parameters == 1
    assert out.parameters == qc.parameters
    assert any(
        theta in getattr(item.operation.params[0], "parameters", set())
        for item in out.data
        if item.operation.name == "rz"
    )


# ==========================================================================
# 4. CORRECT PHYSICAL / LOGICAL WIRE ASSIGNMENT
# ==========================================================================


@pytest.mark.parametrize("control,target", [(0, 2), (2, 0), (1, 0), (2, 1)])
def test_ordinary_cx_control_target_order_is_preserved(control, target):
    qc = QuantumCircuit(3)
    qc.cx(control, target)
    out = normalize(qc)
    assert cx_operands(out) == [(control, target)]
    assert_exact_operator(qc, out)


@pytest.mark.parametrize("control,target", [(0, 2), (2, 0), (2, 1)])
def test_open_control_cx_is_decomposed_on_correct_wires(control, target):
    qc = QuantumCircuit(3)
    qc.append(CXGate(ctrl_state=0), [control, target])
    out = normalize(qc)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_swap_between_nonconsecutive_qubits_preserves_untouched_wire():
    qc = QuantumCircuit(3)
    qc.h(1)
    qc.swap(2, 0)
    qc.ry(-0.6, 1)
    qc.cx(2, 1)
    out = normalize(qc)
    assert out.num_qubits == 3
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_ccx_on_permuted_three_qubit_order_is_correct():
    qc = QuantumCircuit(3)
    qc.x(1)
    qc.ccx(2, 0, 1)
    out = normalize(qc)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_multiple_quantum_registers_and_custom_gate_wire_order():
    left = QuantumRegister(1, "left")
    right = QuantumRegister(2, "right")
    qc = QuantumCircuit(left, right)
    small = QuantumCircuit(2, name="across_registers")
    small.cx(1, 0)
    small.ry(0.4, 1)
    qc.append(small.to_gate(), [right[1], left[0]])
    qc.swap(left[0], right[0])

    out = normalize(qc)
    assert_internal_basis(out)
    assert_preserved_registers(qc, out)
    assert_exact_operator(qc, out)


# ==========================================================================
# 5. MEASUREMENTS / PARTIAL & SHARED BARRIERS
# ==========================================================================


def test_measure_all_creates_correct_mapping_and_keeps_barrier(monkeypatch):
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.measure_all()
    parsed = parse_qc(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0, 1: 1, 2: 2}
    assert barrier_operands(parsed.DAG_circuit) == [(0, 1, 2)]
    assert "measure" not in op_names(parsed.DAG_circuit)


def test_measure_all_appends_classical_register_after_existing_bits(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.measure_all()
    parsed = parse_qc(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 2, 1: 3}
    assert len(parsed.DAG_circuit.clbits) == 4
    assert [(r.name, r.size) for r in parsed.DAG_circuit.cregs.values()] == [
        (r.name, r.size) for r in qc.cregs
    ]


def test_measurements_across_distinct_classical_registers(monkeypatch):
    qa = QuantumRegister(1, "qa")
    qb = QuantumRegister(2, "qb")
    ca = ClassicalRegister(2, "ca")
    cb = ClassicalRegister(3, "cb")
    qc = QuantumCircuit(qa, qb, ca, cb)
    qc.h(qb[1])
    qc.measure(qb[1], cb[2])  # q2 -> c4 (flattened)
    qc.measure(qa[0], ca[1])  # q0 -> c1
    parsed = parse_qc(monkeypatch, qc)
    assert parsed.final_measure_map == {2: 4, 0: 1}
    assert [(r.name, r.size) for r in parsed.DAG_circuit.cregs.values()] == [
        (r.name, r.size) for r in qc.cregs
    ]


def test_duplicate_measurements_separated_by_partial_barrier_are_merged(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.measure(0, 1)
    qc.barrier(0)
    qc.measure(0, 1)
    qc.h(1)
    parsed = parse_qc(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 1}
    assert barrier_operands(parsed.DAG_circuit) == [(0,)]
    assert wire_ops(parsed.DAG_circuit, 1) == ["h"]


def test_measurement_followed_by_barrier_on_measured_qubit_is_terminal(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.barrier(0)
    qc.h(1)
    parsed = parse_qc(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert barrier_operands(parsed.DAG_circuit) == [(0,)]


def test_measurement_after_shared_barrier_with_other_qubit_work_is_allowed(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.barrier(0, 1)
    qc.measure(0, 0)
    qc.h(1)
    parsed = parse_qc(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert barrier_operands(parsed.DAG_circuit) == [(0, 1)]
    assert wire_ops(parsed.DAG_circuit, 1) == ["barrier", "h"]


def test_measurement_then_nonterminal_shared_barrier_is_rejected(monkeypatch):
    # Our conservative policy considers the shared barrier non-final because
    # q1 has a gate after it. The measurement before that barrier stays mid-circuit.
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.barrier(0, 1)
    qc.h(1)
    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_qc(monkeypatch, qc)


def test_final_measurements_followed_by_full_width_barrier_are_accepted(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.measure(0, 0)
    qc.measure(1, 1)
    qc.barrier(0, 1)
    parsed = parse_qc(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0, 1: 1}
    assert barrier_operands(parsed.DAG_circuit) == [(0, 1)]


def test_measurement_rewrites_to_different_classical_register_are_rejected(monkeypatch):
    ca, cb = ClassicalRegister(1, "ca"), ClassicalRegister(1, "cb")
    qc = QuantumCircuit(QuantumRegister(1, "q"), ca, cb)
    qc.measure(0, ca[0])
    qc.measure(0, cb[0])
    with pytest.raises(ValueError, match="different classical bits"):
        parse_qc(monkeypatch, qc)


def test_distinct_qubits_overwriting_one_classical_bit_are_rejected(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.measure(1, 0)
    qc.measure(0, 0)
    with pytest.raises(ValueError, match="same classical bit"):
        parse_qc(monkeypatch, qc)


def test_measurement_followed_by_custom_unitary_on_same_qubit_is_rejected(monkeypatch):
    small = QuantumCircuit(1, name="after_measure")
    small.ry(0.63, 0)
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)
    qc.append(small.to_gate(), [0])
    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_qc(monkeypatch, qc)


# ==========================================================================
# 6. NESTED UNSUPPORTED INSTRUCTIONS
# ==========================================================================


@pytest.mark.parametrize("forbidden", ["delay", "reset"])
def test_parser_rejects_forbidden_inside_one_level_instruction(monkeypatch, forbidden):
    inner = QuantumCircuit(1, name="hidden_" + forbidden)
    if forbidden == "delay":
        inner.delay(50, 0, unit="dt")
    else:
        inner.reset(0)
    qc = QuantumCircuit(1)
    qc.append(inner.to_instruction(), [0])
    with pytest.raises(ValueError, match=forbidden):
        parse_qc(monkeypatch, qc)


@pytest.mark.parametrize("forbidden", ["delay", "reset"])
def test_parser_rejects_forbidden_inside_two_levels_instruction(monkeypatch, forbidden):
    leaf = QuantumCircuit(1, name="leaf_" + forbidden)
    if forbidden == "delay":
        leaf.delay(0, 0, unit="dt")  # zero-duration delays are still prohibited
    else:
        leaf.reset(0)

    wrapper = QuantumCircuit(1, name="wrapper")
    wrapper.append(leaf.to_instruction(), [0])

    qc = QuantumCircuit(1)
    qc.append(wrapper.to_instruction(), [0])
    with pytest.raises(ValueError, match=forbidden):
        parse_qc(monkeypatch, qc)


def test_parser_rejects_hidden_measurement_in_custom_instruction(monkeypatch):
    inner = QuantumCircuit(1, 1, name="hidden_measure")
    inner.measure(0, 0)
    qc = QuantumCircuit(1, 1)
    qc.append(inner.to_instruction(), [0], [0])
    with pytest.raises(ValueError, match="measurement"):
        parse_qc(monkeypatch, qc)


def test_parser_accepts_nested_unitary_instruction_without_forbidden_content(monkeypatch):
    inner = QuantumCircuit(2, name="legal")
    inner.ry(0.3, 0)
    inner.cx(0, 1)
    middle = QuantumCircuit(2, name="legal_wrapper")
    middle.append(inner.to_gate(), [1, 0])

    qc = QuantumCircuit(3)
    qc.append(middle.to_gate(), [2, 0])
    parsed = parse_qc(monkeypatch, qc)
    normalized = normalize(dag_to_circuit(parsed.DAG_circuit))
    assert_internal_basis(normalized)
    assert_exact_operator(qc, normalized)


# ==========================================================================
# 7. STATE PRESERVATION AND INPUT IMMUTABILITY
# ==========================================================================


def test_orig_dag_is_snapshot_before_normalization():
    qc = QuantumCircuit(2)
    qc.ry(0.53, 1)
    qc.z(0)
    dag = circuit_to_dag(qc)
    result = Norm(dag)
    assert set(op_names(result.orig_dag)) == {"ry", "z"}
    assert "ry" not in op_names(result.normalized_dag)
    assert "z" not in op_names(result.normalized_dag)
    assert_exact_operator(dag_to_circuit(result.orig_dag),
                          dag_to_circuit(result.normalized_dag))



def test_normalizer_does_not_mutate_source_quantum_circuit():
    qc = QuantumCircuit(2)
    qc.ry(0.6, 0)
    qc.cx(0, 1)
    original_names = circuit_op_names(qc)
    original_matrix = Operator(qc).data.copy()
    normalize(qc)
    assert circuit_op_names(qc) == original_names
    np.testing.assert_allclose(Operator(qc).data, original_matrix, atol=0, rtol=0)


@pytest.mark.parametrize("num_qubits", [1, 2, 3])
def test_idle_qubits_and_width_survive_normalization(num_qubits):
    qc = QuantumCircuit(num_qubits)
    qc.rx(0.34, 0)
    out = normalize(qc)
    assert out.num_qubits == num_qubits
    assert_preserved_registers(qc, out)
    assert_exact_operator(qc, out)


def test_empty_circuit_with_global_phase_keeps_register_structure():
    qc = QuantumCircuit(3, 2)
    qc.global_phase = math.pi / 7
    out = normalize(qc)
    assert circuit_op_names(out) == []
    assert_preserved_registers(qc, out)
    assert_same_phase_mod_2pi(out.global_phase, qc.global_phase)
    assert_exact_operator(qc, out)


def test_normalizer_preserves_idle_classical_bits_and_registers():
    qreg = QuantumRegister(2, "logical")
    creg = ClassicalRegister(4, "results")
    qc = QuantumCircuit(qreg, creg)
    qc.rx(0.3, qreg[1])
    qc.z(qreg[0])
    out = normalize(qc)
    assert_preserved_registers(qc, out)
    assert_internal_basis(out)
    assert_exact_operator(qc, out)


def test_parser_removes_only_working_dag_measurements_not_original_circuit(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.global_phase = 0.31
    qc.ry(0.4, 1)
    qc.barrier(1)
    qc.measure(1, 0)
    qc.measure(0, 1)
    original_names = circuit_op_names(qc)

    parsed = parse_qc(monkeypatch, qc)
    assert circuit_op_names(qc) == original_names
    assert circuit_op_names(parsed.circuit) == original_names
    assert "measure" not in op_names(parsed.DAG_circuit)
    assert barrier_operands(parsed.DAG_circuit) == [(1,)]
    assert parsed.final_measure_map == {1: 0, 0: 1}
    assert parsed.DAG_circuit.num_qubits() == 2
    assert len(parsed.DAG_circuit.clbits) == 2
    assert_same_phase_mod_2pi(parsed.DAG_circuit.global_phase, qc.global_phase)


def test_parser_and_normalizer_preserve_global_phase_end_to_end(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.global_phase = math.pi / 9
    qc.h(0)
    qc.u(0.6, 0.3, -0.4, 1)
    qc.s(0)
    qc.measure(0, 1)
    qc.measure(1, 0)
    parsed = parse_qc(monkeypatch, qc)

    # Build the exact pre-measurement circuit independently; do not rely on
    # mutation of Qiskit's CircuitData container.
    unitary_only = QuantumCircuit(2, 2)
    unitary_only.global_phase = math.pi / 9
    unitary_only.h(0)
    unitary_only.u(0.6, 0.3, -0.4, 1)
    unitary_only.s(0)

    out = normalize(dag_to_circuit(parsed.DAG_circuit))
    assert parsed.final_measure_map == {0: 1, 1: 0}
    assert_internal_basis(out)
    assert_preserved_registers(unitary_only, out)
    assert_exact_operator(unitary_only, out)


def test_normalizing_again_is_idempotent_in_basis_and_exact_operator():
    qc = QuantumCircuit(3)
    qc.global_phase = 0.21
    qc.ry(0.41, 2)
    qc.swap(2, 0)
    qc.t(1)
    first = normalize(qc)
    second = normalize(first)
    assert_internal_basis(first)
    assert_internal_basis(second)
    assert circuit_op_names(first) == circuit_op_names(second)
    assert_exact_operator(qc, first)
    assert_exact_operator(first, second)


# ==========================================================================
# REAL OPENQASM 3 INTEGRATION (runs normally; no optional-test skips)
# ==========================================================================


def test_real_qasm3_multiregister_barrier_measurement_pipeline(tmp_path):
    path = tmp_path / "multiregister.qasm"
    path.write_text(
        'OPENQASM 3.0;\n'
        'include "stdgates.inc";\n'
        'qubit[1] qa;\n'
        'qubit[2] qb;\n'
        'bit[1] ca;\n'
        'bit[2] cb;\n'
        'h qb[1];\n'
        'barrier qa[0];\n'
        'U(0.21, 0.43, -0.37) qa[0];\n'
        'cx qb[1], qa[0];\n'
        'cb[0] = measure qb[1];\n'
        'ca[0] = measure qa[0];\n',
        encoding="utf-8",
    )
    parsed = parser_0(str(path))
    assert parsed.final_measure_map == {2: 1, 0: 0}
    assert barrier_operands(parsed.DAG_circuit) == [(0,)]
    before = dag_to_circuit(parsed.DAG_circuit)
    after = normalize(before)
    assert_internal_basis(after)
    assert_preserved_registers(before, after)
    assert_exact_operator(before, after)
