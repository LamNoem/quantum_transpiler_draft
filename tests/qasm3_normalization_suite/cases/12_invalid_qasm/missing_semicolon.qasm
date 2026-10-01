// TEST: 12_invalid_qasm/missing_semicolon
// KIND: invalid_qasm
// PURPOSE: Syntax error: missing operation semicolon.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
h q[0]
