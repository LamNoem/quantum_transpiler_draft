"""

Usage from your repository root:
    python -m pytest -v tests/test_parser_norm_basic.py
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


# Avoid conflating missing optional import dependencies with a parser bug.
requires_qasm3_importer = pytest.mark.skipif(
    importlib.util.find_spec("qiskit_qasm3_import") is None,
    reason="Install qiskit-qasm3-import to run OpenQASM 3 integration tests",
)


def assert_exact_operator(expected_circuit, actual_circuit, atol=1e-10):
    """Stricter than Operator.equiv(): checks global phase as well."""
    expected = Operator(expected_circuit).data
    actual = Operator(actual_circuit).data
    assert expected.shape == actual.shape
    np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=atol)


def wire_names(dag, qubit_index):
    """Operations touching this particular logical wire, in dependency order."""
    qubit = dag.qubits[qubit_index]
    return [
        node.op.name for node in dag.topological_op_nodes()
        if qubit in node.qargs
    ]


def parse_circuit(monkeypatch, qc):
    """Test your parser on a Qiskit circuit, bypassing only the QASM text importer."""
    monkeypatch.setattr(qiskit.qasm3, "load", lambda unused_path: qc)
    return parser_0("unused.qasm")


def operation_names(dag):
    return [node.op.name for node in dag.topological_op_nodes()]


def barrier_qubits(dag):
    return [
        tuple(dag.find_bit(bit).index for bit in node.qargs)
        for node in dag.topological_op_nodes()
        if node.op.name == "barrier"
    ]


# -------- BARRIERS --------

@pytest.mark.parametrize("affected_qubits", [(0,), (0, 1)])
def test_barrier_is_preserved_with_correct_operands(monkeypatch, affected_qubits):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.barrier(*affected_qubits)
    qc.h(0)

    parsed = parse_circuit(monkeypatch, qc)
    assert barrier_qubits(parsed.DAG_circuit) == [affected_qubits]
    assert parsed.final_measure_map == {}


def test_barrier_survives_normalization():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.barrier(0)
    qc.rx(0.37, 1)  # Has to be normalized into H-RZ-H.
    qc.h(0)

    norm = Norm(circuit_to_dag(qc))
    result = norm.normalized_dag

    assert barrier_qubits(result) == [(0,)]
    assert set(operation_names(result)) <= {"h", "x", "rz", "cx", "barrier"}
    assert Operator(qc).equiv(Operator(dag_to_circuit(result)))


# -------- MEASUREMENTS --------

def test_exact_duplicate_measurements_are_collapsed(monkeypatch):
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.measure(0, 0)
    qc.measure(0, 0)

    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert "measure" not in operation_names(parsed.DAG_circuit)
    assert operation_names(parsed.DAG_circuit) == ["h"]


def test_same_qubit_to_different_classical_bits_is_rejected(monkeypatch):
    qc = QuantumCircuit(1, 2)
    qc.measure(0, 0)
    qc.measure(0, 1)

    with pytest.raises(ValueError, match="different classical bits"):
        parse_circuit(monkeypatch, qc)


def test_different_qubits_to_same_classical_bit_is_rejected(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.measure(1, 0)

    with pytest.raises(ValueError, match="same classical bit"):
        parse_circuit(monkeypatch, qc)


def test_independent_measurements_preserve_destination_indices(monkeypatch):
    qc = QuantumCircuit(2, 3)
    qc.measure(0, 2)
    qc.measure(1, 0)

    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 2, 1: 0}
    assert "measure" not in operation_names(parsed.DAG_circuit)


def test_measurement_before_gate_on_same_qubit_is_rejected(monkeypatch):
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)
    qc.h(0)

    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_circuit(monkeypatch, qc)


def test_measurement_before_entangling_gate_is_rejected(monkeypatch):
    qc = QuantumCircuit(2, 1)
    qc.measure(0, 0)
    qc.cx(0, 1)

    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_circuit(monkeypatch, qc)


def test_gate_on_other_qubit_after_measurement_is_allowed(monkeypatch):
    qc = QuantumCircuit(2, 2)
    qc.measure(0, 0)
    qc.h(1)
    qc.measure(1, 1)

    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0, 1: 1}
    assert operation_names(parsed.DAG_circuit) == ["h"]


def test_terminal_barrier_after_measurement_is_allowed(monkeypatch):
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)
    qc.barrier(0)

    parsed = parse_circuit(monkeypatch, qc)
    assert parsed.final_measure_map == {0: 0}
    assert operation_names(parsed.DAG_circuit) == ["barrier"]


def test_measure_gate_measure_is_not_treated_as_duplicate(monkeypatch):
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)
    qc.h(0)
    qc.measure(0, 0)

    with pytest.raises(ValueError, match="mid-circuit measurement"):
        parse_circuit(monkeypatch, qc)


# -------- UNSUPPORTED FEATURES --------

@pytest.mark.parametrize("unsupported", ["delay", "reset"])
def test_delay_and_reset_are_rejected(monkeypatch, unsupported):
    qc = QuantumCircuit(1)
    if unsupported == "delay":
        qc.delay(100, 0, unit="dt")
    else:
        qc.reset(0)

    with pytest.raises(ValueError, match=unsupported):
        parse_circuit(monkeypatch, qc)


def test_classical_variable_is_rejected(monkeypatch):
    qc = QuantumCircuit(1)
    qc.add_var("flag", False)

    with pytest.raises(ValueError, match="classical variables"):
        parse_circuit(monkeypatch, qc)


def test_classical_control_flow_is_rejected(monkeypatch):
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)
    with qc.if_test((qc.clbits[0], 1)):
        qc.x(0)

    with pytest.raises(ValueError, match="control flow"):
        parse_circuit(monkeypatch, qc)


def test_more_than_three_qubits_is_rejected(monkeypatch):
    qc = QuantumCircuit(4)
    with pytest.raises(ValueError, match="3 qubits"):
        parse_circuit(monkeypatch, qc)


def test_ancilla_is_rejected(monkeypatch):
    qc = QuantumCircuit(QuantumRegister(1), AncillaRegister(1))
    with pytest.raises(ValueError, match="ancillas"):
        parse_circuit(monkeypatch, qc)


# -------- NORMALIZATION CORRECTNESS --------

@pytest.mark.parametrize(
    "apply_gate",
    [
        lambda qc: qc.rx(0.23, 0),
        lambda qc: qc.ry(-0.47, 0),
        lambda qc: qc.z(0),
        lambda qc: qc.s(0),
        lambda qc: qc.sdg(0),
        lambda qc: qc.t(0),
        lambda qc: qc.tdg(0),
        lambda qc: qc.u(0.31, -0.42, 0.53, 0),
        lambda qc: qc.append(CXGate(ctrl_state=0), [0, 1]),
    ],
    ids=["rx", "ry", "z", "s", "sdg", "t", "tdg", "u", "open_cx"],
)
def test_normalization_preserves_unitary_and_gate_set(apply_gate):
    qc = QuantumCircuit(2)
    qc.h(0)
    apply_gate(qc)
    qc.cx(0, 1)

    norm = Norm(circuit_to_dag(qc))
    result = dag_to_circuit(norm.normalized_dag)

    assert set(instruction.operation.name for instruction in result.data) <= {
        "h", "x", "rz", "cx", "barrier"
    }
    assert Operator(qc).equiv(Operator(result))


# -------- REAL OPENQASM 3 INTEGRATION --------

@requires_qasm3_importer
def test_real_qasm3_import_and_parser(tmp_path):
    qasm = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
barrier q[0];
cx q[0], q[1];
c[1] = measure q[0];
c[0] = measure q[1];
"""
    path = tmp_path / "valid.qasm"
    path.write_text(qasm, encoding="utf-8")

    parsed = parser_0(str(path))
    assert parsed.final_measure_map == {0: 1, 1: 0}
    assert barrier_qubits(parsed.DAG_circuit) == [(0,)]
    assert "measure" not in operation_names(parsed.DAG_circuit)

    normalized = Norm(parsed.DAG_circuit)
    assert set(operation_names(normalized.normalized_dag)) <= {
        "h", "x", "rz", "cx", "barrier"
    }


