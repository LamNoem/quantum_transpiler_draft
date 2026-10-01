// TEST: 10_language_features/custom_gate_named_h
// KIND: feature_probe
// PURPOSE: Do not mark a generic custom gate as normalized solely because its name is h.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
gate h a { U(pi,0,pi) a; }
qubit[1] q;
h q[0];
