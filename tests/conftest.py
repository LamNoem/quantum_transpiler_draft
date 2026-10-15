"""Shared fixtures for the three optimizer test files.

Run from the repository root:
    python -m pytest tests/optimizer -v

No optimizer implementation is patched here. ``engine`` deliberately bypasses
__init__ so a broken constructor does not obscure failures in individual passes.
The public constructor is tested separately. Imports are deferred until fixture
setup, so pytest --collect-only can inspect the suite without importing Qiskit.
"""
from __future__ import annotations

import importlib
import os
from collections import Counter

import numpy as np
import pytest

# Default matches the module path in your traceback. Only change this one place
# if the implementation moves, or set the OPTIMIZER_MODULE environment variable.
OPTIMIZER_MODULE = os.environ.get(
    "OPTIMIZER_MODULE", "simple_optim_2.optim_gates"
)
ALLOWED_GATES = frozenset({"h", "x", "rz", "cx"})
ATOL = 1e-10
RTOL = 1e-10


@pytest.fixture(scope="session")
def optimizer_class():
    """Import the real project class; missing dependencies are errors, not skips."""
    return importlib.import_module(OPTIMIZER_MODULE).OptimGates


@pytest.fixture
def engine(optimizer_class):
    """Function tests must not depend on the constructor or its equivalence check."""
    return optimizer_class.__new__(optimizer_class)


