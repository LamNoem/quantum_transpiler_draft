// TEST: 08_terminal_measurements/cross_register_readout
// KIND: normalize
// PURPOSE: Preserve scalar and array classical destinations across multiple quantum registers.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] data;
qubit anc;
bit[2] out;
bit flag;
ry(pi/7) data[1];
cx data[1],anc;
out[0]=measure anc;
flag=measure data[1];
