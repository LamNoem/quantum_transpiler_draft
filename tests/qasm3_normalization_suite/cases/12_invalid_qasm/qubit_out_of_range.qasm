// TEST: 12_invalid_qasm/qubit_out_of_range
// KIND: invalid_qasm
// PURPOSE: Semantic error: out-of-range array index.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
x q[2];
