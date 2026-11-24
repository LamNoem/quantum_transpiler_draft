# Routing cost formula:
#
# C(A) = C_immediate(A) + FUTURE_WEIGHT * C_future(A)
#
# A: Candidate routing action (bridge or sequence of SWAPs).
#
# Immediate cost:
#     C_immediate(A) = 3                  if bridge
#     C_immediate(A) = 3 * num_swaps      if SWAP sequence
#
#     Counts additional CX gates introduced by the routing action.
#     The original logical CX is excluded because every candidate
#     must implement it.
#
# Future cost:
#     C_future(A) = (1/K) * sum(3 * (d[k] - 1)) for k = 1,...,K
#
#     K    = number of upcoming CX gates considered
#            (other ready CXs + LOOKAHEAD future CXs, if available).
#
#     d[k] = shortest physical distance between the operands of
#            upcoming CX gate k, AFTER applying action A to a
#            temporary copy of the current mapping.
#
#     Subtracting 1 ensures adjacent qubits contribute zero cost.
#     Multiplying by 3 estimates the additional CX overhead
#     associated with routing through SWAPs.
#
#     If K = 0, C_future(A) = 0.
#
# FUTURE_WEIGHT:
#     Controls the importance of future interactions relative
#     to the immediate routing overhead.
#
# Selection:
#     Choose the action A with the minimum C(A).
#
# Note:
#     All current SWAP candidates use the minimum number of SWAPs
#     required to make the selected CX executable. A bridge also
#     has the same immediate CX overhead as a single SWAP.
#
#     Therefore, the current heuristic effectively selects the
#     action that minimizes average future physical separation.
#
#     Future cost is an estimate, not an exact prediction of
#     future routing overhead, since subsequent routing actions
#     may change the mapping again.
import copy

import networkx as nx
from qiskit.dagcircuit import DAGCircuit
from qiskit.converters import circuit_to_dag
from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate

from general.log_config import logging
from itertools import islice

logger = logging.getLogger(__name__)


