import qiskit
import qiskit.qasm3
from general.log_config import logging

logger = logging.getLogger(__name__)


class Stage0:
    ancillas_supported = False
    max_qubits = 3
    unsupport_circ_instruct = ["reset", "measure"]

    def __init__(self, qasm_file):
        self.qasm_file = qasm_file
        self.num_qubits = None
        self.num_ancillas = None
        self.metadata = None
        self.circuit = None
        self.load_qasm(qasm_file)
        self.verify_circuit_supported(self.circuit)

    def load_qasm(self, file_name):
        try:
            self.circuit = qiskit.qasm3.load(file_name)
        except Exception as e:
            # BUG FIX: Log the actual error 'e' so you know WHY the QASM failed (e.g. syntax error)
            logger.error(f"Initial load into qiskit failed: {e}")
            # BUG FIX: Use 'from e' to chain the exception and preserve the traceback
            raise ValueError(f"Initial load into qiskit failed: {e}") from e

    # Check circuit is within supported feature set.
    # No measurements / resets / classical feedback or additional ancillas, 3 qubit max.
    def verify_circuit_supported(self, circuit: qiskit.QuantumCircuit):
        self.num_ancillas = circuit.num_ancillas
        self.num_qubits = circuit.num_qubits
        
        if self.num_ancillas > 0 and not Stage0.ancillas_supported:
            logger.error("Does not support ancillas.")
            raise ValueError("Does not support ancillas.")
        elif self.num_qubits > Stage0.max_qubits:
            logger.error(f"Does not support more than {Stage0.max_qubits} qubits")
            raise ValueError(f"Does not support more than {Stage0.max_qubits} qubits")

        for instruct in circuit.data:
            if instruct.operation.name in Stage0.unsupport_circ_instruct:
                logger.error(f"Does not support {instruct.operation.name}.")
                raise ValueError(f"Does not support {instruct.operation.name}.")

        if circuit.has_control_flow_op() or circuit.num_clbits > 0:
            logger.error("Does not support classical feedback: control flow op.")
            raise ValueError("Does not support classical feedback: control flow op.")

    def store_metadata(self, circuit: qiskit.QuantumCircuit):
        # metadata cannot be sent to qiskit circuit through OpenQASM
        return