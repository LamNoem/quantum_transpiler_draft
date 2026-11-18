import copy
from itertools import permutations

import networkx as nx
import numpy as np
from qiskit.dagcircuit import DAGCircuit
from qiskit import QuantumCircuit

from general.log_config import logging
from parser_0.input_target import Target

logger = logging.getLogger(__name__)


class Router:
    # ideas from Siraichi et al. (2018) and SABRE
    LOOKAHEAD = 6

    def __init__(self,circuit: DAGCircuit, mapping: dict, interact_matrix):
        self.orig_circuit = circuit
        self.mapping = mapping
        self.interact_matrix = interact_matrix
        self.routed_circuit = None
        self.physical_dag = QuantumCircuit(self.orig_circuit.num_qubits())


    def emit(self,node):
        ...


    def can_execute_directly(self, node):
        # Check current physical adjacency.
        ...

    def can_bridge(self, node):
        # Check whether shortest physical distance = 2.
        ...

    def insert_bridge(self, node):
        # Append four physical CX gates.
        # Do NOT change the logical-to-physical mapping.
        ...

    def generate_swap_sequences(self, node):
        # Generate bounded candidate SWAP sequences.
        # Do NOT modify the actual mapping or output DAG.
        ...
    def generate_bridge_sequences(self,node):
        ...
    def score_routing_action(self, action, future_gates):
        # Evaluate immediate overhead and predicted
        # future costs using a temporary mapping.
        ...

    def commit_swaps(self, swap_sequence):
        # Append each SWAP to the physical DAG.
        # Update both mapping directions after each SWAP.
        ...

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
        # Manage ready gates and routing decisions.
        # Return physical DAG, final mapping and statistics.

        # Keep the original logical DAG unchanged.
        remaining_dag = copy.deepcopy(self.orig_circuit)

        while remaining_dag.op_nodes():

            ready_nodes = remaining_dag.front_layer()
            actions = []
            for node in ready_nodes:

                # Check whether this operation can be executed.
                # If it can, emit its physical implementation.
                if self.can_execute_directly(node):
                    self.emit(node)
                    remaining_dag.remove_op_node(node)
                    continue
                if self.can_bridge():
                    actions.append(self.generate_bridge_sequences)

                actions.append(self.generate_swap_sequences)
                future_gates = self.get_future_cx(remaining_dag)
                scores, is_bridge = self.score_routing_action(actions, future_gates)

                best_action = max(scores)

                #assume emit occurs insode the insert bridge of commit swap
                if is_bridge:
                    self.insert_bridge(node)
                else:
                    self.commit_swaps(actions[best_action])



                # Only remove the logical operation AFTER
                # its physical implementation has been emitted.
                remaining_dag.remove_op_node(node)
                
