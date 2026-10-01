// TEST: 12_invalid_qasm/undeclared_angle
// KIND: invalid_qasm
// PURPOSE: Semantic error: undeclared parameter theta.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
ry(theta) q[0];
