"""Check hardware geometry and the saved placement overlay."""

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PathCollection
from matplotlib.colors import to_rgba
import networkx as nx
import numpy as np
import pytest
from qiskit.transpiler import CouplingMap

from general import visualization


def make_target(preset, **parameters):
    argument_names = {
        "grid": ("rows", "cols"),
        "hexagonal_lattice": ("rows", "cols"),
        "heavy_hex": ("distance",),
        "heavy_square": ("distance",),
    }.get(preset, ("num_qubits",))
    coupling = getattr(CouplingMap, f"from_{preset}")(
        *(parameters[name] for name in argument_names), bidirectional=True
    )
    graph = nx.Graph()
    graph.add_nodes_from(range(coupling.size()))
    graph.add_edges_from(coupling.get_edges())
    specification = {"preset": preset, **parameters}
    specification.pop("num_qubits", None)
    return SimpleNamespace(
        physical_graph=graph,
        num_qubits=coupling.size(),
        target_dict={"num_qubits": coupling.size(), "phys_connect": specification},
    )


@pytest.mark.parametrize("preset,parameters", [
    ("line", {"num_qubits": 1}),
    ("line", {"num_qubits": 6}),
    ("ring", {"num_qubits": 6}),
    ("full", {"num_qubits": 5}),
    ("grid", {"rows": 2, "cols": 3}),
    ("hexagonal_lattice", {"rows": 2, "cols": 3}),
    ("hexagonal_lattice", {"rows": 3, "cols": 2}),
    ("heavy_hex", {"distance": 1}),
    ("heavy_hex", {"distance": 3}),
    ("heavy_hex", {"distance": 5}),
    ("heavy_square", {"distance": 1}),
    ("heavy_square", {"distance": 3}),
])
def test_layout_preserves_physical_ids_and_graph(preset, parameters):
    target = make_target(preset, **parameters)
    original = target.physical_graph.copy()
    positions = visualization.physical_layout(target)

    assert set(positions) == set(original)
    coordinates = np.array([positions[p] for p in original])
    assert coordinates.shape == (len(original), 2)
    assert np.isfinite(coordinates).all()
    assert len(np.unique(coordinates, axis=0)) == len(original)
    assert nx.utils.graphs_equal(target.physical_graph, original)


@pytest.mark.parametrize("rows,cols", [(2, 3), (3, 2), (1, 4), (1, 1)])
def test_grid_edges_follow_rows_and_columns(rows, cols):
    target = make_target("grid", rows=rows, cols=cols)
    positions = visualization.physical_layout(target)

    assert len({xy[0] for xy in positions.values()}) == cols
    assert len({xy[1] for xy in positions.values()}) == rows
    for a, b in target.physical_graph.edges:
        delta = np.abs(np.array(positions[a]) - positions[b])
        np.testing.assert_allclose(sorted(delta), [0, 1])


def test_line_is_straight_in_physical_qubit_order():
    positions = visualization.physical_layout(make_target("line", num_qubits=6))
    coordinates = np.array([positions[p] for p in range(6)])
    np.testing.assert_allclose(np.diff(coordinates, axis=0), [[1, 0]] * 5)


@pytest.mark.parametrize("rows,cols", [(1, 1), (2, 3), (3, 2)])
def test_hex_lattice_has_equal_length_edges(rows, cols):
    target = make_target("hexagonal_lattice", rows=rows, cols=cols)
    positions = visualization.physical_layout(target)
    lengths = [
        np.linalg.norm(np.array(positions[a]) - positions[b])
        for a, b in target.physical_graph.edges
    ]
    np.testing.assert_allclose(lengths, np.repeat(lengths[0], len(lengths)))
    if (rows, cols) == (1, 1):
        coordinates = np.array(list(positions.values()))
        radii = np.linalg.norm(coordinates - coordinates.mean(axis=0), axis=1)
        np.testing.assert_allclose(radii, np.repeat(lengths[0], len(radii)))


@pytest.mark.parametrize("distance", [3, 5])
def test_heavy_square_edges_follow_square_lattice(distance):
    target = make_target("heavy_square", distance=distance)
    positions = visualization.physical_layout(target)
    for a, b in target.physical_graph.edges:
        delta = np.abs(np.array(positions[a]) - positions[b])
        np.testing.assert_allclose(sorted(delta), [0, 1])


@pytest.mark.parametrize("distance", [3, 5])
def test_heavy_hex_edges_do_not_cross_or_pass_through_qubits(distance):
    target = make_target("heavy_hex", distance=distance)
    positions = {p: np.array(xy) for p, xy in visualization.physical_layout(target).items()}
    edges = list(target.physical_graph.edges)

    def side(a, b, p):
        edge, offset = positions[b] - positions[a], positions[p] - positions[a]
        return edge[0] * offset[1] - edge[1] * offset[0]

    for index, (a, b) in enumerate(edges):
        length = np.linalg.norm(positions[b] - positions[a])
        assert np.isclose(length, [1, 2]).any()
        for p in set(positions) - {a, b}:
            between = np.dot(positions[p] - positions[a], positions[p] - positions[b]) < -1e-9
            assert not (np.isclose(side(a, b, p), 0) and between), (a, b, p)
        for c, d in edges[index + 1:]:
            if {a, b} & {c, d}:
                continue
            crosses = side(a, b, c) * side(a, b, d) < -1e-9 and side(c, d, a) * side(c, d, b) < -1e-9
            assert not crosses, ((a, b), (c, d))


def test_placement_saves_grid_with_logical_labels_without_showing(tmp_path, monkeypatch):
    target = make_target("grid", rows=2, cols=3)
    mapping = {0: 4, 1: 1, 2: 0, 3: 3}
    monkeypatch.setattr(visualization, "__file__", str(tmp_path / "general" / "visualization.py"))

    def unexpected_show(*args, **kwargs):
        pytest.fail("Saving a placement must not open plot windows")

    monkeypatch.setattr(plt, "show", unexpected_show)
    figure = visualization.plot_placement(mapping, target)
    axes = figure.axes[0]
    nodes = next(collection for collection in axes.collections if isinstance(collection, PathCollection))

    expected_positions = visualization.physical_layout(target)
    np.testing.assert_allclose(nodes.get_offsets(), [expected_positions[p] for p in target.physical_graph])
    assert {text.get_text() for text in axes.texts} == {
        "p0\nq2", "p1\nq1", "p2\nunused", "p3\nq3", "p4\nq0", "p5\nunused"
    }
    for physical, color in zip(target.physical_graph, nodes.get_facecolors()):
        expected = "lightblue" if physical in mapping.values() else "lightgray"
        np.testing.assert_allclose(color, to_rgba(expected))

    image = tmp_path / "visuals" / "placement" / "physical_mapping.png"
    assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert not plt.fignum_exists(figure.number)
