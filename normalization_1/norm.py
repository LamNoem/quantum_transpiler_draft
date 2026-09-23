import qiskit
import qiskit.qasm3
from qiskit.converters import circuit_to_dag
from math import pi
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from general.log_config import logging

logger = logging.getLogger(__name__)

class Norm:

    INTERNAL_GATES  = ["h", "x", "rz", "cx",]
    
    def __init__(self, dag):
        self.orig_dag = dag
        self.normalized_dag = self.recursive_normalize(dag)

    def norm_rx(node):
        theta = node.op.params[0]

        qc = QuantumCircuit(1)
        qc.h(0)
        qc.rz(theta, 0)
        qc.h(0)

        return circuit_to_dag(qc)

    def norm_ry(node):
        theta = node.op.params[0]

        qc = QuantumCircuit(1)

        qc.rz(-pi / 2, 0)
        qc.h(0)
        qc.rz(theta, 0)
        qc.h(0)
        qc.rz(pi / 2, 0)

        return circuit_to_dag(qc)


    def norm_z(node):
        qc = QuantumCircuit(1)
        qc.rz(pi, 0)

        return circuit_to_dag(qc)


    def norm_s(node):
        qc = QuantumCircuit(1)
        qc.rz(pi / 2, 0)

        return circuit_to_dag(qc)


    def norm_sdg(node):
        qc = QuantumCircuit(1)
        qc.rz(-pi / 2, 0)

        return circuit_to_dag(qc)


    def norm_t(node):
        qc = QuantumCircuit(1)
        qc.rz(pi / 4, 0)

        return circuit_to_dag(qc)


    def norm_tdg(node):
        qc = QuantumCircuit(1)
        qc.rz(-pi / 4, 0)

        return circuit_to_dag(qc)


    KNOWN_NORM = {
        "rx": norm_rx,
        "ry": norm_ry,
        "z": norm_z,
        "s": norm_s,
        "sdg": norm_sdg,
        "t": norm_t,
        "tdg": norm_tdg,
    }

    def normalize_node(self, node):


        if node.op.name in self.KNOWN_NORM:
            # We explicitly know how we want to lower it.
            return self.KNOWN_NORM[node.op.name](node)

        elif node.op.definition is not None:
            # Optional fallback for composite/custom gates.
            return circuit_to_dag(node.op.definition)

        else:
            logger.error(f"Does not support {node.op.name}, could not normalize.")
            raise ValueError(f"Does not support {node.op.name}, could not normalize.")

    def recursive_normalize(self, dag):

        for node in dag.op_nodes():
            if node.op.name not in self.INTERNAL_GATES:
                sub_dag = self.normalize_node(node)
                dag.substitute_node_with_dag(node, sub_dag)

        return dag



