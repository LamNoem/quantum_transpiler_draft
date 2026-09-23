from general.log_config import logging
from general.visualization import plot_parser_0, plot_norm_dag
from parser_0.parse_validate_qasm3 import parser_0
from parser_0.input_target import Target
from normalization_1.norm import Norm

logger = logging.getLogger(__name__)

####### Stage 0 ######################

qasm_file = input("Path to qasm: ")

raw_input_circuit = parser_0(qasm_file)

logger.info("circuit loaded")

target_file = input("Path to target: ")

target_specs = Target(target_file)

logger.info("Target loaded")

plot_parser_0(raw_input_circuit, target_specs)

logger.info("Stage 0 done")

####### Stage 1 #####################

logger.info("Stage 1: Normalization")

norm_dag = Norm(raw_input_circuit.DAG_circuit)
plot_norm_dag(norm_dag.normalized_dag)




