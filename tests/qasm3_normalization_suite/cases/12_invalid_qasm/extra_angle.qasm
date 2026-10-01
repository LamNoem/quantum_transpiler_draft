// TEST: 12_invalid_qasm/extra_angle
// KIND: invalid_qasm
// PURPOSE: Wrong parameter arity: RY has one angle.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
ry(pi/7,pi/5) q[0];