@requires_qasm3_importer
@pytest.mark.parametrize(
    "body, expected_map, error_fragment",
    [
        (
            "c[0] = measure q[0]; c[0] = measure q[0];",
            {0: 0},
            None,
        ),
        (
            "c[0] = measure q[0]; c[1] = measure q[0];",
            None,
            "different classical bits",
        ),
        (
            "c[0] = measure q[0]; c[0] = measure q[1];",
            None,
            "same classical bit",
        ),
    ],
)
def test_real_qasm3_repeated_and_conflicting_measurements(
    tmp_path, body, expected_map, error_fragment
):
    qasm = (
        'OPENQASM 3.0;\ninclude "stdgates.inc";\n'
        'qubit[2] q;\nbit[2] c;\n' + body + '\n'
    )
    path = tmp_path / "measurements.qasm"
    path.write_text(qasm, encoding="utf-8")

    if error_fragment is not None:
        with pytest.raises(ValueError, match=error_fragment):
            parser_0(str(path))
    else:
        parsed = parser_0(str(path))
        assert parsed.final_measure_map == expected_map


@requires_qasm3_importer
def test_invalid_qasm_is_reported_at_import(tmp_path):
    path = tmp_path / "invalid.qasm"
    path.write_text("OPENQASM 3.0; this is not valid QASM;", encoding="utf-8")

    with pytest.raises(ValueError, match="Initial load into qiskit failed"):
        parser_0(str(path))

