import qiskit
import qiskit.qasm3
from general.log_config import logging

from qiskit.converters import circuit_to_dag
from qiskit.circuit.measure import Measure
from qiskit.transpiler.passes.utils.remove_final_measurements import calc_final_ops


logger = logging.getLogger(__name__)


class parser_0:
    ancillas_supported = False
    max_qubits = 5
    unsupport_circ_instruct = ["reset", "delay"]

    def __init__(self, qasm_file):
        self.qasm_file = qasm_file
        self.num_qubits = None
        self.num_ancillas = None
        self.metadata = None
        self.circuit = None
        self.DAG_circuit = None
        self.final_measure_map = {}
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

    def validate_operations(self, circuit, nested=False, depth=0):

        if depth > 50:
            raise ValueError("Instruction nesting too deep.")

        for instruct in circuit.data:
            op = instruct.operation

            # Reject delays and resets, including nested ones.
            if op.name in self.unsupport_circ_instruct:
                raise ValueError(
                    f"Unsupported circuit: {op.name} detected."
                )

            # Measurements inside custom instructions aren't supported.
            if nested and op.name == "measure":
                raise ValueError(
                    "Unsupported circuit: measurement inside "
                    "a composite instruction."
                )

            # Check the contents of composite instructions.
            if op.definition is not None:
                self.validate_operations(
                    op.definition,
                    nested=True,
                    depth=depth + 1
                )

    # Check circuit is within supported feature set.
    # No measurements / resets / classical feedback or additional ancillas, 3 qubit max.
    def verify_circuit_supported(self, circuit: qiskit.QuantumCircuit):
        self.num_ancillas = circuit.num_ancillas
        self.num_qubits = circuit.num_qubits
        
        if self.num_ancillas > 0 and not parser_0.ancillas_supported:
            logger.error("Does not support ancillas.")
            raise ValueError("Does not support ancillas.")
        elif 0 >= self.num_qubits or self.num_qubits > parser_0.max_qubits:
            logger.error(f"Does not support more than {parser_0.max_qubits} qubits")
            raise ValueError(f"Does not support more than {parser_0.max_qubits} qubits")

        self.validate_operations(circuit)

        # Reject classical variables
        if circuit.num_vars > 0:
            logger.error("Unsupported circuit: classical variables detected.")
            raise ValueError(
                "Unsupported circuit: classical variables detected."
            )

        # Reject classical control flow
        if circuit.has_control_flow_op():
            logger.error("Unsupported circuit: control flow detected.")
            raise ValueError(
                "Unsupported circuit: control flow detected."
            )
        
    def convert_to_dag(self):
        ## only final measurement ops allowed no measure mid circuit where the measurement is used for logic.
        self.DAG_circuit = circuit_to_dag(self.circuit)
        measure_nodes = self.DAG_circuit.op_nodes(Measure, True)
        final_ops= calc_final_ops(self.DAG_circuit, {"measure", "barrier"})
        final_measure_nodes = [
            node for node in final_ops
            if isinstance(node.op, Measure)
        ]

        for node in measure_nodes:
            if node not in final_measure_nodes:
                logger.error("Unsupported circuit: mid-circuit measurement detected.")
                raise ValueError(
                    "Unsupported circuit: mid-circuit measurement detected."
                )

        if self.DAG_circuit.num_vars:
            logger.error("Unsupported circuit: classical feedback or classical vars detected.")
            raise ValueError(
                "Unsupported circuit: classical feedback or classical vars detected."
            )
        # Build a unique measurement mapping.
        q_to_c = {}
        c_to_q = {}

        for instruction in self.circuit.data:
            if not isinstance(instruction.operation, Measure):
                continue

            q = instruction.qubits[0]
            c = instruction.clbits[0]

            # Same qubit measured multiple times.
            if q in q_to_c:
                if q_to_c[q] != c:
                    logger.error("Same qubit measured into different classical bits.")
                    raise ValueError(
                        "Same qubit measured into different "
                        "classical bits."
                    )

                # Exact duplicate: ignore this occurrence.
                continue

            # Multiple qubits writing to the same classical bit.
            if c in c_to_q:
                logger.error("Different qubits measured into the same classical bit.")
                raise ValueError(
                    "Different qubits measured into the "
                    "same classical bit."
                )

            q_to_c[q] = c
            c_to_q[c] = q

        # STEP 4: Save stable logical/classical indices.
        self.final_measure_map = {
            self.circuit.find_bit(q).index:
            self.circuit.find_bit(c).index
            for q, c in q_to_c.items()
        }

        # STEP 5: Remove all measurement operations.
        # Barriers are preserved.
        for node in measure_nodes:
            self.DAG_circuit.remove_op_node(node)

        logger.info(
            f"Converted to DAG. Final measurement map: "
            f"{self.final_measure_map}"
        )


    def store_metadata(self, circuit: qiskit.QuantumCircuit):
        # metadata cannot be sent to qiskit circuit through OpenQASM
        return