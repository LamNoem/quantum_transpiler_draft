// TEST: 00_basics/already_normalized_mixed
// KIND: normalize
// PURPOSE: A complete pass should be a fixed point on an internal-basis circuit.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
h q[2];
rz(-pi/7) q[2];
cx q[2],q[0];
x q[1];
cx q[0],q[1];
h q[0];
