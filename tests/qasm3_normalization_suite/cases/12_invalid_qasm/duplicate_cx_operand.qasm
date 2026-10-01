// TEST: 12_invalid_qasm/duplicate_cx_operand
// KIND: invalid_qasm
// PURPOSE: Semantic error: a controlled two-qubit gate cannot use the same qubit twice.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
cx q[0],q[0];
