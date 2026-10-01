# Findings and implementation priorities

These observations refer to the saved `norm.py` shared earlier. No Qiskit run
of that class was performed in the creation environment. Source inspection and
independent NumPy calculations are explicitly distinguished below.

## 1. Replacement recursion — observed in saved source

The saved method loops over `dag.op_nodes()` and substitutes each non-internal
node with `normalize_node(node)`. The returned replacement DAG is not itself
normalized before substitution. A name such as `recursive_normalize` does not
make the operation recursive.

**Test:** `05_custom_recursive/three_levels.qasm`.

**Implement:** recursively normalize the replacement first, or use a worklist
that processes every newly inserted non-basis operation. Check the entire final
DAG for non-basis operations. Add a decomposition-depth/work budget and a clear
error on unsupported leaves/no progress. Do not use repeated retries to silently
skip unsupported nodes.

A one-sweep result can be semantically correct yet still not normalized. That
is why the runner reports remaining gate names separately from matrix errors.

## 2. RY registration and its decomposition — source + executed matrix check

The saved function `norm_ry` is absent from `KNOWN_NORM`. Consequently a QASM
file containing `ry` does not necessarily execute that function at all; it may
fall back to the gate definition instead.

Independently, the saved function's ten operations fail to equal RY(theta),
even up to a global phase, at theta=0. Its normalized trace overlap with the
identity at theta=0 is approximately zero, rather than one. The executed
matrix checks are in `checks/math_check_results.json`.

**Tests:** `02_angles/ry_zero.qasm`, `01_single_qubit/ry_generic.qasm`,
`03_symbolic/ry_input.qasm`.

A correct replacement using your basis, in Qiskit execution order, is:

```python
from math import pi
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag

# Use this as a standalone function, or adapt it to your class/dictionary style.
def norm_ry(node):
    theta = node.op.params[0]
    qc = QuantumCircuit(1)
    qc.rz(-pi / 2, 0)
    qc.h(0)
    qc.rz(theta, 0)
    qc.h(0)
    qc.rz(pi / 2, 0)
    return circuit_to_dag(qc)
```

Register that callable under `"ry"` in your dispatch table only after checking
that the input is actually an RY gate, not an unrelated custom gate with that
name. The sequence uses theta symbolically; it does not require `float(theta)`.
The NumPy file verifies this formula on ten representative numerical angles.

## 3. Missing global phases — observed source + executed matrix checks

With the usual RZ convention:

```
P(theta) = exp(i*theta/2) RZ(theta)
Z         = exp(i*pi/2) RZ(pi)
S         = exp(i*pi/4) RZ(pi/2)
SDG       = exp(-i*pi/4) RZ(-pi/2)
T         = exp(i*pi/8) RZ(pi/4)
TDG       = exp(-i*pi/8) RZ(-pi/4)
```

The saved explicit Z/S/SDG/T/TDG replacements emit only RZ. They are physically
equivalent as standalone whole-circuit replacements, but do not preserve the
exact operator.

For exact replacement, store the correction on the replacement circuit/DAG:

```python
qc.rz(theta, 0)
qc.global_phase = theta / 2
```

When inserting replacements, verify that the total phase is propagated once,
not discarded or manually added a second time. Test this against the actual
Qiskit version used by your project rather than assuming substitution behavior.

**Tests:** the entire `07_global_phase` group and isolated S/SDG/T/TDG tests.

Global phase is unobservable for an isolated whole circuit, but a phase of an
operation becomes relative when that operation is coherently controlled.
In particular CP(theta) and CRZ(theta) are different in general. Also,
RX(2*pi) = -I, whereas controlled-RX(2*pi) is not a global phase on the full
two-qubit system. A simplistic angle modulo 2*pi rule can be wrong.

The runner's exact/physical modes make this distinction explicit instead of
labeling every phase-only loss as a wrong observable output.

## 4. Original/result aliasing — observed source

The saved constructor assigns `self.orig_dag = dag` and then normalizes that
same DAG in place. `orig_dag` therefore no longer provides an unchanged
reference for correctness testing.

**Implement:** either make the in-place API explicit and keep a separate deep
copy for tests, or preserve an actual original DAG inside the object.

**Runner coverage:** deep independent reference copies, input-mutation and
original/result-alias diagnostics, repeatability and fixed-point checks.

## 5. Explicit fallback endpoints — coverage target, not executed diagnosis

A gate's `.definition` is not a guarantee that recursively following it will
reach your chosen basis. QASM built-in U and generic phase/identity operations
are important probes. A primitive with no usable definition must have an
explicit lowering or a helpful unsupported-gate error.

**Tests:** `01_single_qubit/U_generic.qasm`, `01_single_qubit/p_generic.qasm`,
`01_single_qubit/id_only.qasm` and nested custom-gate cases.

Base any U decomposition on the actual imported operation's convention and
compare its full matrix. Do not assume identically spelled operations from
different QASM versions or external libraries have interchangeable phase
conventions.

## 6. Gate names are not always semantic identities — targeted probe

A valid file can omit stdgates.inc and define a custom gate named `h` or `rx`.
A normalizer using only `node.op.name` can either treat that gate as already
internal or apply the wrong built-in replacement.

**Tests:** `10_language_features/custom_gate_named_h.qasm`,
`10_language_features/custom_gate_named_rx.qasm`, `negative_control.qasm` and
`mixed_controls.qasm`.

**Implement:** distinguish canonical standard-gate operations from generic
custom gates, check parameters/arity, and preserve control-state semantics.
The runner checks canonical classes and positive CX control state on output.

## 7. Ordered wires and parameter bindings — coverage target

A sub-DAG has local wires. Its first wire must map to `node.qargs[0]`, not
necessarily original circuit qubit zero. Multi-register bit indices must be
resolved within the whole circuit. Do not sort control and target operands.
Do not reuse an already-mapped replacement between invocations.

**Tests:** all of `06_wire_mapping`, `03_symbolic/repeated_custom_parameter.qasm`
and the 120-instance custom-gate stress test.

Bind symbolic parameters by Parameter identity, not a guessed parameter-vector
order. Preserve symbolic expressions during normalization. A symbol may vanish
after genuine cancellation, but replacing it with a fresh unrelated symbol of
the same name should not pass silently.

## 8. Explicit non-unitary/directive policy — coverage target

Do not send measurement, reset, barrier, delay or classical-control nodes
through ordinary unitary gate-definition fallback. Validate before stripping
terminal measurements; stripping an intermediate measurement to make an
Operator constructible is a semantic change, not a test convenience.

Repeated readout, classical overwrites, terminal-per-wire versus terminal-in-
text order and barrier semantics are intentional decision probes. The user
validator/pipeline hooks are required to test your own handling of these cases.

## 9. Error paths and atomicity — additional Python fixtures suggested

OpenQASM files cannot represent every malformed in-memory Gate or DAG. Add
separate Python tests for self-referential `.definition`, wrong replacement
width, NaN/infinite parameters, a failure after some nodes were already
substituted, and exceptions inside rule functions. Decide whether a failed
in-place pass may leave its input partially modified. Never catch all exceptions
and return a circuit marked normalized.

## Suggested order

First make isolated RX/RY and phase-aware single-qubit lowerings correct. Then
make replacement recursion terminate with a verified basis postcondition.
Next check U/phase/identity endpoints, symbolic expressions and ordered wires.
Finally connect validator/readout integration tests and decide which optional
language features to support. Optimization and routing can remain separate.
