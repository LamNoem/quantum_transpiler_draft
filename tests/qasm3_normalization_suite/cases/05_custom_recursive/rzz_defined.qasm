// TEST: 05_custom_recursive/rzz_defined
// KIND: normalize
// PURPOSE: RZZ is explicitly defined here; do not assume it is supplied by stdgates.inc.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate rzz_test(t) a,b { cx a,b; rz(t) b; cx a,b; }
qubit[2] q;
rzz_test(pi/7) q[1],q[0];
