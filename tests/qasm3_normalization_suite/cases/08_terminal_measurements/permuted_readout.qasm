// TEST: 08_terminal_measurements/permuted_readout
// KIND: normalize
// PURPOSE: Keep ordered qubit/classical-bit associations instead of rebuilding c[i]=measure q[i].
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

bit[3] c;
qubit[3] q;
x q[0];
ry(pi/7) q[2];
c[2]=measure q[0];
c[0]=measure q[2];
c[1]=measure q[1];
