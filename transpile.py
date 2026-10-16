from general.log_config import logging
from general.visualization import plot_parser_0, plot_norm_dag, plot_optim_dag
from parser_0.parse_validate_qasm3 import parser_0
from parser_0.input_target import Target
from normalization_1.norm import Norm
from simple_optim_2.optim_gates import OptimGates

logger = logging.getLogger(__name__)

####### Stage 0 ######################

logger.info("Stage 0: Parser")

qasm_file = input("Path to qasm: ")
logger.info(f"qasm file: {qasm_file}")

raw_input_circuit = parser_0(qasm_file)



target_file = input("Path to target: ")
logger.info(f"target file: {target_file}")

target_specs = Target(target_file)


plot_parser_0(raw_input_circuit, target_specs)

logger.info("Stage 0 done")

####### Stage 1 #####################

logger.info("Stage 1: Normalization")

norm_dag = Norm(raw_input_circuit.DAG_circuit)
plot_norm_dag(norm_dag.normalized_dag)

logger.info("Stage 1: done")

####### Stage 2 ######################

logger.info("Stage 2: Optimize/Simplify")

optim_dag = OptimGates(norm_dag.normalized_dag)
logger.info(f"gate count diff (new-old):{optim_dag.new_gate_count - optim_dag.orig_gate_count}")
logger.info(f"depth diff (new-old):{optim_dag.new_depth - optim_dag.orig_depth}")

plot_optim_dag(optim_dag.optim_dag)




