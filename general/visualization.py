"""Drawing and display helpers for the compiler pipeline."""

import os
from pathlib import Path
import shutil
import sys

import matplotlib.pyplot as plt
import networkx as nx
from qiskit.visualization import dag_drawer


def plot_parser_0(raw_input_circuit, target_specs):
    """Save and display the input circuit, target connectivity, and circuit DAG."""
    output_dir = Path(__file__).resolve().parent.parent / "visuals"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save a PDF using Matplotlib without an external LaTeX installation.
    circuit_figure = raw_input_circuit.circuit.draw(
        output="mpl", filename=output_dir / "orig_circuit.pdf"
    )
    circuit_figure.canvas.manager.set_window_title("Input circuit")

    qubits = range(target_specs.target_dict["num_qubits"])
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
        figure, axes = plt.subplots(num=title, figsize=(6, 5), layout="constrained")
        nx.draw_networkx(
            graph,
            pos=nx.circular_layout(graph),
            ax=axes,
            node_color="lightblue",
            node_size=1000,
            arrowsize=20,
            connectionstyle="arc3,rad=0.12",
        )
        axes.set_title(title)
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

    plt.show()
