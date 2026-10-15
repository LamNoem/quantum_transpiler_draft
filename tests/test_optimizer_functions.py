"""1. Individual function contracts and targeted regression tests.

Nested helpers inside full_optimize are not public methods: they are exercised
through full_optimize, not extracted with inspection or reimplemented here.
"""
import pytest


class TestFindDoubledOp:
    @pytest.mark.parametrize("name,ops,qubits", [
        ("h", [("h", 0), ("h", 0)], (0,)),
        ("x", [("x", 1), ("x", 1)], (1,)),
        ("cx", [("cx", 0, 1), ("cx", 0, 1)], (0, 1)),
        ("rz", [("rz", 0.25, 0), ("rz", -0.75, 0)], (0,)),
    ], ids=["HH", "XX", "CX-CX", "different-RZ-angles"])
    def test_finds_adjacent_pair(self, engine, tools, name, ops, qubits):
        dag = tools.to_dag(tools.circuit(2, ops))
        first, second = tools.nodes(dag, name, qubits)
        found = engine.find_doubled_op(dag, first)
        assert found is not None
        # Separate iterators can return different Python wrappers for one node.
        assert found._node_id == second._node_id

    def test_helper_guarantees_adjacency_not_gate_equality(self, engine, tools):
        dag = tools.to_dag(tools.circuit(1, [("h", 0), ("x", 0)]))
        found = engine.find_doubled_op(dag, tools.nodes(dag, "h")[0])
        assert found is not None and found.op.name == "x"

    def test_no_operation_after_last_gate(self, engine, tools):
        dag = tools.to_dag(tools.circuit(1, [("h", 0)]))
        assert engine.find_doubled_op(dag, tools.nodes(dag)[0]) is None

    def test_disjoint_instruction_does_not_break_wire_adjacency(self, engine, tools):
        dag = tools.to_dag(tools.circuit(2, [("h", 0), ("x", 1), ("h", 0)]))
        first, last = tools.nodes(dag, "h")
        found = engine.find_doubled_op(dag, first)
        assert found is not None and found._node_id == last._node_id

    @pytest.mark.parametrize("blocked_qubit", [0, 1])
    def test_cx_must_be_adjacent_on_both_wires(self, engine, tools, blocked_qubit):
        dag = tools.to_dag(tools.circuit(2, [
            ("cx", 0, 1), ("h", blocked_qubit), ("cx", 0, 1),
        ]))
        assert engine.find_doubled_op(dag, tools.nodes(dag, "cx")[0]) is None

    def test_reversed_cx_operands_are_not_same_operands(self, engine, tools):
        dag = tools.to_dag(tools.circuit(2, [("cx", 0, 1), ("cx", 1, 0)]))
        assert engine.find_doubled_op(dag, tools.nodes(dag, "cx")[0]) is None

    def test_two_different_successors_are_not_one_candidate(self, engine, tools):
        dag = tools.to_dag(tools.circuit(2, [("cx", 0, 1), ("h", 0), ("x", 1)]))
        assert engine.find_doubled_op(dag, tools.nodes(dag, "cx")[0]) is None

    def test_repeated_iterator_calls_use_dag_identity(self, engine, tools):
        dag = tools.to_dag(tools.circuit(2, [("cx", 0, 1), ("cx", 0, 1)]))
        for _ in range(5):
            first, second = tools.nodes(dag, "cx")
            found = engine.find_doubled_op(dag, first)
            assert found is not None and found._node_id == second._node_id

    def test_detection_after_a_manual_legal_commutation(self, engine, tools):
        dag = tools.to_dag(tools.circuit(2, [
            ("cx", 0, 1), ("rz", 0.5, 0), ("cx", 0, 1),
        ]))
        first, last = tools.nodes(dag, "cx")
        middle = tools.nodes(dag, "rz")[0]
        dag.swap_nodes(first, middle)
        found = engine.find_doubled_op(dag, first)
        assert found is not None and found._node_id == last._node_id


