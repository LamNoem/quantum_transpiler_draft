
import copy
from itertools import permutations

import networkx as nx
import numpy as np
from qiskit.dagcircuit import DAGCircuit

from general.log_config import logging
from parser_0.input_target import Target

logger = logging.getLogger(__name__)


class Placer:

    def __init__(self, optim_circuit: DAGCircuit, target: Target):
        # Keep independent copies of the logical DAG and hardware model.
        self.hardware = copy.deepcopy(target)
        self.circuit = copy.deepcopy(optim_circuit)

        G = self.hardware.physical_graph

        if not nx.is_connected(G):
            raise ValueError("Hardware graph must be connected")

        if self.circuit.num_qubits() > G.number_of_nodes():
            raise ValueError("Circuit has more logical qubits than physical qubits")

        # Cache hop distances and total distances once, for every placement.
        # centrality[p] is smaller for more centrally located physical qubits.
        self.distances = dict(nx.all_pairs_shortest_path_length(G))
        self.centrality = {
            p: sum(self.distances[p].values())
            for p in G.nodes
        }

        # i prefer for these to be assined explicitly when possible in as little palces as possible, mnimizes confusion
        self.interact_matrix = self.build_interact_matrix()
        self.mapping = self.heuristic_initial_placement()
        self.mapping_cost = self.evaluate_mapping()

        
    def evaluate_mapping(self):
        n = self.circuit.num_qubits()
        total_cost = 0

        #only upper triangle bc symmetrical
        for i in range(n):
            for j in range(i + 1, n):
                interactions = int(self.interact_matrix[i, j])

                physical_i = self.mapping[i]
                physical_j = self.mapping[j]

                distance = self.distances[physical_i][physical_j]

                pair_cost = interactions * (distance - 1)
                total_cost += pair_cost

        return total_cost
    
    def num_free_neighbours(self, p, free, reserved):
        """Count free neighbours of physical qubit p, excluding reserved sites (usually the free physical qubits being considered)."""
        G = self.hardware.physical_graph
        return sum(
            neighbour in free and neighbour not in reserved
            for neighbour in G.neighbors(p)
        )

    def cost(self, pp, popularity1, popularity2, free):
        """Score two physical locations for a new logical pair (lower is better)."""
        p1, p2 = pp
        reserved = {p1, p2}

        return (
            # 1. Put the interacting pair as close together as possible.
            self.distances[p1][p2],

            # 2. Preserve free neighbours around more popular logical qubits.
            -(
                popularity1 * self.num_free_neighbours(p1, free, reserved) #num free neighbours around p1 and p2 that are not p1 or p2
                + popularity2 * self.num_free_neighbours(p2, free, reserved)
            ),

            # 3. Among ties, favour locations near the hardware's center.
            popularity1 * self.centrality[p1]
            + popularity2 * self.centrality[p2],

            # 4. Ensure repeatable results when all other scores tie.
            pp,
        )


    def build_interact_matrix(self):
        """Count CX interactions between logical qubits in the optimized DAG."""
        num_qubits = self.circuit.num_qubits()
        interacts = np.zeros((num_qubits, num_qubits), dtype=int)

        for node in self.circuit.topological_op_nodes():
            if node.op.name == "cx":
                control, target = node.qargs
                control_index = self.circuit.find_bit(control).index
                target_index = self.circuit.find_bit(target).index

                # Treat each pair as undirected for placement, because the
                # current hardware connectivity is bidirectional.
                interacts[control_index, target_index] += 1
                interacts[target_index, control_index] += 1
                

        # self.interact_matrix = interacts
        return interacts

    def place(self, interacts, pair, mapping):
        """Assign one or both members of a logical pair to free physical sites."""
        G = self.hardware.physical_graph
        q1, q2 = pair

        # A pair is a tuple; iterating over it returns q1 and q2.
        # 'new' contains only the logical qubits not assigned yet.
        new = [q for q in pair if q not in mapping]
        if not new:
            raise ValueError("Both qubits are already placed")

        # Only physical positions NOT already used by another logical qubit.
        free = sorted(set(G.nodes) - set(mapping.values()))
        if len(free) < len(new):
            raise ValueError("Not enough free physical qubits")

        if len(new) == 2:
            # First pair, or first pair of a new disconnected logical group:
            # assign both logical qubits together.
            popularity1 = int(interacts[q1].sum())
            popularity2 = int(interacts[q2].sum())

            best_pair = None
            best_cost = None

            # Check all ordered pairs of free physical locations.
            # This is NOT a search over complete circuit mappings.
            for pp in permutations(free, 2):
                current_cost = self.cost(pp, popularity1, popularity2, free)
                if best_cost is None or current_cost < best_cost:
                    best_cost = current_cost
                    best_pair = pp

            
            mapping[q1], mapping[q2] = best_pair

        else:
            # Exactly one qubit has already been assigned.
            # Never change that existing assignment.
            unplaced_q = new[0]
            placed_q = q2 if unplaced_q == q1 else q1
            partner_physical = mapping[placed_q]

            best_physical = None
            best_cost = None

            for p in free:
                # Also consider this qubit's OTHER previously placed partners
                # when several sites are equally close to the selected one.
                # for each free phys q
                other_partner_cost = sum( #for each logic and phys already mapped
                    int(interacts[unplaced_q, other_q])  # num of interacts btwn the log unplaced and log placed  (multiplied by)
                    * self.distances[p][other_physical] # the distance from the free phys q to th ephys q of this log placed 
                    for other_q, other_physical in mapping.items()
                )  # essentially (does th eunplaced qubit interact alot with this placed log qubit)*(is this free physical qubit a smart placement for this relationship)
                #summed up: is this free phys_q a smart choice to couple (the unmapped log_q) to an already placed logical_q (if they interact a lot)

                current_cost = (
                    # 1. Prefer a direct connection to the selected partner.
                    self.distances[p][partner_physical],

                    # 2. Then prefer proximity to its other placed partners.
                    other_partner_cost,

                    # 3. Preserve free neighbours for later placements.
                    -self.num_free_neighbours(p, free, {p}), #number of free neighbours around p that is not p. so a phys q with alot of free neighbours left is prioritized

                    # 4. Use centrality and index for remaining ties.
                    self.centrality[p],
                    p,
                )

                if best_cost is None or current_cost < best_cost:
                    best_cost = current_cost
                    best_physical = p

            
            mapping[unplaced_q] = best_physical

    def place_remaining(self, unplaced, mapping):
        """Assign any logical qubits with no remaining CX interaction partners."""
        G = self.hardware.physical_graph

        for unplaced_q in sorted(unplaced):
            free = sorted(set(G.nodes) - set(mapping.values()))
            if not free:
                raise ValueError("Not enough free physical qubits")

            best_physical = None
            best_cost = None

            for p in free:
                current_cost = (
                    self.centrality[p],  # Prefer central free sites.
                    -G.degree[p],        # Then more connected sites.
                    p,                   # Finally the lower physical index.
                )
                if best_cost is None or current_cost < best_cost:
                    best_cost = current_cost
                    best_physical = p

            
            mapping[unplaced_q] = best_physical

    def heuristic_initial_placement(self):
        """
        old strat:        Ideally, nobody should have to SWAP beds just to have an affair.
                            Keep wives, husbands and mistresses close.

                            Pick frequently interacting logical pairs, favouring pairs with a
                            highly active member. Place each pair without moving existing ones.
                            Routing (including real SWAP gates) belongs to the next stage.

        fix: test new jensen huang heuristic placer, weighting is done differently
        - logical qubits with a high diversity of interactions are prioritized instead, 
        - high frequency within one pair less prioritized
        - binary interact matrix then, scores = has_interact(i,j)*(div(i) + div(j)), for each (i,j)
        -improvent: both endpoint contribute to weighting, number of total interactions/interact_freq, no longer contributes.
        - essentially the interact pairs with the most popular qubits are placed first
        """
        num_qubits = self.circuit.num_qubits()

        if self.interact_matrix is None:
            self.interact_matrix = self.build_interact_matrix()

        interacts = self.interact_matrix

        # Matrix is symmetric, but row weighting intentionally need not be.
        # Each candidate orientation is considered by the search below.
        # weights = np.sum(interacts, axis=1, keepdims=True)
        # scores = weights * interacts
        #fix: scores = has_interact(i,j)*(div(i) + div(j)), for each (i,j) -> jensen huang scoring

        binary = (interacts >0).astype(int)
        diversity = binary.sum(axis=1, keepdims = True)
        scores =  (diversity + diversity.T)*binary

        placed = set()
        unplaced = set(range(num_qubits))
        mapping = {}  # logical qubit index -> physical qubit index

        while unplaced:
            # Prefer an interaction between an already-placed logical qubit
            # and an unplaced one. Both tuple orientations are considered.
            placed_subset = [
                (i, j)
                for i in range(num_qubits)
                for j in range(num_qubits)
                if (
                    (i in placed and j in unplaced)
                    or (i in unplaced and j in placed)
                )
                and scores[i, j] > 0
            ]

            if placed_subset:
                pair = max(placed_subset, key=lambda x: scores[x])
            else:
                # No positive-weight edge crosses from placed to unplaced.
                # Start the next disconnected logical interaction group.
                unplaced_subset = [
                    (i, j)
                    for i in sorted(unplaced)
                    for j in sorted(unplaced)
                    if i != j and scores[i, j] > 0
                ]

                if not unplaced_subset:
                    break  # Remaining qubits have no CX interactions.

                pair = max(unplaced_subset, key=lambda x: scores[x])

            # The pair describes interacting qubits; it is NOT necessarily
            # (control, target), because the interaction matrix is symmetric.
            self.place(interacts, pair, mapping)

            # Only mark qubits placed AFTER the physical assignments succeed.
            placed.update(pair)
            unplaced.difference_update(pair)

        # Assign any logical qubits that do not participate in CX operations.
        self.place_remaining(unplaced, mapping)

        # A valid initial placement assigns every logical qubit once,
        # and never uses the same physical qubit for two logical qubits.
        if set(mapping) != set(range(num_qubits)):
            raise ValueError("Initial placement is incomplete")
        if len(set(mapping.values())) != num_qubits:
            raise ValueError("Multiple logical qubits share a physical location")

        # self.mapping = mapping.copy()
        return mapping
