import qiskit.qasm3
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGOpNode
from math import pi
from qiskit import QuantumCircuit
from general.log_config import logging
from qiskit.circuit.library import HGate, XGate, RZGate, CXGate, RXGate, RYGate, ZGate, SGate, SdgGate, TGate, TdgGate, UGate, Barrier
import networkx as nx
import copy


logger = logging.getLogger(__name__)

class OptimGates:

    ITER_LIMIT = 10

    def __init__(self, norm_dag):
        self.optim_dag = self.simple_optimize(circuit_to_dag(dag_to_circuit(norm_dag)))

    def simple_optimize(self, norm_dag):
        """
        inverse cancellation (HH, XX, CX-CX)

        adjacent RZ

        non adjacent optimization -> to do /learn

        repeat passes until no more optimization is possible

        maintain equiv and qubit identities.
        """

        for _ in range(self.ITER_LIMIT):
            optimized = self.inverse_cancellation(norm_dag)
            optimized |= self.merge_adjacent_RZ(norm_dag)

            if not optimized:
                break

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

        edges = list(norm_dag.edges(node))

        for succ in norm_dag.successors(node):
            if not isinstance(succ, DAGOpNode):
                continue

            if succ.qargs != node.qargs:
                continue
            adjacent = True
            # for every qubit involved in the current gate
            for node_q in node.qargs:
                 # Check the edges connected to the current gate
                found = False
                for _, dest_gate, edge_q in edges:
                    # for every qubit involved, 
                    # There must be a direct edge to the SAME successor
                    if dest_gate is succ and edge_q== node_q:
                        found = True
                        break

                # If no such edge exists for even one qubit,
                # the two gates are not fully adjacent
                if not found:
                    adjacent = False
                    break

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



    