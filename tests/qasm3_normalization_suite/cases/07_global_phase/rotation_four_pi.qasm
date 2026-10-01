// TEST: 07_global_phase/rotation_four_pi
// KIND: normalize
// PURPOSE: RY(4*pi) is exactly I within numerical precision.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
ry(4*pi) q[0];
