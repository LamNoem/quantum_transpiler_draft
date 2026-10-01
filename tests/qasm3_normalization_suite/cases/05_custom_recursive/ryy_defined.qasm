// TEST: 05_custom_recursive/ryy_defined
// KIND: normalize
// PURPOSE: YY interaction exercises S/SDG and nested custom definitions.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate rzz_test(t) a,b { cx a,b; rz(t) b; cx a,b; }
gate ryy_test(t) a,b { sdg a; h a; sdg b; h b; rzz_test(t) a,b; h a; s a; h b; s b; }
qubit[2] q;
ryy_test(pi/7) q[0],q[1];