class Router:
    # ideas from Siraichi et al. (2018) and SABRE
    LOOKAHEAD = 6
    FUTURE_WEIGHT = 1.0
    MAX_SHORTEST_PATHS = 3
    

    def __init__(self, circuit: DAGCircuit, mapping: dict, target):

        self.swap_count = 0
        self.bridge_count = 0

        # Original logical DAG, kept unchanged for verification.
        self.orig_circuit = circuit

        # Working logical DAG. Remove operations as they are routed.
        self.remaining_dag = copy.deepcopy(circuit)

        # Preserve the initial mapping separately.
        # self.mapping changes whenever a SWAP is inserted.
        self.initial_mapping = mapping.copy()
        self.mapping = mapping.copy()

        self.hardware = copy.deepcopy(target)
        self.hardware_graph = self.hardware.physical_graph

        self.validate_mapping()

        # Cache shortest physical distances.
        self.distances = dict(
            nx.all_pairs_shortest_path_length(self.hardware_graph)
        )

        # Create an empty DAG with one wire per physical qubit.
        self.routed_circuit = circuit_to_dag(
            QuantumCircuit(
                self.hardware.num_qubits,
                len(self.orig_circuit.clbits)
            )
        )

        # Preserve the global phase accumulated during previous stages.
        self.routed_circuit.global_phase = self.orig_circuit.global_phase

        self.routing_history = [
            {
                "action": "initial",
                "physical_qubits": None,
                "mapping": self.mapping.copy(),
                "circuit_size": self.routed_circuit.size(),
                "dag": copy.deepcopy(self.routed_circuit)
            }
        ]

        # Execute routing.
        # Modifies self.routed_circuit and self.mapping directly.
        _,_ = self.route()

        # Verify CX count after routing.
        original_cx = self.orig_circuit.count_ops().get("cx", 0)
        routed_cx = self.routed_circuit.count_ops().get("cx", 0)

        expected_cx = (
            original_cx
            + 3 * self.swap_count
            + 3 * self.bridge_count
        )

        assert routed_cx == expected_cx, "Unexpected CX count after routing"
        expected_history_size = (
            1
            + len(self.orig_circuit.op_nodes()) # bridges and immediately ready nodes
            + self.swap_count
        )

        assert len(self.routing_history) == expected_history_size
        self.validate_mapping()

    def record_routing_step(self, action, physical_qubits):
        """
        Save the current mapping and routed physical DAG
        after committing a routing action.
        """
        self.routing_history.append({
            "action": action,
            "physical_qubits": physical_qubits,
            "mapping": self.mapping.copy(),
            "circuit_size": self.routed_circuit.size(),
            "dag": copy.deepcopy(self.routed_circuit)
        })

    def validate_mapping(self):
        if not nx.is_connected(self.hardware_graph):
            raise ValueError("Hardware graph must be connected")

        if set(self.mapping.keys()) != set(range(self.orig_circuit.num_qubits())):
            raise ValueError("Incomplete mapping")

        if len(set(self.mapping.values())) != len(self.mapping):
            raise ValueError("Mapping is not one-to-one")

        if not set(self.mapping.values()).issubset(self.hardware_graph.nodes):
            raise ValueError("Invalid physical qubit in mapping")
    
    def get_physical_indices(self, node):
        # Get integer indices of the logical qubits.
        log_qargs_index = [
            self.remaining_dag.find_bit(q).index
            for q in node.qargs
        ]

        # Convert logical indices into current physical indices.
        phys_qargs_index = [
            self.mapping[q]
            for q in log_qargs_index
        ]

        return phys_qargs_index

    def emit(self,node):
        # Find the current physical locations of the logical operands.
        phys_qargs_index = self.get_physical_indices(node)

        # Retrieve the Qubit objects belonging to the physical DAG.
        phys_qargs = [
            self.routed_circuit.qubits[p]
            for p in phys_qargs_index
        ]

        # Preserve classical operand indices, if applicable.
        cargs = [
            self.routed_circuit.clbits[
                self.remaining_dag.find_bit(c).index
            ]
            for c in node.cargs
        ]

        # Append the operation to the routed physical DAG.
        self.routed_circuit.apply_operation_back(
            node.op,
            qargs=phys_qargs,
            cargs=cargs
        )

        self.record_routing_step(
            node.op.name,
            tuple(phys_qargs_index)
        )
        

    def can_execute_directly(self, node):

        if node.op.name == "cx":

            control_phys, target_phys = self.get_physical_indices(node)

            # Check whether the two physical qubits are adjacent.
            return self.hardware_graph.has_edge(
                control_phys,
                target_phys
            )

        else:
                    # Barriers are directives, not physical interactions.
            if node.op.name == "barrier":
                return True

            # All single-qubit gates are assumed executable.
            if len(node.qargs) == 1:
                return True

            raise ValueError(f"Unsupported operation: {node.op.name}")

    def can_bridge(self, node):
        # Check whether shortest physical distance = 2.
        control_phys, target_phys = self.get_physical_indices(node)
        return self.distances[control_phys][target_phys]  == 2
   
    def insert_bridge(self,node, sequence):
        # Append four physical CX gates.
        # Do NOT change the logical-to-physical mapping.
        
        control_p, middle_p, target_p =  sequence

        # Verify that the bridge implements the intended logical CX.
        control_phys, target_phys = self.get_physical_indices(node)

        if control_p != control_phys or target_p != target_phys:
            raise ValueError("Bridge operands do not match logical CX")

        # Verify that both physical connections exist.
        if not self.hardware_graph.has_edge(control_p, middle_p):
            raise ValueError("Invalid bridge connection")

        if not self.hardware_graph.has_edge(middle_p, target_p):
            raise ValueError("Invalid bridge connection")

        # Physical qubit objects from the routed DAG
        control = self.routed_circuit.qubits[control_p]
        middle = self.routed_circuit.qubits[middle_p]
        target = self.routed_circuit.qubits[target_p]

        # Four-CX bridge decomposition
        self.routed_circuit.apply_operation_back(
            CXGate(), qargs=[control, middle]
        )

        self.routed_circuit.apply_operation_back(
            CXGate(), qargs=[middle, target]
        )

        self.routed_circuit.apply_operation_back(
            CXGate(), qargs=[control, middle]
        )

        self.routed_circuit.apply_operation_back(
            CXGate(), qargs=[middle, target]
        )

        self.bridge_count += 1
        self.record_routing_step(
            "bridge",
            (control_p, middle_p, target_p)
        )

    def generate_swap_sequences(self, node):
        """
        Generate candidate SWAP sequences along shortest paths.

        Each sequence makes the selected CX executable.
        All indices represent physical qubits.
        """

        control_phys, target_phys = self.get_physical_indices(node)

        paths = nx.all_shortest_paths(
            self.hardware_graph,
            source=control_phys,
            target=target_phys
        )

        swap_sequences = []

        # Limit the number of shortest paths considered.
        for path in islice(paths, self.MAX_SHORTEST_PATHS):

            # OPTION 1: Move target towards control.
            path_inv = path[::-1]
            swap_sequence = []

            # Stop once the target is adjacent to the control.
            for i in range(len(path_inv) - 2):
                swap_sequence.append(
                    (path_inv[i], path_inv[i + 1])
                )

            swap_sequences.append(swap_sequence)

            # OPTION 2: Move control towards target.
            swap_sequence = []

            for i in range(len(path) - 2):
                swap_sequence.append(
                    (path[i], path[i + 1])
                )

            swap_sequences.append(swap_sequence)

            # OPTION 3: Move both control and target towards each other.

            # Total number of SWAPs needed to make the operands adjacent.
            num_swaps = len(path) - 2

            # Consider every possible distribution of SWAPs between
            # the control and target, where both operands move at least once.
            for control_swaps in range(1, num_swaps):

                target_swaps = num_swaps - control_swaps

                swap_sequence = []

                # Move control towards target.
                for i in range(control_swaps):
                    swap_sequence.append(
                        (path[i], path[i + 1])
                    )

                # Move target towards control.
                for i in range(target_swaps):
                    swap_sequence.append(
                        (path_inv[i], path_inv[i + 1])
                    )

                swap_sequences.append(swap_sequence)

        return swap_sequences
    
    def generate_bridge_sequences(self, node):
        """
        Generate possible three-qubit bridge paths.

        Each sequence is:
            (physical control, physical middle, physical target)
        """

        control_phys, target_phys = self.get_physical_indices(node)

        paths = nx.all_shortest_paths(
            self.hardware_graph,
            source=control_phys,
            target=target_phys
        )

        bridge_sequences = []

        for path in paths:

            # A four-CX bridge requires exactly three physical nodes.
            if len(path) == 3:

                control_p, middle_p, target_p = path

                bridge_sequences.append(
                    (control_p, middle_p, target_p)
                )

        return bridge_sequences

    def simulate_swaps(self, swap_sequence):
        """
        Return the hypothetical mapping after a sequence of SWAPs.
        Do not modify the actual mapping or routed circuit.
        """

        trial_mapping = self.mapping.copy()

        for p1, p2 in swap_sequence:

            # Find logical qubits occupying the physical locations
            # and exchange their recorded locations.
            for logical_q in trial_mapping:

                physical_q = trial_mapping[logical_q]

                if physical_q == p1:
                    trial_mapping[logical_q] = p2

                elif physical_q == p2:
                    trial_mapping[logical_q] = p1

        return trial_mapping
    
    def score_routing_action(self, action, future_gates):
        """
        Score a candidate routing action using:
            1. Immediate additional CX-equivalent gate count.
            2. Estimated average routing cost of future CX gates.

        Lower scores are better.
        """

        action_type, sequence = action

        # -----------------------------------------------
        # 1. Determine the resulting mapping and immediate
        #    routing overhead.
        # -----------------------------------------------

        if action_type == "bridge":

            # A bridge does not change the mapping.
            trial_mapping = self.mapping.copy()

            # Four CX gates replace one original CX.
            immediate_cost = 3

        elif action_type == "swap":

            # Simulate the entire SWAP sequence.
            trial_mapping = self.simulate_swaps(sequence)

            # Each SWAP requires three CX-equivalent gates.
            immediate_cost = 3 * len(sequence)

        else:
            raise ValueError("Unknown routing action")

        # -----------------------------------------------
        # 2. Evaluate future CX interactions using the
        #    hypothetical mapping.
        # -----------------------------------------------

        total_future_cost = 0

        for node in future_gates:

            control, target = node.qargs

            # Get the original logical indices.
            control_log = self.remaining_dag.find_bit(control).index
            target_log = self.remaining_dag.find_bit(target).index

            # Get physical locations under the TRIAL mapping.
            control_phys = trial_mapping[control_log]
            target_phys = trial_mapping[target_log]

            # Shortest physical distance between the operands.
            distance = self.distances[control_phys][target_phys]

            # Estimate additional CX gates needed for routing.
            gate_cost = 3 * (distance - 1)

            total_future_cost += gate_cost

        # -----------------------------------------------
        # 3. Calculate average future routing cost.
        # -----------------------------------------------

        if len(future_gates) > 0:
            future_cost = total_future_cost / len(future_gates)
        else:
            future_cost = 0

        # -----------------------------------------------
        # 4. Combine immediate and future costs.
        # -----------------------------------------------

        total_cost = (
            immediate_cost
            + self.FUTURE_WEIGHT * future_cost
        )

        return total_cost

    def commit_swaps(self, swap_sequence):
        """
        Append the physical CX decomposition of each SWAP
        and update the logical-to-physical mapping.
        """

        for A, B in swap_sequence:
            
            # Ensure this is a legal physical SWAP.
            if not self.hardware_graph.has_edge(A, B):
                raise ValueError("Invalid physical SWAP")

            A_q = self.routed_circuit.qubits[A]
            B_q = self.routed_circuit.qubits[B]

            # SWAP(A, B) = CX(A, B), CX(B, A), CX(A, B)
            self.routed_circuit.apply_operation_back(
                CXGate(), qargs=[A_q, B_q]
            )

            self.routed_circuit.apply_operation_back(
                CXGate(), qargs=[B_q, A_q]
            )

            self.routed_circuit.apply_operation_back(
                CXGate(), qargs=[A_q, B_q]
            )

            # Identify the logical qubits occupying A and B.
            log_that_has_A = None
            log_that_has_B = None

            for log, phys in self.mapping.items():

                if phys == A:
                    log_that_has_A = log

                if phys == B:
                    log_that_has_B = log

            

            # Exchange their recorded physical locations.
            # An unused physical location has no logical qubit to update.
            if log_that_has_A is not None:
                self.mapping[log_that_has_A] = B

            if log_that_has_B is not None:
                self.mapping[log_that_has_B] = A

            self.swap_count +=1
            self.record_routing_step("swap", (A, B))

                    
                

    def get_future_cx(self, remaining_dag):
        """
        Return the next 'lookahead' CX operations
        that are not already in the front layer.
        """
        if self.LOOKAHEAD <= 0:
            return []

        front_layer = remaining_dag.front_layer()
        future_cx = []

        for node in remaining_dag.topological_op_nodes():

            # Ready gates are considered separately.
            if node in front_layer:
                continue

            # Only CX gates matter for connectivity scoring.
            if node.op.name != "cx":
                continue

            future_cx.append(node)

            if len(future_cx) == self.LOOKAHEAD:
                break

        return future_cx

    def route(self):

        while self.remaining_dag.op_nodes():

            ready_nodes = self.remaining_dag.front_layer()
            made_progress = False

            # -----------------------------------------------
            # 1. Emit all directly executable ready operations.
            # -----------------------------------------------

            for node in ready_nodes:

                if self.can_execute_directly(node):

                    self.emit(node)

                    self.remaining_dag.remove_op_node(node)

                    made_progress = True

            # Refresh the front layer if operations were emitted.
            if made_progress:
                continue

            # -----------------------------------------------
            # 2. No directly executable operations remain.
            #    Select a blocked ready CX.
            # -----------------------------------------------

            node = self.remaining_dag.front_layer()[0]

            actions = []

            # -----------------------------------------------
            # 3. Generate possible routing actions.
            # -----------------------------------------------

            if self.can_bridge(node):

                bridge_sequences = self.generate_bridge_sequences(node)

                for sequence in bridge_sequences:
                    actions.append(("bridge", sequence))

            swap_sequences = self.generate_swap_sequences(node)

            for sequence in swap_sequences:
                actions.append(("swap", sequence))

            if not actions:
                raise ValueError("No valid routing actions found")

            # -----------------------------------------------
            # 4. Score each candidate action.
            # -----------------------------------------------

            future_gates = self.get_future_cx(self.remaining_dag)
            other_ready_cx = [
                ready_node
                for ready_node in self.remaining_dag.front_layer()
                if ready_node.op.name == "cx" and ready_node != node
            ]

            future_gates = other_ready_cx + future_gates

            best_action = min(
                actions,
                key=lambda action: self.score_routing_action(
                    action,
                    future_gates
                )
            )

            action_type, sequence = best_action

            # -----------------------------------------------
            # 5. Commit the selected routing action.
            # -----------------------------------------------

            if action_type == "bridge":

                # Emit four physical CXs.
                # Do not modify the mapping.
                self.insert_bridge(node, sequence)

            else:

                # Emit physical SWAPs and update the mapping.
                self.commit_swaps(sequence)

                # The original CX should now be executable.
                if not self.can_execute_directly(node):
                    raise ValueError("SWAP sequence failed to route CX")

                self.emit(node)

            # -----------------------------------------------
            # 6. Remove the implemented logical operation.
            # -----------------------------------------------

            self.remaining_dag.remove_op_node(node)

        return self.routed_circuit, self.mapping.copy()