class TestInverseCancellation:
    @pytest.mark.parametrize("op", [("h", 0), ("x", 0), ("cx", 0, 1)], ids=["H", "X", "CX"])
    @pytest.mark.parametrize("length", [1, 2, 3, 12])
    def test_chain_and_change_flag(self, engine, tools, op, length):
        qc = tools.circuit(2, [op] * length)
        dag = tools.to_dag(qc)
        changed = engine.inverse_cancellation(dag)
        assert changed is (length >= 2)
        assert dag.size() == length % 2
        tools.assert_exact(qc, dag)
        assert engine.inverse_cancellation(dag) is False

    @pytest.mark.parametrize("ops", [
        [], [("h", 0), ("x", 0)],
        [("cx", 0, 1), ("cx", 1, 0)],
        [("h", 0), ("h", 1)],
    ], ids=["empty", "H-not-X", "reversed-CX", "different-wires"])
    def test_no_rewrite_returns_false(self, engine, tools, ops):
        qc = tools.circuit(2, ops)
        dag = tools.to_dag(qc)
        assert engine.inverse_cancellation(dag) is False
        tools.assert_same_dag(qc, dag)

    def test_does_not_also_merge_rz(self, engine, tools):
        dag = tools.to_dag(tools.circuit(1, [("rz", 0.2, 0), ("rz", 0.3, 0)]))
        assert engine.inverse_cancellation(dag) is False
        assert dag.size() == 2

    def test_cancellation_exposes_another_pair(self, engine, tools):
        qc = tools.circuit(2, [("h", 0), ("cx", 0, 1), ("cx", 0, 1), ("h", 0)])
        dag = tools.to_dag(qc)
        assert engine.inverse_cancellation(dag) is True
        tools.assert_output(qc, dag, counts={}, size=0, depth=0)


class TestMergeAdjacentRZ:
    @pytest.mark.parametrize("angles", [(0.2, 0.3), (-0.2, 0.8), (0.2, 0.3, 0.4), (0.5, -0.5)])
    def test_sum_and_change_flag(self, engine, tools, angles):
        qc = tools.circuit(1, [("rz", a, 0) for a in angles])
        dag = tools.to_dag(qc)
        assert engine.merge_adjacent_RZ(dag) is True
        nodes = tools.nodes(dag, "rz")
        assert len(nodes) == 1
        assert float(nodes[0].op.params[0]) == pytest.approx(sum(angles))
        tools.assert_exact(qc, dag)
        assert engine.merge_adjacent_RZ(dag) is False

    @pytest.mark.parametrize("ops", [
        [], [("rz", 0.2, 0)],
        [("rz", 0.2, 0), ("h", 0), ("rz", 0.3, 0)],
        [("rz", 0.2, 0), ("rz", 0.3, 1)],
    ], ids=["empty", "single-RZ", "intervening-H", "different-wires"])
    def test_no_merge_returns_false(self, engine, tools, ops):
        qc = tools.circuit(2, ops)
        dag = tools.to_dag(qc)
        assert engine.merge_adjacent_RZ(dag) is False
        tools.assert_same_dag(qc, dag)

    def test_does_not_also_cancel_hh(self, engine, tools):
        dag = tools.to_dag(tools.circuit(1, [("h", 0), ("h", 0)]))
        assert engine.merge_adjacent_RZ(dag) is False
        assert dag.size() == 2

    def test_symbolic_sum(self, engine, tools):
        from qiskit.circuit import Parameter
        alpha, beta = Parameter("alpha"), Parameter("beta")
        qc = tools.circuit(1, [("rz", alpha, 0), ("rz", beta, 0)])
        dag = tools.to_dag(qc)
        assert engine.merge_adjacent_RZ(dag) is True
        assert len(tools.nodes(dag, "rz")) == 1
        assert set(tools.from_dag(dag).parameters) == {alpha, beta}
        tools.assert_symbolic_exact(qc, dag, [
            {alpha: 0.2, beta: -0.7}, {alpha: -1.4, beta: 0.8}, {alpha: 0.0, beta: 0.0},
        ])


