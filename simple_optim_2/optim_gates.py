import qiskit.qasm3
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGOpNode
from math import pi
from qiskit import QuantumCircuit
from general.log_config import logging
from qiskit.circuit.library import HGate, XGate, RZGate, CXGate, RXGate, RYGate, ZGate, SGate, SdgGate, TGate, TdgGate, UGate, Barrier
import networkx as nx
import copy
from collections import deque
from qiskit.quantum_info import Operator


logger = logging.getLogger(__name__)

class OptimGates:

    ITER_LIMIT = 10

    def __init__(self, norm_dag):
        self.orig_norm_dag = norm_dag
        self.orig_gate_count = len(
                    self.orig_norm_dag.op_nodes(include_directives=False)
                )
        self.orig_depth = self.orig_norm_dag.depth()
                

        self.optim_dag = self.full_optimize(circuit_to_dag(dag_to_circuit(norm_dag)))
        self.new_gate_count = len(
            self.optim_dag.op_nodes(include_directives=False)
        )
        self.new_depth = self.optim_dag.depth()
        self.equiv_check = (Operator(dag_to_circuit(self.orig_norm_dag))).equiv(Operator(dag_to_circuit(self.optim_dag)))



    def full_optimize(self, norm_dag, beam_width=8, max_depth=5):
        """
         Greedy optimization -> beam search -> greedy optimization.

        For each legal commutation, branch into:
            A. Commute, but perform no local optimization.
            B. Commute, then apply ONE local optimization.

        If multiple local optimizations are available,
        create a separate branch for each.

        Currently supports unconditional H, X, RZ, CX.

                            1. Initial greedy optimization
                                Remove obvious redundancies

                            2. Beam search — repeat up to max_depth
                                For every legal commutation, explore:
                        Branch A                            Branch B
                        Commute only                        Commute + one local rewrite
                        Score, deduplicate, retain best beam_width states

                            3. Final greedy optimization
                    Clean up remaining adjacent cancellations and merge  
        """
        logger.info("full optimize begin")
        if beam_width < 1 or max_depth < 0:
            raise ValueError("Invalid beam width or search depth")

        allowed_gates = {"h", "x", "rz", "cx"}
        directives = {"barrier"}

        # Keep the first implementation restricted to the
        # unitary gate set used by your normalized circuits.
        if any(
            node.op.name not in allowed_gates|directives or node.cargs
            for node in norm_dag.op_nodes()
        ):
            raise ValueError("Unsupported operation in full_optimize")

        # -------------------------------------------------
        # Helpers
        # -------------------------------------------------

        def clone(dag):
            return circuit_to_dag(dag_to_circuit(dag))

        def cost(dag):
            # Prioritize CX count, then total gates, then depth.
            return (
                dag.count_ops().get("cx", 0),
                len(
                    dag.op_nodes(include_directives=False)
                ),
                dag.depth()
            )

        def circuit_key(dag):
            return (
                dag.num_qubits(),
                tuple(
                    (
                        node.op.name,
                        tuple(
                            dag.find_bit(q).index
                            for q in node.qargs
                        ),
                        tuple(str(p) for p in node.op.params)
                    )
                    for node in dag.topological_op_nodes()
                )
            )

        def commute(a, b):
            """
            Conservative commutation rules for the
            normalized gate set.
            """
            # Barriers must remain fixed relative to operations
            # on their qubit wires.
            if a.op.name == "barrier" or b.op.name == "barrier":
                return False
            
            # Disjoint-qubit operations are already
            # independent in the DAG.
            if not set(a.qargs).intersection(b.qargs):
                return False

            x = a.op.name
            y = b.op.name

            # Identical gate names on identical operands
            # commute (including RZ with different angles).
            if x == y and a.qargs == b.qargs:
                return True

            # CX gates commute when they share a control,
            # or when they share a target.
            if x == y == "cx":
                return (
                    a.qargs[0] == b.qargs[0]
                    or a.qargs[1] == b.qargs[1]
                )

            # Handle a CX together with RZ or X.
            if x == "cx" and y in {"rz", "x"}:
                cx, one = a, b

            elif y == "cx" and x in {"rz", "x"}:
                cx, one = b, a

            else:
                return False

            if one.op.name == "rz":
                # RZ on the control commutes with CX.
                return one.qargs[0] == cx.qargs[0]

            # X on the target commutes with CX.
            return one.qargs[0] == cx.qargs[1]

        def legal_moves(dag):
            nodes = list(dag.topological_op_nodes())

            # Use Qiskit's DAG node IDs, not Python object IDs
            positions = {
                node._node_id: i
                for i, node in enumerate(nodes)
            }

            moves = []

            for node in nodes:
                for succ in dag.op_successors(node):

                    if not commute(node, succ):
                        continue

                    # Check for intermediate dependency paths
                    descendants = {
                        n._node_id for n in dag.descendants(node)
                    }
                    ancestors = {
                        n._node_id for n in dag.ancestors(succ)
                    }

                    if descendants & ancestors:
                        continue

                    moves.append((
                        positions[node._node_id],
                        positions[succ._node_id]
                    ))

            return moves

        def local_rewrites(dag, moved_nodes):
            """
            Find optimizations involving the swapped gates
            or their immediate predecessors.

            Return pairs of operation indices.
            """

            relevant = list(moved_nodes)

            # A commutation may create a new adjacent pair
            # immediately before either moved gate.
            for node in moved_nodes:
                relevant.extend(dag.op_predecessors(node))

            positions = {
                n._node_id: i
                for i, n in enumerate(dag.topological_op_nodes())
            }

            rewrites = set()

            for node in relevant:
                # dont consider directives
                if node.op.name not in allowed_gates:
                    continue

                succ = self.find_doubled_op(dag, node)

                if succ is None:
                    continue

                if node.op.name != succ.op.name:
                    continue

                rewrites.add((
                    positions[node._node_id],
                    positions[succ._node_id]
                ))

            return sorted(rewrites)

        def apply_one_rewrite(dag, rewrite):
            """
            Apply exactly one inverse cancellation
            or one adjacent RZ merge.
            """

            nodes = list(dag.topological_op_nodes())

            node = nodes[rewrite[0]]
            succ = nodes[rewrite[1]]

            if node.op.name == "rz":
                theta = (
                    node.op.params[0]
                    + succ.op.params[0]
                )

                dag.substitute_node(
                    node,
                    RZGate(theta),
                    inplace=True
                )
                dag.remove_op_node(succ)

            else:
                # HH, XX, CX-CX
                dag.remove_op_node(succ)
                dag.remove_op_node(node)

        # -------------------------------------------------
        # Stage 1: Initial greedy optimization
        # -------------------------------------------------

        initial = self.greedy_optimize(clone(norm_dag))

        best_dag = initial
        best_cost = cost(initial)

        beam = [initial]

        # Remember states actually visited, not merely
        # generated and discarded by beam selection.
        visited = set()

        # Preserve retained states from earlier depths
        # for the final greedy comparison.
        finalists = [initial]

        # -------------------------------------------------
        # Stage 2: Beam search
        # -------------------------------------------------
        logger.info(f"starting beam search for optim, not logging best sequence yet")
        for _ in range(max_depth):

            # Deduplicate candidates within this depth.
            candidates = {}

            for dag in beam:

                parent_key = circuit_key(dag)

                if parent_key in visited:
                    continue

                visited.add(parent_key)

                # Find every legal adjacent commutation.
                moves = legal_moves(dag)
                print("Current circuit:")
                print(dag_to_circuit(dag).draw())
                print("Legal moves:", moves)

                for i, j in moves:

                    # Independent copy for this commutation.
                    trial = clone(dag)

                    nodes = list(trial.topological_op_nodes())
                    first = nodes[i]
                    second = nodes[j]

                    # Perform the selected commutation.
                    trial.swap_nodes(first, second)

                    # BRANCH A:
                    # Keep the commuted circuit unchanged.
                    branches = [trial]

                    # BRANCH B:
                    # Apply one possible local optimization.
                    # Separate branch for each possible rewrite.
                    rewrites = local_rewrites(
                        trial, (first, second)
                    )

                    for rewrite in rewrites:
                        variant = clone(trial)

                        apply_one_rewrite(variant, rewrite)

                        branches.append(variant)

                    # Evaluate every generated branch.
                    for branch in branches:

                        key = circuit_key(branch)

                        if key in visited or key in candidates:
                            continue

                        score = cost(branch)

                        candidates[key] = (score, branch)

                        if score < best_cost:
                            best_cost = score
                            best_dag = branch

            if not candidates:
                break

            # Retain only the best beam_width states.
            ranked = sorted(
                candidates.values(),
                key=lambda item: item[0]
            )

            beam = [
                dag
                for score, dag in ranked[:beam_width]
            ]

            finalists.extend(beam)

        # -------------------------------------------------
        # Stage 3: Final greedy optimization
        # -------------------------------------------------

        # Also consider the best state encountered at any
        # intermediate search depth.
        finalists.append(best_dag)

        # Finish every retained candidate greedily,
        # then select the cheapest final circuit.
        results = [
            self.greedy_optimize(clone(dag))
            for dag in finalists
        ]

        logger.info("full optimize end: not all actions are logged in this function needs to be fixed")
        return min(results, key=cost)


    def greedy_optimize(self, norm_dag):
        """
        Worklist-based optimization:
        - Cancel HH, XX, CX-CX
        - Merge adjacent RZ rotations
        - Recheck only locally affected gates
        """
        logger.info("greedy optimize begin")
        # Initially, every gate needs to be checked
        worklist = deque(norm_dag.topological_op_nodes())

        # Track removed nodes still referenced by the queue
        removed = set()

        while worklist:
            node = worklist.popleft()

            # Skip nodes already removed from the DAG
            if node._node_id in removed:
                continue

            # Retrieve the current version of this node from the DAG.
            # A queued DAGOpNode may hold outdated gate parameters
            # after an in-place substitution.
            node = norm_dag.node(node._node_id)

            if not isinstance(node.op, (HGate, XGate, CXGate, RZGate)):
                continue

            succ = self.find_doubled_op(norm_dag, node)

            if succ is None:
                continue

            # Both gates must be of the same type
            if type(node.op) is not type(succ.op):
                continue

            # Save the predecessors BEFORE modifying the DAG
            predecessors = list(norm_dag.op_predecessors(node))

            # CASE 1: Inverse cancellation
            if isinstance(node.op, (HGate, XGate, CXGate)):

                norm_dag.remove_op_node(succ)
                norm_dag.remove_op_node(node)

                logger.info(f"Inverse cancellation of {node.op} with nodes {node._node_id} and {succ._node_id}")
                removed.add(node._node_id)
                removed.add(succ._node_id)
                

                # Removal may create new adjacent pairs
                worklist.extend(predecessors)

            # CASE 2: RZ merging
            elif isinstance(node.op, RZGate):

                theta = node.op.params[0] + succ.op.params[0]

                logger.info(f"RZ merge of {node.op} with nodes {node._node_id} and {succ._node_id}")

                norm_dag.remove_op_node(succ)
                removed.add(succ._node_id)

                # Keep the existing node in the DAG
                merged_node = norm_dag.substitute_node(
                    node, RZGate(theta), inplace=True
                )

                # Check for more RZ gates on either side
                worklist.append(merged_node)
                worklist.extend(predecessors)

        logger.info("greedy optimize end")
        return norm_dag

    def find_doubled_op(self,norm_dag,node):
        #       CX1    CX2
        # q0: ──●──────●──
        #       │      │
        # q1: ──⊕──────⊕──
        # e.g CX1 - CX2 gives edges:
        # [
        #     (CX1, CX2, q0),
        #     (CX1, CX2, q1)
        # ] and passes of CX2 chosen as successor
        #       CX1     H     CX2
        # q0: ──●──────H──────●──
        #       │             │
        # q1: ──⊕────────────⊕─
        # e.g CX1 H CX2 gives edges
        # [
        #     (CX1, H, q0),
        #     (CX1, CX2, q1)
        # ] and fails if CX2 chosen as successor
        # Outgoing edges identified by their qubit
        # and destination DAG node ID
        outgoing = {
            (wire, dest._node_id)
            for _, dest, wire in norm_dag.edges(node)
        }

        for succ in norm_dag.op_successors(node):

            # Must operate on the same ordered qubits
            if succ.qargs != node.qargs:
                continue

            # Every qubit must lead directly to this successor
            adjacent = all(
                (q, succ._node_id) in outgoing
                for q in node.qargs
            )

            if adjacent:
                return succ

        return None
        


    def inverse_cancellation(self, norm_dag):
        """
        Cancel adjacent inverse gates (HH, XX, CX-CX)
        """
        optim_flag = False
        while True: 
            cancelled = False
            for node in norm_dag.op_nodes():
                doubled_succ = self.find_doubled_op(norm_dag,node)
                if doubled_succ is not None:

                    if isinstance(doubled_succ.op, (HGate, XGate, CXGate)):
                        if isinstance(node.op, (HGate, XGate, CXGate)) and node.op == doubled_succ.op:
                            cancelled = True
                            optim_flag = True
                            norm_dag.remove_op_node(doubled_succ)
                            norm_dag.remove_op_node(node)
                            break

            if not cancelled:
                break

        return optim_flag

    def merge_adjacent_RZ(self, norm_dag):
        optim_flag = False
        while True:
            merged = False
            for node in norm_dag.op_nodes():
                doubled_succ = self.find_doubled_op(norm_dag,node)
                if doubled_succ is not None:

                    if isinstance(doubled_succ.op, (RZGate)):
                        if isinstance(node.op, (RZGate)):
                            merged = True
                            optim_flag = True
                            norm_dag.substitute_node(node, RZGate(node.op.params[0]+doubled_succ.op.params[0]))
                            norm_dag.remove_op_node(doubled_succ)
                            break
            if not merged:
                break

        return optim_flag