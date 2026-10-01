// TEST: 10_language_features/inverse_custom
// KIND: feature_probe
// PURPOSE: Inverse of a sequence requires reversing order and inverting every constituent.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

gate custom_gate(t) a { ry(t) a; rz(t/2) a; }
qubit[1] q;
inv @ custom_gate(pi/7) q[0];
