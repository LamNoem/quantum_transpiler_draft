// TEST: 08_terminal_measurements/custom_then_readout
// KIND: normalize
// PURPOSE: Nested normalization plus partial permuted terminal readout.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

bit[3] c;
gate f(t) a,b { ry(t) a; cz a,b; }
qubit[3] q;
f(pi/7) q[2],q[0];
c[0]=measure q[2];
c[2]=measure q[0];
