import qiskit
import qiskit.qasm3
from qiskit.converters import circuit_to_dag, dag_to_circuit
from math import pi
from qiskit import QuantumCircuit
from general.log_config import logging
import networkx as nx
import copy


logger = logging.getLogger(__name__)

class Norm:

    INTERNAL_GATES  = ["h", "x", "rz", "cx",]
    
    def __init__(self, dag):
        self.orig_dag = circuit_to_dag(dag_to_circuit(dag))
        self.normalized_dag = self.recursive_normalize(dag)

    def norm_u(node):
        theta, phi, lam = node.op.params

        qc = QuantumCircuit(1)
        qc.rz(lam, 0)
        # ry
        qc.rz(-pi / 2, 0)
        qc.h(0)
        qc.rz(theta, 0)
        qc.h(0)
        qc.rz(pi / 2, 0)
        #
        qc.rz(phi, 0)

        qc.global_phase += (phi + lam) / 2
        logger.info(f"Normalized U gate with theta={theta}, phi={phi}, lambda={lam} to RZ-RY-RZ sequence.")

        return circuit_to_dag(qc)

    def norm_rx(node):
        theta = node.op.params[0]

        qc = QuantumCircuit(1)
        qc.h(0)
        qc.rz(theta, 0)
        qc.h(0)
        logger.info(f"Normalized RX gate with theta={theta} to H-RZ-H sequence.")

        return circuit_to_dag(qc)

    def norm_ry(node):
        """
        RY(theta) = [[cos(theta/2), -sin(theta/2)],
                     [sin(theta/2), cos(theta/2)]]
        
        """
        theta = node.op.params[0]

        qc = QuantumCircuit(1)

        qc.rz(-pi / 2, 0)
        qc.h(0)
        qc.rz(theta, 0)
        qc.h(0)
        qc.rz(pi / 2, 0)

      
        logger.info(f"Normalized RY gate with theta={theta} to RZ-H-RZ-H-RZ sequence.")

        return circuit_to_dag(qc)


    def norm_z(node):
        """
        Z = [[1, 0],
             [0, -1]]
        RZ(pi) = [[exp(-i*pi/2), 0],
                  [0, exp(i*pi/2)]]
        Z = exp(i*pi/2) * RZ(pi)
        """
        qc = QuantumCircuit(1)
        qc.rz(pi, 0)
        qc.global_phase = pi/2
        logger.info(f"Normalized Z gate to RZ gate with lambda={pi}.")
        return circuit_to_dag(qc)


    def norm_s(node):
        """
        S = [[1, 0],
             [0, i]] 
        RZ(pi/2) = [[exp(-i*pi/4), 0],
                    [0, exp(i*pi/4)]]
        S = exp(i*pi/4) * RZ(pi/2)
        
        """
        qc = QuantumCircuit(1)
        qc.rz(pi / 2, 0)
        qc.global_phase = pi/4
        logger.info(f"Normalized S gate to RZ gate with lambda={pi / 2}.")
        return circuit_to_dag(qc)


    def norm_sdg(node):
        """
        Sdg = [[1, 0],
               [0, -i]]
        RZ(-pi/2) = [[exp(i*pi/4), 0],
                     [0, exp(-i*pi/4)]]
        Sdg = exp(-i*pi/4) * RZ(-pi/2)
        """
        qc = QuantumCircuit(1)
        qc.rz(-pi / 2, 0)
        qc.global_phase = -pi/4
        logger.info(f"Normalized Sdg gate to RZ gate with lambda={-pi / 2}.")
        return circuit_to_dag(qc)


    def norm_t(node):
        """
        T = [[1, 0],
             [0, exp(i*pi/4)]]
        RZ(pi/4) = [[exp(-i*pi/8), 0],
                     [0, exp(i*pi/8)]]
        T = exp(i*pi/8) * RZ(pi/4)
        """
        qc = QuantumCircuit(1)
        qc.rz(pi / 4, 0)
        qc.global_phase = pi/8
        logger.info(f"Normalized T gate to RZ gate with lambda={pi / 4}.")
        return circuit_to_dag(qc)


    def norm_tdg(node):
        """
        Tdg = [[1, 0],
               [0, exp(-i*pi/4)]]
        RZ(-pi/4) = [[exp(i*pi/8), 0],
                      [0, exp(-i*pi/8)]]
        Tdg = exp(-i*pi/8) * RZ(-pi/4)
        """
        qc = QuantumCircuit(1)
        qc.rz(-pi / 4, 0)
        qc.global_phase = -pi/8
        logger.info(f"Normalized Tdg gate to RZ gate with lambda={-pi / 4}.")
        return circuit_to_dag(qc)


    KNOWN_NORM = {
        "rx": norm_rx,
        "ry": norm_ry,
        "z": norm_z,
        "s": norm_s,
        "sdg": norm_sdg,
        "t": norm_t,
        "tdg": norm_tdg,
        "u": norm_u,
    }

    def normalize_node(self, node) -> tuple[nx.DiGraph, int]:


        if node.op.name in self.KNOWN_NORM:
            # We explicitly know how we want to lower it.
            return self.KNOWN_NORM[node.op.name](node), 0

        elif node.op.definition is not None:
            # Optional fallback for composite/custom gates.
            logger.info(f"Normalizing {node.op.name} using its definition.")
            return circuit_to_dag(node.op.definition), 1

        else:
            logger.error(f"Does not support {node.op.name}, could not normalize.")
            raise ValueError(f"Does not support {node.op.name}, could not normalize.")

    def recursive_normalize(self, dag):
        not_normalized = 1

        while (not_normalized):
            not_normalized = 0

            for node in dag.op_nodes():
                if node.op.name not in self.INTERNAL_GATES:
                    sub_dag, norm_flag = self.normalize_node(node)
                    dag.substitute_node_with_dag(node, sub_dag)
                    not_normalized |= norm_flag
        logger.info("Dag normalization complete")

        return dag



