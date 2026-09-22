from general.log_config import logging
from general.visualization import plot_parser_0
from parser_0.parse_validate_qasm3 import parser_0
from parser_0.input_target import Target

logger = logging.getLogger(__name__)

####### Stage 0 ######################

qasm_file = input("Path to qasm: ")

raw_input_circuit = parser_0(qasm_file)

logger.info("circuit loaded")

target_file = input("Path to target:")

target_specs = Target(target_file)

logger.info("Target loaded")

for meas_node in raw_input_circuit.final_measure_logical_qubits:
    print(meas_node)
    print(meas_node.qargs)

plot_parser_0(raw_input_circuit, target_specs)

####### Stage 1 #####################








