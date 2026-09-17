import qiskit.qasm3
from general.log_config import logging

logger = logging.getLogger(__name__)

def load_qasm(filename):

    file_name = input("input path to QASM file: ")

    circuit = qiskit.qasm3.load(file_name)

    return circuit

#check circuit is within supported feature set.
# no measurements /  resets / classical feedback or additional ancillas, 3 qubit max.
def verify_circuit_supported(circuit):
    ancillas = circuit.ancillas
    if len(ancillas) != 0:
        logger.error("Does not support ancillas.")


# Parse and load circuit into internal rep

# record metadata

