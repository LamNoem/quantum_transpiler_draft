// TEST: 12_invalid_qasm/duplicate_ccx_operand
// KIND: invalid_qasm
// PURPOSE: Semantic error: repeated qubit in one three-qubit operation.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
ccx q[0],q[1],q[1];
