// TEST: 08_terminal_measurements/symbolic_then_readout
// KIND: normalize
// PURPOSE: Bind symbolic parameters only for equivalence checks, not before normalization.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
bit[2] c;
qubit[2] q;
ry(theta) q[1];
cx q[1],q[0];
c=measure q;
