"""Drawing and display helpers for the compiler pipeline."""

import os
from math import sqrt
from pathlib import Path
import shutil
import sys

import matplotlib.pyplot as plt
import networkx as nx
import rustworkx as rx
from qiskit.visualization import dag_drawer


def physical_layout(target_specs):
    """Place physical node IDs in the geometry of the target's topology preset."""
    graph = target_specs.physical_graph
    topology = target_specs.target_dict["phys_connect"]
    preset = topology["preset"]

    if preset == "line":
        return {p: (p, 0) for p in graph.nodes}
    if preset == "grid":
        cols = topology["cols"]
        return {p: (p % cols, -(p // cols)) for p in graph.nodes}
    if preset in {"ring", "full"}:
        return nx.circular_layout(graph, scale=max(1, len(graph) / 6))
    if preset == "hexagonal_lattice":
        # Qiskit uses this same generator, so coordinates retain its node IDs.
        lattice = rx.generators.hexagonal_lattice_graph(
            topology["rows"], topology["cols"], with_positions=True
        )
        return {p: lattice[p] for p in graph.nodes}
    if preset in {"heavy_hex", "heavy_square"}:
        return _heavy_layout(graph, topology["distance"], preset)

    raise ValueError(f"Unsupported physical topology: {preset!r}")


def _heavy_layout(graph, distance, preset):
    """Draw Qiskit's heavy lattices with their original physical node IDs."""
    if distance == 1:
        return {0: (0, 0)}
    hexagonal = preset == "heavy_hex"

    def midpoint(a, b):
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

    def hex_corner(row, col):
        # Alternating heights form regular hexagonal cells.
        return (sqrt(3) * col, -(3 * row + (row + col) % 2))

    # The generator numbers its distance**2 data qubits first, row by row.
    positions = {}
    for p in range(distance**2):
        row, col = divmod(p, distance)
        if not hexagonal:
            positions[p] = (2 * col, -2 * row)
        elif col == 0:
            positions[p] = hex_corner(row, -1)
        elif col == distance - 1:
            positions[p] = hex_corner(row, col)
        else:
            positions[p] = midpoint(hex_corner(row, col - 1), hex_corner(row, col))

    # Locate intermediate qubits through their connections, preserving IDs.
    for p in graph:
        if p < distance**2:
            continue
        neighbors = sorted(q for q in graph[p] if q < distance**2)
        if len(neighbors) == 2:
            a, b = neighbors
            row, col = divmod(a, distance)
            if hexagonal and b // distance == row:
                positions[p] = hex_corner(row, col)
            else:
                positions[p] = midpoint(positions[a], positions[b])

    # Remaining degree-two qubits bridge the positioned rows.
    for p in graph:
        if p not in positions:
            a, b = graph[p]
            positions[p] = midpoint(positions[a], positions[b])
    return positions


def _physical_figure_size(positions):
    """Leave room for node labels without distorting the lattice geometry."""
    xs, ys = zip(*positions.values())
    return (
        max(7, 1.3 * (max(xs) - min(xs) + 2)),
        max(5, 1.3 * (max(ys) - min(ys) + 2)),
    )


def plot_parser_0(raw_input_circuit, target_specs):
    """Save and display the input circuit, target connectivity, and circuit DAG."""
    output_dir = Path(__file__).resolve().parent.parent /"visuals"/"parser"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save a PDF using Matplotlib without an external LaTeX installation.
    circuit_figure = raw_input_circuit.circuit.draw(
        output="mpl", filename=output_dir / "orig_circuit.pdf"
    )
    circuit_figure.canvas.manager.set_window_title("Input circuit")

    qubits = range(target_specs.target_dict["num_qubits"])
    positions = physical_layout(target_specs)
    connectivity_plots = [
        ("Physical connectivity", target_specs.physical_graph, output_dir / "physical_connectivity.png")
    ]
    for gate, connectivity in target_specs.gate_connect_graphs.items():
        if connectivity == "all":
            graph = nx.empty_graph(qubits, create_using=nx.MultiDiGraph)
            title = f"{gate}: supported on all qubits"
        else:
            graph = connectivity
            title = f"{gate} connectivity"
        connectivity_plots.append((title, graph, output_dir / f"gate_connectivity_{gate}.png"))

    for title, graph, filename in connectivity_plots:
        graph = graph.copy()
        graph.add_nodes_from(qubits)  # Include qubits with no connections, too.
        figure, axes = plt.subplots(
            num=title, figsize=_physical_figure_size(positions), layout="constrained"
        )
        edge_style = (
            {"arrowsize": 20, "connectionstyle": "arc3,rad=0.12"}
            if graph.is_directed() else {}
        )
        nx.draw_networkx(
            graph,
            pos=positions,
            ax=axes,
            node_color="lightblue",
            arrows=graph.is_directed(),
            node_size=1000,
            **edge_style,
        )
        axes.set_title(title)
        axes.margins(0.15)
        axes.set_aspect("equal")
        axes.set_axis_off()
        figure.savefig(filename, dpi=150)

    # Support the portable Graphviz installation in this virtual environment.
    graphviz_bin = Path(sys.prefix) / "graphviz" / "bin"
    if shutil.which("dot") is None and (graphviz_bin / "dot.exe").is_file():
        os.environ["PATH"] = str(graphviz_bin) + os.pathsep + os.environ.get("PATH", "")

    dag_image = dag_drawer(raw_input_circuit.DAG_circuit)
    dag_image.save(output_dir / "circuit_dag.png")
    dag_figure, dag_axes = plt.subplots(num="Circuit DAG", figsize=(8, 8), layout="constrained")
    dag_axes.imshow(dag_image)
    dag_axes.set_title("Circuit DAG (final measurements removed)")
    dag_axes.set_axis_off()

    # plt.show()

def plot_norm_dag(norm_dag):
    """Save and display the normalized circuit DAG."""
    output_dir = Path(__file__).resolve().parent.parent /"visuals"/"norm"
    output_dir.mkdir(parents=True, exist_ok=True)

    dag_image = dag_drawer(norm_dag)
    dag_image.save(output_dir / "normalized_circuit_dag.png")
    dag_figure, dag_axes = plt.subplots(num="Normalized Circuit DAG", figsize=(8, 8), layout="constrained")
    dag_axes.imshow(dag_image)
    dag_axes.set_title("Normalized Circuit DAG")
    dag_axes.set_axis_off()

    # plt.show()

def plot_optim_dag(norm_dag):
    """Save and display optimized circuit DAG."""
    output_dir = Path(__file__).resolve().parent.parent /"visuals"/"optim"
    output_dir.mkdir(parents=True, exist_ok=True)

    dag_image = dag_drawer(norm_dag)
    dag_image.save(output_dir / "optimized_circuit_dag.png")
    dag_figure, dag_axes = plt.subplots(num="Optimized Circuit DAG", figsize=(8, 8), layout="constrained")
    dag_axes.imshow(dag_image)
    dag_axes.set_title("Optimized Circuit DAG")
    dag_axes.set_axis_off()

    # plt.show()


def plot_placement(mapping, target_specs):
    """Save the logical-to-physical mapping without opening plot windows.

    ``mapping`` maps logical qubit indices to physical node indices.
    Blue nodes are assigned; gray nodes are unused physical qubits.
    """
    output_dir = Path(__file__).resolve().parent.parent / "visuals" / "placement"
    output_dir.mkdir(parents=True, exist_ok=True)

    graph = target_specs.physical_graph
    physical_to_logical = {physical: logical for logical, physical in mapping.items()}
    labels = {
        physical: (
            f"p{physical}\nq{physical_to_logical[physical]}"
            if physical in physical_to_logical
            else f"p{physical}\nunused"
        )
        for physical in graph.nodes
    }
    colors = [
        "lightblue" if physical in physical_to_logical else "lightgray"
        for physical in graph.nodes
    ]

    positions = physical_layout(target_specs)
    figure, axes = plt.subplots(
        num="Initial placement", figsize=_physical_figure_size(positions),
        layout="constrained", clear=True
    )
    nx.draw_networkx(
        graph,
        pos=positions,
        ax=axes,
        labels=labels,
        node_color=colors,
        node_size=1800,
        edgecolors="dimgray",
        edge_color="gray",
        font_size=10,
    )
    axes.margins(0.15)
    # A single row/column needs space for markers beyond the wire itself.
    xs, ys = zip(*positions.values())
    if min(xs) == max(xs):
        axes.set_xlim(xs[0] - 0.5, xs[0] + 0.5)
    if min(ys) == max(ys):
        axes.set_ylim(ys[0] - 0.5, ys[0] + 0.5)
    axes.set_aspect("equal")
    axes.set_axis_off()
    figure.savefig(output_dir / "physical_mapping.png", dpi=150)

    plt.close(figure)
    return figure
