// TEST: 03_symbolic/repeated_custom_parameter
// KIND: normalize
// PURPOSE: Repeated instantiations must not mutate or reuse the first replacement with stale parameters.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
gate pair(t) a,b { ry(t) a; cx a,b; rz(-t/2) b; }
qubit[3] q;
pair(theta) q[0],q[1];
pair(theta+pi/7) q[1],q[2];
pair(-theta) q[2],q[0];