class CircuitChecks:
    """Small, independent test oracles; never invoke an optimizer/transpiler."""

    def __init__(self):
        from qiskit import QuantumCircuit
        from qiskit.converters import circuit_to_dag, dag_to_circuit
        from qiskit.dagcircuit import DAGCircuit
        from qiskit.quantum_info import Operator

        self.QuantumCircuit = QuantumCircuit
        self.to_dag = circuit_to_dag
        self.from_dag = dag_to_circuit
        self.DAGCircuit = DAGCircuit
        self.Operator = Operator

    def circuit(self, n, ops=(), *, n_clbits=0, phase=0.0):
        """Build explicit fixtures, e.g. [('h', 0), ('rz', 0.5, 0), ('cx', 0, 1)]."""
        qc = self.QuantumCircuit(n, n_clbits)
        qc.global_phase = phase
        for name, *args in ops:
            getattr(qc, name)(*args)
        return qc

    def as_circuit(self, value):
        if isinstance(value, self.DAGCircuit):
            return self.from_dag(value)
        assert isinstance(value, self.QuantumCircuit), (
            f"Expected QuantumCircuit or DAGCircuit, got {type(value).__name__}. "
            "A trailing comma after an assignment creates a tuple."
        )
        return value

    def as_dag(self, value):
        return value if isinstance(value, self.DAGCircuit) else self.to_dag(value)

    def clone(self, value):
        return self.to_dag(self.as_circuit(value).copy())

    def nodes(self, dag, name=None, qubits=None):
        """Fresh DAG traversal; no reliance on Python object identity or node order."""
        result = []
        for node in dag.topological_op_nodes():
            if name is not None and node.op.name != name:
                continue
            qindices = tuple(dag.find_bit(q).index for q in node.qargs)
            if qubits is not None and qindices != tuple(qubits):
                continue
            result.append(node)
        return result

    def matrix(self, value):
        """Exact-unitary oracle, including global phase.

        Remove ONLY barrier directives from a fresh oracle copy. Never remove
        barriers from the input to the optimizer, and never drop measurements,
        resets, or other nonunitary instructions to make a check pass.
        """
        qc = self.as_circuit(value)
        clean = qc.copy_empty_like()
        clean.global_phase = qc.global_phase
        for instruction in qc.data:
            if instruction.operation.name == "barrier":
                continue
            clean.append(
                instruction.operation,
                [clean.qubits[qc.find_bit(q).index] for q in instruction.qubits],
                [clean.clbits[qc.find_bit(c).index] for c in instruction.clbits],
            )
        return self.Operator(clean).data

    def assert_exact(self, before, after):
        """Stronger than Operator.equiv: do not quotient out global phase."""
        a, b = self.as_circuit(before), self.as_circuit(after)
        assert a.num_qubits == b.num_qubits, "Optimizer changed quantum width"
        assert a.num_clbits == b.num_clbits, "Optimizer changed classical width"
        np.testing.assert_allclose(
            self.matrix(b), self.matrix(a), rtol=RTOL, atol=ATOL,
            err_msg="Optimizer changed the unitary (including global phase)",
        )

    def assert_symbolic_exact(self, before, after, bindings):
        """Test symbolic identities at explicit bindings; not a symbolic proof."""
        a, b = self.as_circuit(before), self.as_circuit(after)
        for values in bindings:
            # A valid simplification can eliminate a parameter altogether.
            bound_a = a.assign_parameters({p: v for p, v in values.items() if p in a.parameters})
            bound_b = b.assign_parameters({p: v for p, v in values.items() if p in b.parameters})
            assert not bound_a.parameters and not bound_b.parameters, "Incomplete binding"
            self.assert_exact(bound_a, bound_b)

    def assert_shape_preserved(self, before, after):
        a, b = self.as_circuit(before), self.as_circuit(after)
        assert list(b.qubits) == list(a.qubits), "Logical qubit identities/order changed"
        assert list(b.clbits) == list(a.clbits), "Classical bit identities/order changed"
        assert [(r.name, len(r)) for r in b.qregs] == [(r.name, len(r)) for r in a.qregs]
        assert [(r.name, len(r)) for r in b.cregs] == [(r.name, len(r)) for r in a.cregs]

    def assert_same_dag(self, before, after):
        """Data-flow equality, not a comparison of wrapper IDs or draw() strings."""
        assert self.as_dag(before) == self.as_dag(after), "DAG structure/operations changed"
        self.assert_shape_preserved(before, after)

    def assert_output(self, before, after, *, counts, size, expected=None, depth=None):
        assert isinstance(after, self.DAGCircuit), (
            f"Expected a DAGCircuit, got {type(after).__name__}"
        )
        self.assert_exact(before, after)
        self.assert_shape_preserved(before, after)
        actual_counts = dict(after.count_ops())
        assert actual_counts == counts, f"Expected {counts}, got {actual_counts}"
        assert after.size() == size, "Unexpected raw DAG operation count"
        assert set(actual_counts) <= ALLOWED_GATES | {"barrier"}
        if expected is not None:
            # Validate the expected fixture as well as the optimizer's result.
            self.assert_exact(before, expected)
            self.assert_exact(expected, after)
        if depth is not None:
            assert after.depth() == depth, "Unexpected DAG depth"

    def run(self, engine, method, circuit, **kwargs):
        dag = self.clone(circuit)
        result = getattr(engine, method)(dag, **kwargs)
        if method in {"inverse_cancellation", "merge_adjacent_RZ"}:
            assert type(result) is bool, "Standalone passes must return a change flag"
            return dag
        assert isinstance(result, self.DAGCircuit), "Optimizer must return a DAGCircuit"
        return result

    def cost(self, value):
        """The module's lexicographic objective, not an assumed hardware cost."""
        dag = self.as_dag(value)
        return (dag.count_ops().get("cx", 0), dag.size(), dag.depth())

    def gate_count(self, value):
        """Unitary basis gates only; a preserved barrier is NOT a gate."""
        return sum(n.op.name in ALLOWED_GATES for n in self.as_dag(value).op_nodes())

    def barrier_signatures(self, value):
        dag = self.as_dag(value)
        # Multiset: independent barriers need not have a unique global order.
        return Counter(
            (tuple(dag.find_bit(q).index for q in n.qargs), n.op.label)
            for n in dag.op_nodes() if n.op.name == "barrier"
        )

    def wire_names(self, value, qubit):
        dag = self.as_dag(value)
        return [n.op.name for n in dag.nodes_on_wire(dag.qubits[qubit], only_ops=True)]

    def wire_segments(self, value, qubit):
        """Operation names separated by barriers, in this wire's dependency order."""
        segments = [[]]
        for name in self.wire_names(value, qubit):
            if name == "barrier":
                segments.append([])
            else:
                segments[-1].append(name)
        return segments


@pytest.fixture(scope="session")
def tools():
    return CircuitChecks()
