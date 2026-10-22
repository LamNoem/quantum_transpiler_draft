"""Load a small, static quantum hardware target for the compiler."""

from general.log_config import logging
import json
import networkx as nx

logger = logging.getLogger(__name__)

# Supported native-set presets: gate name -> number of qubit operands/arity.
# Registering a preset does not implement its native-gate translator.
NATIVE_SETS = {
    "demo_cx": {"h": 1, "x": 1, "rz": 1, "cx": 2},
    "ibm_cx": {"rz": 1, "sx": 1, "x": 1, "cx": 2},
    "ibm_cz": {"rz": 1, "sx": 1, "x": 1, "cz": 2},
    "ibm_ecr": {"rz": 1, "sx": 1, "x": 1, "ecr": 2},
}


class Target:
    needed_specs = ["native_set", "instruct_connect", "phys_connect",
                    "swap_graph", "num_qubits"]

    def __init__(self, hardware_spec_file: str):
        self.target_file = hardware_spec_file
        self.target_dict = None
        self.physical_graph = None
        self.gate_connect_graphs = None
        self.swap_graph = None # usually derived but this is a simplification
        self.instruction_qargs = None  # Gate -> supported ordered operand tuples
        self.load_given_target()
        self.load_into_graph()

    def load_given_target(self):
        with open(self.target_file, "r", encoding="utf-8") as file:
            self.target_dict = json.load(file)

        for spec in self.needed_specs:
            if spec not in self.target_dict:
                logger.error("Missing hardware spec: %s", spec)
                raise ValueError(f"Missing hardware spec: {spec}")

        native_set = self.target_dict["native_set"]
        if native_set not in NATIVE_SETS:
            logger.error(f"Unknown native_set: {native_set!r}")
            raise ValueError(f"Unknown native_set: {native_set!r}")

        self.num_qubits = self.target_dict["num_qubits"]
        if type(self.num_qubits) is not int or self.num_qubits < 1:
            logger.error("num_qubits must be a positive integer")
            raise ValueError("num_qubits must be a positive integer")

        self.gate_arities = NATIVE_SETS[native_set]
        self.native_gates = list(self.gate_arities)
        connectivity_names = set(self.target_dict["instruct_connect"])
        if connectivity_names != set(self.native_gates):
            logger.error("instruct_connect keys must match the selected native_set")
            raise ValueError("instruct_connect keys must match the selected native_set")


    def expand_connectivity(self, gate_name, connectivity):
        """Turn 'all' or explicit operand lists into ordered physical-qubit tuples.
        also an opportunity to expand any other shorthands/standards that are implemented later
        """
        arity = self.gate_arities[gate_name]

        if connectivity == "all":
            if arity != 1:
                logger.error(f"{gate_name}: 'all' is only supported for 1-qubit gates")
                raise ValueError(f"{gate_name}: 'all' is only supported for 1-qubit gates")
            # h: all -> h: { (0,),...,(num_qubits,) }
            return {(q,) for q in range(self.num_qubits)}

        if not isinstance(connectivity, list):
            logger.error(f"{gate_name}: expected 'all' or a list of operand tuples")
            raise ValueError(f"{gate_name}: expected 'all' or a list of operand tuples")

        result = set()
        # connectivity = [[],[],[]] -> {(),(),()}
        for entry in connectivity:
            if not isinstance(entry, (list, tuple)) or len(entry) != arity:
                logger.error(f"{gate_name}: expected {arity} qubit indices in {entry!r}")
                raise ValueError(f"{gate_name}: expected {arity} qubit indices in {entry!r}")
            if any(type(q) is not int or not 0 <= q < self.num_qubits for q in entry):
                logger.error(f"{gate_name}: invalid physical-qubit index in {entry!r}")
                raise ValueError(f"{gate_name}: invalid physical-qubit index in {entry!r}")
            if len(set(entry)) != arity:
                logger.info(f"{gate_name}: repeated operand in {entry!r}")
                raise ValueError(f"{gate_name}: repeated operand in {entry!r}")
            result.add(tuple(entry))
        return result

    def _check_edges(self, edges, name):
        if not isinstance(edges, list):
            logger.info(f"{name} must be a list of 2-qubit pairs")
            raise ValueError(f"{name} must be a list of 2-qubit pairs")
        validated = []
        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) != 2:
                logger.info(f"{name}: expected a pair, got {edge!r}")
                raise ValueError(f"{name}: expected a pair, got {edge!r}")
            a, b = edge
            if (type(a) is not int or type(b) is not int
                    or not 0 <= a < self.num_qubits
                    or not 0 <= b < self.num_qubits or a == b):
                logger.info(f"{name}: invalid physical pair {edge!r}")
                raise ValueError(f"{name}: invalid physical pair {edge!r}")
            validated.append((a, b))
        return validated

    def load_into_graph(self):
        # Physical coupling is undirected and includes isolated qubits.
        self.physical_graph = nx.Graph()
        self.physical_graph.add_nodes_from(range(self.num_qubits))
        self.physical_graph.add_edges_from(
            self._check_edges(self.target_dict["phys_connect"], "phys_connect")
        )

        # SWAP links are also undirected.
        self.swap_graph = nx.Graph()
        self.swap_graph.add_nodes_from(range(self.num_qubits))
        swap_edges = self._check_edges(self.target_dict["swap_graph"], "swap_graph")
        for a, b in swap_edges:
            if not self.physical_graph.has_edge(a, b):
                logger.info(f"swap_graph has a link absent from phys_connect: {(a, b)}")
                raise ValueError(f"swap_graph has a link absent from phys_connect: {(a, b)}")
        self.swap_graph.add_edges_from(swap_edges)

        self.instruction_qargs = {}
        self.gate_connect_graphs = {}
        for native_gate in self.native_gates:
            connectivity = self.target_dict["instruct_connect"][native_gate]
            supported = self.expand_connectivity(native_gate, connectivity)
            self.instruction_qargs[native_gate] = supported

            if self.gate_arities[native_gate] == 2:
                for a, b in supported:
                    if not self.physical_graph.has_edge(a, b):
                        logger.info(f"{native_gate}: pair {(a, b)} absent from phys_connect")
                        raise ValueError(
                            f"{native_gate}: pair {(a, b)} absent from phys_connect"
                        )
                # Direction matters for native two-qubit instruction operands.
                graph = nx.DiGraph()
                graph.add_nodes_from(range(self.num_qubits))
                graph.add_edges_from(supported)
                self.gate_connect_graphs[native_gate] = graph
            else:
                # 1q graphs
                graph = nx.DiGraph()
                graph.add_nodes_from(q[0] for q in supported)
                self.gate_connect_graphs[native_gate] = graph

        logger.info("Loaded physical, SWAP, and native-instruction connectivity")

    def supports_native(self, gate_name, physical_qargs):
        return tuple(physical_qargs) in self.instruction_qargs.get(gate_name, set())
