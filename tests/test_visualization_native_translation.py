"""Check stage-5 plots against real native gate translations."""

import copy
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from PIL import Image
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.converters import circuit_to_dag

from general import visualization
from native_translation_5.native_translator import ToNativeTranslator
from parser_0.input_target import NATIVE_SETS


def make_translation(circuit, native_set):
    target = SimpleNamespace(
        native_set=native_set,
        native_gates=list(NATIVE_SETS[native_set]),
        gate_arities=NATIVE_SETS[native_set],
    )
    return ToNativeTranslator(circuit_to_dag(circuit), target)


def export_translation(translator, tmp_path, monkeypatch):
    monkeypatch.setattr(visualization, "__file__", str(tmp_path / "general" / "visualization.py"))

    def unexpected_show(*args, **kwargs):
        pytest.fail("Native translation exports must not open plot windows")

    monkeypatch.setattr(plt, "show", unexpected_show)
    open_figures = plt.get_fignums()
    figures = visualization.plot_native_translation(translator)
    assert plt.get_fignums() == open_figures

    output_dir = tmp_path / "visuals" / "native_translation"
    assert {path.name for path in output_dir.iterdir()} == {
        "native_circuit.pdf", "native_circuit_dag.png",
        "gate_counts.png", "translation_history.png",
    }
    assert (output_dir / "native_circuit.pdf").read_bytes().startswith(b"%PDF-")
    for filename in ("native_circuit_dag.png", "gate_counts.png", "translation_history.png"):
        with Image.open(output_dir / filename) as image:
            assert image.format == "PNG"
            image.verify()
    return figures


@pytest.mark.parametrize(
    "native_set,expected_counts,expected_sizes,expected_native,expected_nonnative",
    [
        ("demo_cx", {"h": 1, "cx": 1, "rz": 1, "x": 1},
         [6] * 8, [4] * 8, [0] * 8),
        ("ibm_cx", {"cx": 1, "rz": 3, "sx": 1, "x": 1},
         [6] + [8] * 7, [3] + [6] * 7, [1] + [0] * 7),
        ("ibm_cz", {"cz": 1, "rz": 7, "sx": 3, "x": 1},
         [6, 8] + [14] * 6, [2, 5] + [12] * 6, [2, 1] + [0] * 6),
        ("ibm_ecr", {"ecr": 1, "rz": 4, "sx": 2, "x": 2},
         [6, 8] + [11] * 6, [2, 5] + [9] * 6, [2, 1] + [0] * 6),
    ],
)
def test_native_exports_show_gate_replacements(
    tmp_path, monkeypatch, native_set, expected_counts,
    expected_sizes, expected_native, expected_nonnative,
):
    # Nonconsecutive physical operands and symbolic phases must remain intact.
    circuit = QuantumCircuit(3, 1)
    circuit.global_phase = Parameter("phi")
    circuit.h(2)
    circuit.cx(2, 0)
    circuit.rz(Parameter("theta"), 1)
    circuit.x(0)
    circuit.barrier()
    circuit.measure(2, 0)
    translator = make_translation(circuit, native_set)
    snapshots = copy.deepcopy((translator.orig_dag, translator.native_dag, translator.translation_history))

    figures = export_translation(translator, tmp_path, monkeypatch)
    counts_axes = figures["counts"].axes[0]
    gate_names = [tick.get_text() for tick in counts_axes.get_xticklabels()]
    original_counts = {"h": 1, "cx": 1, "rz": 1, "x": 1}
    assert gate_names == sorted(set(original_counts) | set(expected_counts))
    for bars, expected in zip(counts_axes.containers, (original_counts, expected_counts)):
        assert [bar.get_height() for bar in bars] == [expected.get(name, 0) for name in gate_names]

    gates_axes, size_axes = figures["history"].axes
    np.testing.assert_array_equal(gates_axes.lines[0].get_ydata(), expected_native)
    np.testing.assert_array_equal(gates_axes.lines[1].get_ydata(), expected_nonnative)
    np.testing.assert_array_equal(size_axes.lines[0].get_ydata(), expected_sizes)
    np.testing.assert_array_equal(size_axes.lines[0].get_xdata(), range(8))
    if native_set == "demo_cx":
        assert not size_axes.collections
    else:
        replacements = [[1, 8]] if native_set == "ibm_cx" else [[1, 8], [2, expected_sizes[2]]]
        np.testing.assert_array_equal(size_axes.collections[0].get_offsets(), replacements)

    assert (translator.orig_dag, translator.native_dag, translator.translation_history) == snapshots


@pytest.mark.parametrize("directives_only", [False, True], ids=["empty", "barrier-and-measurement"])
def test_native_exports_handle_circuits_without_gates(tmp_path, monkeypatch, directives_only):
    circuit = QuantumCircuit(2, 1)
    if directives_only:
        circuit.barrier()
        circuit.measure(1, 0)
    translator = make_translation(circuit, "ibm_cz")
    figures = export_translation(translator, tmp_path, monkeypatch)

    counts_axes = figures["counts"].axes[0]
    assert not counts_axes.patches
    assert "No gates to translate" in [text.get_text() for text in counts_axes.texts]
    gates_axes, size_axes = figures["history"].axes
    expected_sizes = [2] * 4 if directives_only else [0, 0]
    np.testing.assert_array_equal(size_axes.lines[0].get_ydata(), expected_sizes)
    for line in gates_axes.lines:
        np.testing.assert_array_equal(line.get_ydata(), [0] * len(expected_sizes))
    assert not size_axes.collections
    assert translator.native_dag == circuit_to_dag(circuit)


def test_native_export_failure_closes_only_its_figures(tmp_path, monkeypatch):
    translator = make_translation(QuantumCircuit(1), "demo_cx")
    monkeypatch.setattr(visualization, "__file__", str(tmp_path / "general" / "visualization.py"))

    def failed_export(*args, **kwargs):
        raise RuntimeError("DAG export failed")

    monkeypatch.setattr(visualization, "dag_drawer", failed_export)
    existing_figure = plt.figure()
    open_figures = plt.get_fignums()
    try:
        with pytest.raises(RuntimeError, match="DAG export failed"):
            visualization.plot_native_translation(translator)
        assert plt.get_fignums() == open_figures
    finally:
        plt.close(existing_figure)
