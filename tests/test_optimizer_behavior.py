"""3. Project behavior contracts, not only matrix/gate-count correctness.

Barrier acceptance/preservation is REQUIRED by the requested project behavior,
although the supplied full_optimize currently rejects barriers. These tests fail
normally until that implementation gap is fixed: no xfail, skip, or removing
barriers before calling the optimizer.

Measurements are different: this unitary optimizer receives a DAG after the
upstream terminal-measurement handling. Raw measurement/reset/control-flow/delay
instructions are rejected here; this suite does not test the parser/normalizer.
"""
from collections import Counter
from math import pi

import numpy as np
import pytest


# Each low-level pass is tested with the rule it actually implements.
FENCE_CASES = [
    pytest.param(method, name, id=f"{method}-{name}")
    for name, methods in [
        ("h", ("inverse_cancellation", "greedy_optimize", "full_optimize")),
        ("x", ("inverse_cancellation", "greedy_optimize", "full_optimize")),
        ("cx", ("inverse_cancellation", "greedy_optimize", "full_optimize")),
        ("rz", ("merge_adjacent_RZ", "greedy_optimize", "full_optimize")),
    ]
    for method in methods
]


class TestBarrierFences:
    @pytest.mark.parametrize("method,gate", FENCE_CASES)
    def test_never_cancel_or_merge_across_a_barrier(self, engine, tools, method, gate):
        source = tools.circuit(2)
        operands = (0, 1) if gate == "cx" else (0,)
        if gate == "rz":
            source.rz(0.2, 0)
        else:
            getattr(source, gate)(*operands)
        source.barrier(*operands, label="optimization-fence")
        if gate == "rz":
            source.rz(0.3, 0)
        else:
            getattr(source, gate)(*operands)
        # A ValueError for a barrier is a failure of the desired behavior, too.
        result = tools.run(engine, method, source)
        tools.assert_same_dag(source, result)
        tools.assert_exact(source, result)
        assert tools.barrier_signatures(result) == tools.barrier_signatures(source)
        assert result.count_ops().get(gate, 0) == 2

    @pytest.mark.parametrize("method", ["greedy_optimize", "full_optimize"])
    @pytest.mark.parametrize("barrier_qubit", [0, 1])
    def test_fence_on_either_cx_operand_blocks_cancellation(self, engine, tools, method, barrier_qubit):
        source = tools.circuit(2)
        source.cx(0, 1)
        source.barrier(barrier_qubit, label="one-wire-fence")
        source.cx(0, 1)
        result = tools.run(engine, method, source)
        tools.assert_output(source, result, counts={"cx": 2, "barrier": 1}, size=3)
        assert tools.barrier_signatures(result) == tools.barrier_signatures(source)

    @pytest.mark.parametrize("method", ["greedy_optimize", "full_optimize"])
    def test_unrelated_wire_barrier_is_not_a_global_fence(self, engine, tools, method):
        source = tools.circuit(3)
        source.h(0)
        source.barrier(2, label="q2-only")
        source.h(0)
        result = tools.run(engine, method, source)
        tools.assert_output(source, result, counts={"barrier": 1}, size=1)
        assert tools.barrier_signatures(result) == tools.barrier_signatures(source)

    @pytest.mark.parametrize("method", ["greedy_optimize", "full_optimize"])
    def test_can_optimize_within_each_barrier_region(self, engine, tools, method):
        source = tools.circuit(1)
        source.rz(0.1, 0)
        source.rz(0.2, 0)
        source.barrier(0, label="middle")
        source.rz(0.4, 0)
        source.rz(0.5, 0)
        result = tools.run(engine, method, source)
        tools.assert_output(source, result, counts={"rz": 2, "barrier": 1}, size=3)
        on_wire = list(result.nodes_on_wire(result.qubits[0], only_ops=True))
        assert [n.op.name for n in on_wire] == ["rz", "barrier", "rz"]
        assert float(on_wire[0].op.params[0]) == pytest.approx(0.3)
        assert float(on_wire[2].op.params[0]) == pytest.approx(0.9)
        assert on_wire[1].op.label == "middle"

    @pytest.mark.parametrize("method", ["greedy_optimize", "full_optimize"])
    def test_adjacent_barriers_are_not_gates_to_cancel_or_swap(self, engine, tools, method):
        source = tools.circuit(1)
        source.barrier(0, label="first")
        source.barrier(0, label="second")
        result = tools.run(engine, method, source)
        assert dict(result.count_ops()) == {"barrier": 2}
        labels = [n.op.label for n in result.nodes_on_wire(result.qubits[0], only_ops=True)]
        assert labels == ["first", "second"]
        tools.assert_same_dag(source, result)

    def test_commutation_search_does_not_move_gates_across_fence(self, engine, tools):
        source = tools.circuit(2)
        source.cx(0, 1)
        source.rz(0.5, 0)
        source.barrier(0, 1, label="full-fence")
        source.cx(0, 1)
        result = engine.full_optimize(tools.to_dag(source), beam_width=4, max_depth=3)
        tools.assert_output(source, result, counts={"cx": 2, "rz": 1, "barrier": 1}, size=4)
        # RZ and CX may exchange order WITHIN the left region, not change sides.
        assert [Counter(s) for s in tools.wire_segments(result, 0)] == [
            Counter({"cx": 1, "rz": 1}), Counter({"cx": 1}),
        ]
        assert tools.barrier_signatures(result) == tools.barrier_signatures(source)

    def test_reported_gate_count_excludes_barrier_directives(self, optimizer_class, tools):
        source = tools.circuit(1)
        source.h(0)
        source.barrier(0, label="preserved")
        source.h(0)
        instance = optimizer_class(tools.to_dag(source))
        assert instance.optim_dag.size() == 3, "Raw DAG size includes the barrier operation"
        assert instance.gate_count == 2, "A barrier is a directive, not a unitary gate"
        assert instance.gate_count == tools.gate_count(instance.optim_dag)
        assert instance.depth == instance.optim_dag.depth(), "Keep the module's DAG-depth convention"
        assert bool(instance.equiv_check) is True
        tools.assert_same_dag(source, instance.optim_dag)