class TestGreedyOptimize:
    def test_adjacent_cx_after_rz_regression(self, engine, tools):
        qc = tools.circuit(2, [("rz", 0.5, 0), ("cx", 0, 1), ("cx", 0, 1)])
        dag = tools.to_dag(qc)
        result = engine.greedy_optimize(dag)
        assert result is dag, "This pass is documented/implemented as in-place"
        tools.assert_output(qc, result, counts={"rz": 1}, size=1, depth=1)

    def test_rechecks_predecessors_after_removal(self, engine, tools):
        qc = tools.circuit(2, [
            ("rz", 0.2, 0), ("h", 0), ("cx", 0, 1),
            ("cx", 0, 1), ("h", 0), ("rz", 0.3, 0),
        ])
        result = engine.greedy_optimize(tools.to_dag(qc))
        tools.assert_output(qc, result, counts={"rz": 1}, size=1, depth=1)
        assert float(tools.nodes(result, "rz")[0].op.params[0]) == pytest.approx(0.5)

    def test_stale_worklist_entries_do_not_crash(self, engine, tools):
        qc = tools.circuit(2, [("h", 0), ("h", 0), ("x", 1), ("x", 1)] * 20)
        result = engine.greedy_optimize(tools.to_dag(qc))
        tools.assert_output(qc, result, counts={}, size=0, depth=0)

    def test_rz_chain_does_not_leave_stale_parameters(self, engine, tools):
        qc = tools.circuit(1, [("rz", 0.125, 0)] * 24)
        result = engine.greedy_optimize(tools.to_dag(qc))
        tools.assert_output(qc, result, counts={"rz": 1}, size=1, depth=1)
        assert float(tools.nodes(result, "rz")[0].op.params[0]) == pytest.approx(3.0)

    @pytest.mark.parametrize("gate_name", ["h", "x", "cx"])
    def test_mutable_and_singleton_gate_instances_still_cancel(self, engine, tools, gate_name):
        from qiskit.circuit.library import HGate, XGate, CXGate
        gate = {"h": HGate, "x": XGate, "cx": CXGate}[gate_name]()
        qc = tools.circuit(2)
        qubits = [0, 1] if gate_name == "cx" else [0]
        qc.append(gate, qubits)
        qc.append(gate.to_mutable(), qubits)
        # Same quantum operation; exact Python implementation classes need not match.
        result = engine.greedy_optimize(tools.to_dag(qc))
        tools.assert_output(qc, result, counts={}, size=0, depth=0)

    def test_second_greedy_run_is_a_fixed_point(self, engine, tools):
        qc = tools.circuit(2, [("h", 0), ("h", 0), ("rz", 0.2, 1), ("rz", 0.3, 1)])
        once = engine.greedy_optimize(tools.to_dag(qc))
        snapshot = tools.clone(once)
        twice = engine.greedy_optimize(once)
        tools.assert_same_dag(snapshot, twice)


class TestFullOptimizeFunction:
    def test_depth_zero_is_greedy_only(self, engine, tools):
        qc = tools.circuit(2, [("cx", 0, 1), ("rz", 0.5, 0), ("cx", 0, 1)])
        greedy = engine.greedy_optimize(tools.to_dag(qc))
        full = engine.full_optimize(tools.to_dag(qc), beam_width=2, max_depth=0)
        tools.assert_same_dag(greedy, full)
        assert full.count_ops().get("cx", 0) == 2

    def test_one_search_step_unlocks_a_cancellation(self, engine, tools):
        qc = tools.circuit(2, [("cx", 0, 1), ("rz", 0.5, 0), ("cx", 0, 1)])
        result = engine.full_optimize(tools.to_dag(qc), beam_width=2, max_depth=1)
        tools.assert_output(qc, result, counts={"rz": 1}, size=1, depth=1)

    def test_empty_circuit_returns_a_dag(self, engine, tools):
        qc = tools.circuit(3)
        result = engine.full_optimize(tools.to_dag(qc))
        tools.assert_output(qc, result, counts={}, size=0, depth=0)


class TestConstructorFunction:
    def test_calls_full_optimize_on_an_independent_dag(self, optimizer_class, tools, monkeypatch):
        source = tools.to_dag(tools.circuit(1, [("h", 0)]))
        received = []

        def identity_full(self, dag, *args, **kwargs):
            received.append(dag)
            return dag

        monkeypatch.setattr(optimizer_class, "full_optimize", identity_full)
        instance = optimizer_class(source)
        assert len(received) == 1
        assert received[0] is not source
        assert isinstance(instance.orig_norm_dag, tools.DAGCircuit)
        assert isinstance(instance.optim_dag, tools.DAGCircuit)
        tools.assert_same_dag(source, instance.orig_norm_dag)

    @pytest.mark.parametrize("return_wrong_unitary", [False, True], ids=["equivalent", "not-equivalent"])
    def test_equivalence_flag_is_computed_not_hardcoded(
        self, optimizer_class, tools, monkeypatch, return_wrong_unitary
    ):
        import numpy as np
        source = tools.to_dag(tools.circuit(1, [("h", 0)]))
        replacement = tools.to_dag(tools.circuit(1, [("x" if return_wrong_unitary else "h", 0)]))
        monkeypatch.setattr(optimizer_class, "full_optimize", lambda self, dag: replacement)
        instance = optimizer_class(source)
        assert isinstance(instance.equiv_check, (bool, np.bool_))
        assert bool(instance.equiv_check) is (not return_wrong_unitary)
