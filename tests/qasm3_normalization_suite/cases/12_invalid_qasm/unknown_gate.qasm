// TEST: 12_invalid_qasm/unknown_gate
// KIND: invalid_qasm
// PURPOSE: Semantic error: undefined gate.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
not_a_gate q[0];
