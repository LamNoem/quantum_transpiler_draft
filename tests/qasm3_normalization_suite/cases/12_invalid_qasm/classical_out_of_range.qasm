// TEST: 12_invalid_qasm/classical_out_of_range
// KIND: invalid_qasm
// PURPOSE: Semantic error: classical destination out of range.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
bit[1] c;
c[1]=measure q[0];