class TestInputAndLogicalIdentity:
    def test_full_optimize_does_not_mutate_input(self, engine, tools):
        source = tools.to_dag(tools.circuit(2, [
            ("h", 0), ("h", 0), ("cx", 0, 1), ("rz", 0.5, 0), ("cx", 0, 1),
        ], phase=0.173))
        snapshot = tools.clone(source)
        result = engine.full_optimize(source, beam_width=4, max_depth=2)
        assert result is not source
        tools.assert_same_dag(snapshot, source)
        tools.assert_exact(snapshot, result)
        result.remove_all_ops_named("rz")
        tools.assert_same_dag(snapshot, source)

    def test_constructor_does_not_alias_output_to_input(self, optimizer_class, tools):
        source = tools.to_dag(tools.circuit(1, [("rz", 0.5, 0)]))
        snapshot = tools.clone(source)
        instance = optimizer_class(source)
        assert instance.optim_dag is not source
        instance.optim_dag.remove_all_ops_named("rz")
        tools.assert_same_dag(snapshot, source)

    def test_quantum_and_idle_classical_registers_are_preserved(self, engine, tools):
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
        left, right = QuantumRegister(2, "left"), QuantumRegister(2, "right")
        record = ClassicalRegister(3, "record")
        source = QuantumCircuit(left, right, record, name="logical-input")
        source.metadata = {"stage": "normalized", "case": "register-preservation"}
        source.h(left[1])
        source.h(left[1])
        source.cx(right[1], left[0])
        result = engine.full_optimize(tools.to_dag(source), max_depth=1)
        tools.assert_shape_preserved(source, result)
        tools.assert_exact(source, result)
        assert result.name == source.name
        assert result.metadata == source.metadata
        cx = tools.nodes(result, "cx")[0]
        assert tuple(result.find_bit(q).index for q in cx.qargs) == (3, 0)

    def test_optimizer_does_not_route_or_relabel_logical_qubits(self, engine, tools):
        source = tools.circuit(4, [("cx", 0, 3)])
        result = engine.full_optimize(tools.to_dag(source), max_depth=1)
        tools.assert_output(source, result, counts={"cx": 1}, size=1, depth=1)
        assert tuple(result.find_bit(q).index for q in tools.nodes(result, "cx")[0].qargs) == (0, 3)


