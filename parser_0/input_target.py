"""Load a preset-only, homogeneous target for the compiler draft.

Model assumptions:
- All native one-qubit gates are available on every physical qubit.
- All native two-qubit gates are available in BOTH operand orders on each link.
- Every physical link can implement a routing SWAP (not necessarily natively).
- No per-qubit restrictions, calibration data, durations, or angle limits.

"""

from general.log_config import logging
import json
import networkx as nx
from qiskit.transpiler import CouplingMap

logger = logging.getLogger(__name__)

# Native-set name -> {gate name: number of qubit operands}
NATIVE_SETS = {
    "demo_cx": {"h": 1, "x": 1, "rz": 1, "cx": 2},
    "ibm_cx": {"rz": 1, "sx": 1, "x": 1, "cx": 2},
    "ibm_cz": {"rz": 1, "sx": 1, "x": 1, "cz": 2},
    "ibm_ecr": {"rz": 1, "sx": 1, "x": 1, "ecr": 2},
}

# Extra parameters required by each Qiskit CouplingMapm constructor
#Empty tuples mean use num_qubits 
TOPOLOGY_PARAMETERS = {
    "line": (),
    "ring": (),
    "full": (),
    "grid": ("rows", "cols"),
    "heavy_hex": ("distance",),
    "heavy_square": ("distance",),
    "hexagonal_lattice": ("rows", "cols"),
}


