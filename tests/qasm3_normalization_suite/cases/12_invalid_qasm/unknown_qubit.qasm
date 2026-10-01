// TEST: 12_invalid_qasm/unknown_qubit
// KIND: invalid_qasm
// PURPOSE: Semantic error: undeclared qubit.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
h missing[0];
