"""Exercise routing exports with real circuits, mappings, and history."""

import copy
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pytest
from PIL import Image
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag

from general import visualization
from routing_4.router import Router


@pytest.mark.parametrize(
    "physical_count,expected_locations,expected_sizes,swaps,bridges",
    [
        (1, [[0]], [0], 0, 0),  # Empty circuit: only the initial history entry.
        (2, [[0, 0, 0], [1, 1, 1]], [0, 1, 2], 0, 0),
        (3, [[0, 0, 0], [2, 2, 2]], [0, 1, 5], 0, 1),
        (4, [[0, 0, 0, 0, 0], [3, 3, 2, 1, 1]], [0, 1, 4, 7, 8], 2, 0),
    ],
    ids=["empty", "adjacent", "bridge", "swaps-into-unused-qubits"],
)
def test_routing_exports_match_physical_execution(
    tmp_path, monkeypatch, physical_count, expected_locations, expected_sizes, swaps, bridges
):
    target = SimpleNamespace(
        physical_graph=nx.path_graph(physical_count),
        num_qubits=physical_count,
        target_dict={"phys_connect": {"preset": "line"}},
    )
    circuit = QuantumCircuit(1 if physical_count == 1 else 2)
    initial_mapping = {0: 0}
    if physical_count > 1:
        circuit.h(0)
        circuit.cx(0, 1)
        initial_mapping[1] = physical_count - 1
    router = Router(circuit_to_dag(circuit), initial_mapping, target)
    original_dag = copy.deepcopy(router.routed_circuit)
    original_history = copy.deepcopy(router.routing_history)
    original_graph = target.physical_graph.copy()
    monkeypatch.setattr(visualization, "__file__", str(tmp_path / "general" / "visualization.py"))

    def unexpected_show(*args, **kwargs):
        pytest.fail("Routing exports must not open plot windows")

    monkeypatch.setattr(plt, "show", unexpected_show)
    open_figures = plt.get_fignums()
    figures = visualization.plot_routing(router, target)
    assert plt.get_fignums() == open_figures

    output_dir = tmp_path / "visuals" / "routing"
    assert {path.name for path in output_dir.iterdir()} == {
        "routed_circuit.pdf", "routed_circuit_dag.png",
        "physical_mapping.png", "routing_history.png",
    }
    assert (output_dir / "routed_circuit.pdf").read_bytes().startswith(b"%PDF-")
    for filename in ("routed_circuit_dag.png", "physical_mapping.png", "routing_history.png"):
        with Image.open(output_dir / filename) as image:
            assert image.format == "PNG"
            assert image.width > 0 and image.height > 0
            image.verify()

    # Bridge routing leaves logical locations fixed; SWAPs move into unused nodes.
    mapping_axes, size_axes = figures["history"].axes
    assert [line.get_label() for line in mapping_axes.lines] == [
        f"q{logical}" for logical in range(circuit.num_qubits)
    ]
    for line, locations in zip(mapping_axes.lines, expected_locations):
        np.testing.assert_array_equal(line.get_xdata(), range(len(expected_sizes)))
        np.testing.assert_array_equal(line.get_ydata(), locations)
    np.testing.assert_array_equal(size_axes.lines[0].get_ydata(), expected_sizes)
    markers = {collection.get_label(): collection.get_offsets() for collection in size_axes.collections}
    if swaps:
        np.testing.assert_array_equal(markers["SWAP (+3 CX)"], [[2, 4], [3, 7]])
    if bridges:
        np.testing.assert_array_equal(markers["Bridge (4 CX for 1 logical CX)"], [[2, 5]])
    assert len(markers) == bool(swaps) + bool(bridges)

    for axes, mapping in zip(figures["mapping"].axes, (initial_mapping, router.mapping)):
        inverse = {physical: logical for logical, physical in mapping.items()}
        assert {text.get_text() for text in axes.texts} == {
            f"p{physical}\nq{inverse[physical]}" if physical in inverse else f"p{physical}\nunused"
            for physical in range(physical_count)
        }
    assert router.swap_count == swaps
    assert router.bridge_count == bridges
    assert router.initial_mapping == initial_mapping
    assert router.mapping == {logical: locations[-1] for logical, locations in enumerate(expected_locations)}
    assert router.routed_circuit == original_dag
    assert router.routing_history == original_history
    assert nx.utils.graphs_equal(target.physical_graph, original_graph)


def test_routing_closes_its_figures_if_dag_export_fails(tmp_path, monkeypatch):
    router = SimpleNamespace(routed_circuit=circuit_to_dag(QuantumCircuit(1)))
    monkeypatch.setattr(visualization, "__file__", str(tmp_path / "general" / "visualization.py"))

    def failed_dag_export(*args, **kwargs):
        raise RuntimeError("DAG export failed")

    monkeypatch.setattr(visualization, "dag_drawer", failed_dag_export)
    existing_figure = plt.figure()
    open_figures = plt.get_fignums()
    try:
        with pytest.raises(RuntimeError, match="DAG export failed"):
            visualization.plot_routing(router, None)
        assert plt.get_fignums() == open_figures
    finally:
        plt.close(existing_figure)