class Target:
    needed_specs = ["native_set", "num_qubits", "phys_connect"]

    def __init__(self, hardware_spec_file: str):
        self.target_file = hardware_spec_file
        #from load given target
        self.target_dict
        self.native_set
        self.num_qubits
        self.gate_arities
        self.native_gates

        #from load into graph
        #physical connectivity
        self.physical_edges
        self.physical_graph
        self.swap_graph

        #gate connectivity
        self.gate_connect_qargs
        self.gate_connect_graphs
        self.load_given_target()
        self.load_into_graph()

    def load_given_target(self):
        with open(self.target_file, "r", encoding="utf-8") as file:
            self.target_dict = json.load(file)

        if not isinstance(self.target_dict, dict):
            logger.error("Target file must contain a JSON object")
            raise ValueError("Target file must contain a JSON object")

        missing = set(self.needed_specs) - self.target_dict.keys()
        if missing:
            logger.error(f"Missing hardware specs: {sorted(missing)}")
            raise ValueError(f"Missing hardware specs: {sorted(missing)}")


        self.native_set = self.target_dict["native_set"]
        if not isinstance(self.native_set, str) or self.native_set not in NATIVE_SETS:
            logger.error(f"Unknown native_set: {self.native_set!r}")
            raise ValueError(f"Unknown native_set: {self.native_set!r}")

        self.num_qubits = self.target_dict["num_qubits"]
        if type(self.num_qubits) is not int or self.num_qubits < 1:
            logger.error("num_qubits must be a positive integer")
            raise ValueError("num_qubits must be a positive integer")

        #arity as in number of involved qubits. {gate_name: num_qubits_involved}
        self.gate_arities = dict(NATIVE_SETS[self.native_set])
        #lsit of gate names
        self.native_gates = list(self.gate_arities)
        # Keep compatibility with existing code that READS this dictionary key.
        self.target_dict["native_gates"] = self.native_gates.copy()

    def expand_physical_connectivity(self, specification):
        """Generate undirected physical links from a Qiskit topology preset."""
        if not isinstance(specification, dict):
            logger.error("phys_connect must be a dict")
            raise ValueError("phys_connect must be a dict")

        preset = specification.get("preset")
        if not isinstance(preset, str):
            logger.error("phys_connect requires a string 'preset' name")
            raise ValueError("phys_connect requires a string 'preset' name")

        if preset not in TOPOLOGY_PARAMETERS:
            logger.error(f"Unknown Qiskit connectivity preset: {preset!r}")
            raise ValueError(f"Unknown Qiskit connectivity preset: {preset!r}")

        parameters = TOPOLOGY_PARAMETERS[preset]
        required = {"preset", *parameters}
        if set(specification) != required:
            logger.error(f"phys_connect '{preset}' requires exactly these fields: "
                            f"{sorted(required)}")
            raise ValueError(
                f"phys_connect '{preset}' requires exactly these fields: "
                f"{sorted(required)}"
            )

        coupling_constructor_args = []
        for name in parameters:
            value = specification[name]
            if type(value) is not int or value < 1:
                logger.error(f"{preset}: '{name}' must be a positive integer")
                raise ValueError(f"{preset}: '{name}' must be a positive integer")
            coupling_constructor_args.append(value)

        # The code distance for the generated heavy hex graph. The value for distance can be any odd positive integer. The distance relates to the number of qubits by: n = (5d² - 2d - 1) / 2
        #  # The code distance for the generated heavy square graph.
        # The value for distance can be any odd positive integer.
        # The distance relates to the number of qubits by: n = 3d² - 2d
        if preset in {"heavy_hex", "heavy_square"} and coupling_constructor_args[0] % 2 == 0:
            logger.error(f"{preset}: distance must be odd")
            raise ValueError(f"{preset}: distance must be odd")

        if not parameters: # line, ring, full
            coupling_constructor_args = [self.num_qubits]

        constructor = getattr(CouplingMap, f"from_{preset}")
        coupling = constructor(*coupling_constructor_args, bidirectional=True)
        if coupling.size() != self.num_qubits: #should be true according to docs, if all went well, if i loaded things properly
            logger.error(f"Topology '{preset}' generates {coupling.size()} qubits, "
                            f"but num_qubits={self.num_qubits}")
            raise ValueError(
                f"Topology '{preset}' generates {coupling.size()} qubits, "
                f"but num_qubits={self.num_qubits}"
            )

        # Each undirected link stored once
        #keep Qiskit qubit numbering.
        return sorted({
            tuple(sorted((a, b)))
            for a, b in coupling.get_edges()
            if a != b
        })

    def load_into_graph(self):
        self.physical_edges = self.expand_physical_connectivity(
            self.target_dict["phys_connect"]
        )
        self.physical_graph = nx.Graph()
        self.physical_graph.add_nodes_from(range(self.num_qubits))
        self.physical_graph.add_edges_from(self.physical_edges)

        # simplification: every physical edge can implement a routing SWAP.
        self.swap_graph = self.physical_graph.copy()

        one_qubit_support = {(q,) for q in range(self.num_qubits)}
        two_qubit_support = {
            pair
            for a, b in self.physical_edges
            for pair in ((a, b), (b, a))
        }

        self.gate_connect_qargs = {}
        self.gate_connect_graphs = {}
        for gate, arity in self.gate_arities.items():
            if arity == 1:
                supported = one_qubit_support.copy()
            elif arity == 2:
                supported = two_qubit_support.copy()
            else:
                logger.error(f"{gate}: only 1q and 2q native gates are supported")
                raise ValueError(f"{gate}: only 1q and 2q native gates are supported")

            self.gate_connect_qargs[gate] = supported #from arity to actual tuples of gate connect
            graph = nx.DiGraph()
            graph.add_nodes_from(range(self.num_qubits))
            if arity == 2:
                graph.add_edges_from(sorted(supported))
            # A 1q gate's graph contains all physical nodes and no edges
            self.gate_connect_graphs[gate] = graph

        logger.info(
            "Loaded uniform target: native_set=%s, qubits=%d, physical links=%d",
            self.native_set, self.num_qubits, len(self.physical_edges),
        )

    def supports_nativegate(self, gate_name, desired_gate_connect_qargs):
        """Check native gate name and operands, not synthesis or angle limits."""
        d_g_qargs = tuple(desired_gate_connect_qargs)
        #qubits described by ints
        if any(type(q) is not int for q in d_g_qargs):
            return False
        #desired gate connectivity, available in instruction
        return d_g_qargs in self.gate_connect_qargs.get(gate_name, set())
