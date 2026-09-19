import qiskit.qasm3
from general.log_config import logging
from stage0.input_qasm3 import Stage0
from  stage0.input_target import Target
import networkx as nx
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

####### Stage 0 ######################

qasm_file = input("Path to qasm: ")

raw_input_circuit = Stage0(qasm_file)

logger.info("circuit loaded")

target_file = input("Path to target:")

target_specs = Target(target_file)

logger.info("Target loaded")

# Or save a LaTeX rendering
Stage0.circuit.draw(output="latex", filename="orig_circuit_latex.pdf")

nx.draw(target_specs.physical_graph)

for gate_connectivity in target_specs.gate_connect_graphs.keys():
    try:
        nx.draw(target_specs.gate_connect_graphs[gate_connectivity])
    except Exception:
        print()


####### Stage 1 #####################