class TestSemanticBoundaries:
    @pytest.mark.parametrize("ops,n", [
        ([("cx", 0, 1), ("rz", 0.7, 1), ("cx", 0, 1)], 2),
        ([("cx", 0, 1), ("x", 0), ("cx", 0, 1)], 2),
        ([("cx", 0, 1), ("cx", 1, 2), ("cx", 0, 1)], 3),
        ([("cx", 0, 1), ("h", 0), ("cx", 0, 1)], 2),
        ([("cx", 0, 1), ("h", 1), ("cx", 0, 1)], 2),
    ], ids=["RZ-on-target", "X-on-control", "CX-control-target-chain", "H-on-control", "H-on-target"])
    def test_noncommuting_operations_are_not_skipped(self, engine, tools, ops, n):
        source = tools.circuit(n, ops)
        result = engine.full_optimize(tools.to_dag(source), beam_width=4, max_depth=2)
        tools.assert_exact(source, result)
        tools.assert_same_dag(source, result)

    @pytest.mark.parametrize("method", ["greedy_optimize", "full_optimize"])
    @pytest.mark.parametrize("phase", [0.173, pi, -0.4])
    def test_preserves_exact_global_phase(self, engine, tools, method, phase):
        source = tools.circuit(2, [("h", 0), ("h", 0), ("rz", 0.2, 1), ("rz", 0.3, 1)], phase=phase)
        result = tools.run(engine, method, source)
        tools.assert_exact(source, result)

    @pytest.mark.parametrize("angles", [(pi, pi), (2 * pi, 2 * pi), (0.5, -0.5), (1e-6, 2e-6)])
    def test_rz_boundary_angles_are_not_rounded_or_phase_dropped(self, engine, tools, angles):
        source = tools.circuit(1, [("rz", a, 0) for a in angles])
        result = engine.full_optimize(tools.to_dag(source), max_depth=1)
        tools.assert_exact(source, result)
        assert result.size() <= 1
        # Do not demand retention of RZ(0): a future EXACT identity rewrite is OK.
        # RZ(2*pi) may only disappear if its global phase is compensated.

    def test_equiv_flag_means_up_to_phase_not_exact_matrix_equality(self, optimizer_class, tools, monkeypatch):
        source = tools.to_dag(tools.circuit(1, [("h", 0)]))
        phase_shifted = tools.to_dag(tools.circuit(1, [("h", 0)], phase=0.4))
        assert not np.allclose(tools.matrix(source), tools.matrix(phase_shifted), atol=1e-10, rtol=1e-10)
        # Fault injection only tests the reporting contract, not a real rewrite.
        monkeypatch.setattr(optimizer_class, "full_optimize", lambda self, dag: phase_shifted)
        instance = optimizer_class(source)
        assert bool(instance.equiv_check) is True  # Current source uses Operator.equiv.
        # Actual optimizer runs are checked independently for EXACT phase above.

    @pytest.mark.parametrize("method", ["greedy_optimize", "full_optimize"])
    def test_symbolic_angles_survive_low_level_optimization(self, engine, tools, method):
        from qiskit.circuit import Parameter
        alpha, beta = Parameter("alpha"), Parameter("beta")
        source = tools.circuit(2, [("rz", alpha, 0), ("cx", 0, 1), ("rz", beta, 0)])
        result = tools.run(engine, method, source)
        assert set(tools.from_dag(result).parameters) == {alpha, beta}
        tools.assert_symbolic_exact(source, result, [
            {alpha: 0.1, beta: 0.7}, {alpha: -0.5, beta: 1.4}, {alpha: pi, beta: -pi},
        ])
        # Constructor's numerical Operator check is only exercised after binding.


class TestSearchAndInputContract:
    @pytest.mark.parametrize("width,depth", [(0, 1), (-1, 1), (2, -1)])
    def test_invalid_bounds_raise_value_error_without_mutation(self, engine, tools, width, depth):
        source = tools.to_dag(tools.circuit(1, [("h", 0)]))
        snapshot = tools.clone(source)
        with pytest.raises(ValueError, match="Invalid beam width or search depth"):
            engine.full_optimize(source, beam_width=width, max_depth=depth)
        tools.assert_same_dag(snapshot, source)

    @pytest.mark.parametrize("width", [1, 2, 8])
    def test_small_beams_still_preserve_semantics_and_baseline(self, engine, tools, width):
        source = tools.circuit(2, [("cx", 0, 1), ("rz", 0.3, 0), ("x", 1), ("cx", 0, 1)])
        greedy = engine.greedy_optimize(tools.to_dag(source))
        result = engine.full_optimize(tools.to_dag(source), beam_width=width, max_depth=2)
        tools.assert_exact(source, result)
        assert tools.cost(result) <= tools.cost(greedy)

    @pytest.mark.parametrize("kind", [
        "z", "rx", "ry", "s", "t", "swap", "reset", "delay", "measure", "if_else", "open_control_cx",
    ])
    def test_rejects_non_normalized_or_nonunitary_input(self, engine, tools, kind):
        from qiskit.circuit.library import CXGate
        source = tools.circuit(2, [("h", 0), ("h", 0)], n_clbits=1)
        if kind in {"z", "s", "t", "reset"}:
            getattr(source, kind)(0)
        elif kind in {"rx", "ry"}:
            getattr(source, kind)(0.3, 0)
        elif kind == "swap":
            source.swap(0, 1)
        elif kind == "delay":
            source.delay(5, 0, unit="dt")
        elif kind == "measure":
            source.measure(0, 0)
        elif kind == "if_else":
            with source.if_test((source.clbits[0], True)):
                source.x(1)
        elif kind == "open_control_cx":
            source.append(CXGate(ctrl_state=0), [0, 1])
        else:
            raise AssertionError(f"Unknown fixture: {kind}")
        dag = tools.to_dag(source)
        snapshot = tools.clone(dag)
        with pytest.raises(ValueError, match="Unsupported operation"):
            engine.full_optimize(dag)
        tools.assert_same_dag(snapshot, dag)

    def test_repeated_calls_are_deterministic_for_fixed_settings(self, engine, tools):
        source = tools.circuit(3, [("cx", 0, 1), ("cx", 0, 2), ("cx", 0, 1)])
        first = engine.full_optimize(tools.to_dag(source), beam_width=4, max_depth=2)
        second = engine.full_optimize(tools.to_dag(source), beam_width=4, max_depth=2)
        tools.assert_exact(source, first)
        tools.assert_exact(source, second)
        tools.assert_same_dag(first, second)
