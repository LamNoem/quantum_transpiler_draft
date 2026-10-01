import qiskit
import qiskit.qasm3
from general.log_config import logging

from qiskit.converters import circuit_to_dag
from qiskit.circuit.measure import Measure
from qiskit.transpiler.passes.utils.remove_final_measurements import calc_final_ops


logger = logging.getLogger(__name__)


class parser_0:
    ancillas_supported = False
    max_qubits = 3
    unsupport_circ_instruct = ["reset"]

    def __init__(self, qasm_file):
        self.qasm_file = qasm_file
        self.num_qubits = None
        self.num_ancillas = None
        self.metadata = None
        self.circuit = None
        self.DAG_circuit = None
        self.final_measure_logical_qubits = None
        self.load_qasm(qasm_file)
        self.verify_circuit_supported(self.circuit)
        self.convert_to_dag()

    def load_qasm(self, file_name):
        try:
            self.circuit = qiskit.qasm3.load(file_name)
        except Exception as e:
            # BUG FIX: Log the actual error 'e' so you know WHY the QASM failed (e.g. syntax error)
            logger.error(f"Initial load into qiskit failed: {e}")
            # BUG FIX: Use 'from e' to chain the exception and preserve the traceback
            raise ValueError(f"Initial load into qiskit failed: {e}") from e

        logger.info("circuit loaded")

    # Check circuit is within supported feature set.
    # No measurements / resets / classical feedback or additional ancillas, 3 qubit max.
    def verify_circuit_supported(self, circuit: qiskit.QuantumCircuit):
        self.num_ancillas = circuit.num_ancillas
        self.num_qubits = circuit.num_qubits
        
        if self.num_ancillas > 0 and not parser_0.ancillas_supported:
            logger.error("Does not support ancillas.")
            raise ValueError("Does not support ancillas.")
        elif self.num_qubits > parser_0.max_qubits:
            logger.error(f"Does not support more than {parser_0.max_qubits} qubits")
            raise ValueError(f"Does not support more than {parser_0.max_qubits} qubits")

        for instruct in circuit.data:
            if instruct.operation.name in parser_0.unsupport_circ_instruct:
                logger.error(f"Does not support {instruct.operation.name}.")
                raise ValueError(f"Does not support {instruct.operation.name}.")

        if circuit.has_control_flow_op():
            logger.error("Does not support classical feedback: control flow op.")
            raise ValueError("Does not support classical feedback: control flow op.")
    def convert_to_dag(self):
        ## only final measurement ops allowed no measure mid circuit where the measurement is used for logic.
        self.DAG_circuit = circuit_to_dag(self.circuit)
        measure_nodes = self.DAG_circuit.op_nodes(Measure, True)
        final_measure_nodes = calc_final_ops(self.DAG_circuit, {"measure"})

        for node in measure_nodes:
            if node not in final_measure_nodes:
                logger.error("Unsupported circuit: mid-circuit measurement detected.")
                raise ValueError(
                    "Unsupported circuit: mid-circuit measurement detected."
                )
            self.DAG_circuit.remove_op_node(node)

        if self.DAG_circuit.num_vars:
            logger.error("Unsupported circuit: classical feedback or classical vars detected.")
            raise ValueError(
                "Unsupported circuit: classical feedback or classical vars detected."
            )
        self.final_measure_logical_qubits = final_measure_nodes
        logger.info("converted to dag")

    def store_metadata(self, circuit: qiskit.QuantumCircuit):
        # metadata cannot be sent to qiskit circuit through OpenQASM
        return