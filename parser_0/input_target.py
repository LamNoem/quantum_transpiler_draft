import qiskit.qasm3
from general.log_config import logging
import json
import networkx as nx

logger = logging.getLogger(__name__)

{
    "optional name": "string_name",

    "num_qubits": 3,

    "phys_connect": [
        [0, 1],
        [1, 2], #so CX(control=1, target=2) allowed
        ["control", "target"], 
    ],


    "instruct_connect": {
        "h": "all",
        "x": "all",
        "rz": "all",

        "cx": [
        [0, 1],
        [1, 0],
        [1, 2],
        [2, 1]
        ]
    },

    "native_gates": [
        "h",
        "x",
        "rz",
        "cx"
    ]
}

class Target:
    needed_specs = ["native_gates", "instruct_connect", "phys_connect", "num_qubits"]

    def __init__(self, hardware_spec_file: str):
        self.target_file = hardware_spec_file
        self.target_dict = None
        self.physical_graph = None
        self.gate_connect_graphs = None
        self.load_given_target()
        self.load_into_graph()


    def load_given_target(self):
        with open(self.target_file, 'r') as file:
            self.target_dict = json.load(file)

        for spec in Target.needed_specs:
            if spec not in self.target_dict:
                logger.error(f"Missing hardware spec: {spec}.")
                raise ValueError(f"Missing hardware spec: {spec}")

    def load_into_graph(self):
        self.physical_graph = nx.MultiDiGraph()
        self.physical_graph.add_edges_from(self.target_dict["phys_connect"])

        self.gate_connect_graphs = {}

        for native_gate in self.target_dict["native_gates"]:
            connectivity = self.target_dict["instruct_connect"][native_gate]
            if isinstance(connectivity,list):
                self.gate_connect_graphs[native_gate] = nx.MultiDiGraph()
                self.gate_connect_graphs[native_gate].add_edges_from(connectivity)
            else:
                self.gate_connect_graphs[native_gate] = connectivity


    














            



