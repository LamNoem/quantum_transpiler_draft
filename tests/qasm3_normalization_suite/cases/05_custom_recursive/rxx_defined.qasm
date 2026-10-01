// TEST: 05_custom_recursive/rxx_defined
// KIND: normalize
// PURPOSE: Nested custom XX interaction with only a final internal-basis result.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate rzz_test(t) a,b { cx a,b; rz(t) b; cx a,b; }
gate rxx_test(t) a,b { h a; h b; rzz_test(t) a,b; h a; h b; }
qubit[2] q;
rxx_test(pi/7) q[0],q[1];
