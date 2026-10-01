// TEST: 10_language_features/custom_gate_named_rx
// KIND: feature_probe
// PURPOSE: A user-defined rx name need not mean Qiskit RXGate. Dispatch must inspect the operation type/definition.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
gate rx(t) a { U(0,0,t) a; }
qubit[1] q;
rx(pi/7) q[0];
