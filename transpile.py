from general.log_config import logging
from general.visualization import plot_parser_0, plot_norm_dag, plot_optim_dag, plot_placement, plot_routing
from parser_0.parse_validate_qasm3 import parser_0
from parser_0.input_target import Target
from normalization_1.norm import Norm
from simple_optim_2.optim_gates import OptimGates
from placement_3.placement import Placer
from routing_4.router import Router

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
logger.info(f"equivalent check: {optim_dag.equiv_check}")
logger.info(f"Stage2 Optimizer done")

plot_optim_dag(optim_dag.optim_dag)


############ stage 3 #################
logger.info("stage 3: placement")

placer = Placer(optim_dag.optim_dag,target_specs)

logger.info(f"mapping: {placer.mapping}")
logger.info("stage 3: placement done")
plot_placement(placer.mapping, target_specs)

########## stage 4 ####################
logger.info("stage 4: routing")
router = Router(optim_dag.optim_dag, placer.mapping, target_specs)
plot_routing(router, target_specs)

routed_dag = router.routed_circuit
final_mapping = router.mapping
inital_mapping = router.initial_mapping
swap_count = router.swap_count
bridge_count = router.bridge_count
routing_history = router.routing_history
logger.info(f"swap_count: {swap_count}")
logger.info(f"bridge_count: {bridge_count}")
logger.info(f"final_mapping: {final_mapping}")
logger.info(f"ROUTING HISTORY: {routing_history}") #improvement: each stage should export a well organized report, 
                                                    #their version of this routing history. maybe converted to json.

logger.info("stage 4: routing done")
