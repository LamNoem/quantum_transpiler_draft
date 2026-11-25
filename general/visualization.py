"""Drawing and display helpers for the compiler pipeline."""

import os
from math import sqrt
from pathlib import Path
import shutil
import sys

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import networkx as nx
import rustworkx as rx
from qiskit.converters import dag_to_circuit
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


def _configure_graphviz():
    """Find the portable Graphviz installation when it is not on PATH."""
    graphviz_bin = Path(sys.prefix) / "graphviz" / "bin"
    if shutil.which("dot") is None and (graphviz_bin / "dot.exe").is_file():
        os.environ["PATH"] = str(graphviz_bin) + os.pathsep + os.environ.get("PATH", "")


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

    _configure_graphviz()
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


def _draw_physical_mapping(mapping, graph, positions, axes):
    """Overlay logical qubits on a physical topology using its fixed geometry."""
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


def plot_placement(mapping, target_specs):
    """Save the logical-to-physical mapping without opening plot windows.

    ``mapping`` maps logical qubit indices to physical node indices.
    Blue nodes are assigned; gray nodes are unused physical qubits.
    """
    output_dir = Path(__file__).resolve().parent.parent / "visuals" / "placement"
    output_dir.mkdir(parents=True, exist_ok=True)

    positions = physical_layout(target_specs)
    figure, axes = plt.subplots(
        num="Initial placement", figsize=_physical_figure_size(positions),
        layout="constrained", clear=True
    )
    _draw_physical_mapping(mapping, target_specs.physical_graph, positions, axes)
    figure.savefig(output_dir / "physical_mapping.png", dpi=150)

    plt.close(figure)
    return figure


def plot_routing(router, target_specs):
    """Save routing results under ``visuals/routing`` without showing windows.

    Pass a completed ``Router`` and its target specification. Outputs are
    ``routed_circuit.pdf``, ``routed_circuit_dag.png``, ``physical_mapping.png``
    (initial and final placement), and ``routing_history.png`` (logical qubit
    locations and emitted operation counts after each recorded action).

    SWAP and bridge markers identify routing overhead even though the routed
    circuit contains their CX decompositions. All circuit wire indices are
    physical qubit indices; q labels in the mapping/history denote logical qubits.
    Returns a dictionary of closed Matplotlib figures for further inspection.
    """
    output_dir = Path(__file__).resolve().parent.parent / "visuals" / "routing"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {}

    # Close only figures created here, including when an export fails.
    try:
        circuit = dag_to_circuit(router.routed_circuit)
        circuit_figure = circuit.draw(output="mpl", idle_wires=True)
        figures["circuit"] = circuit_figure
        circuit_figure.suptitle("Routed circuit (wire indices are physical qubits)")
        circuit_figure.savefig(output_dir / "routed_circuit.pdf", bbox_inches="tight")

        _configure_graphviz()
        dag_image = dag_drawer(router.routed_circuit)
        dag_image.save(output_dir / "routed_circuit_dag.png")
        dag_figure, dag_axes = plt.subplots(figsize=(8, 8), layout="constrained")
        figures["dag"] = dag_figure
        dag_axes.imshow(dag_image)
        dag_axes.set_title("Routed circuit DAG (physical qubits)")
        dag_axes.set_axis_off()

        positions = physical_layout(target_specs)
        width, height = _physical_figure_size(positions)
        mapping_figure, mapping_axes = plt.subplots(
            1, 2, figsize=(2 * width, height), layout="constrained"
        )
        figures["mapping"] = mapping_figure
        for axes, mapping, title in zip(
            mapping_axes,
            (router.initial_mapping, router.mapping),
            ("Initial placement", "Final placement"),
        ):
            _draw_physical_mapping(mapping, target_specs.physical_graph, positions, axes)
            axes.set_title(title)
        mapping_figure.suptitle(
            f"Routing: {router.swap_count} SWAPs, {router.bridge_count} bridges\n"
            "p = physical qubit, q = logical qubit; gray = unused"
        )
        mapping_figure.savefig(output_dir / "physical_mapping.png", dpi=150)

        history = router.routing_history
        steps = list(range(len(history)))
        history_figure, (mapping_axes, size_axes) = plt.subplots(
            2, 1, sharex=True,
            figsize=(12, max(7, 0.4 * target_specs.num_qubits + 4)),
            layout="constrained",
        )
        figures["history"] = history_figure
        for logical in sorted(router.initial_mapping):
            mapping_axes.step(
                steps, [entry["mapping"][logical] for entry in history],
                where="post", marker=".", label=f"q{logical}",
            )
        mapping_axes.set_yticks(sorted(target_specs.physical_graph))
        mapping_axes.set_ylabel("Physical qubit")
        mapping_axes.set_title("Logical qubit locations after each routing step")
        if router.initial_mapping:
            mapping_axes.legend(title="Logical qubit", loc="upper left", bbox_to_anchor=(1, 1))
        mapping_axes.grid(alpha=0.25)

        sizes = [entry["circuit_size"] for entry in history]
        size_axes.step(
            steps, sizes, where="post", marker=".", color="steelblue",
            label="Emitted operations",
        )
        for action, color, marker, label in (
            ("swap", "darkorange", "s", "SWAP (+3 CX)"),
            ("bridge", "purple", "D", "Bridge (4 CX for 1 logical CX)"),
        ):
            indices = [i for i, entry in enumerate(history) if entry["action"] == action]
            if indices:
                size_axes.scatter(
                    indices, [sizes[i] for i in indices], color=color,
                    marker=marker, label=label, zorder=3,
                )
        size_axes.set_xlabel("Routing step (0 = initial placement)")
        size_axes.set_ylabel("Emitted operations")
        size_axes.xaxis.set_major_locator(MaxNLocator(integer=True))
        size_axes.yaxis.set_major_locator(MaxNLocator(integer=True))
        size_axes.set_xlim(-0.5, max(0.5, len(history) - 0.5))
        size_axes.set_ylim(bottom=-0.5)
        size_axes.grid(alpha=0.25)
        size_axes.legend(loc="upper left", bbox_to_anchor=(1, 1))
        history_figure.savefig(output_dir / "routing_history.png", dpi=150)
    finally:
        for figure in figures.values():
            plt.close(figure)

    return figures
