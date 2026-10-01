// TEST: 06_wire_mapping/multiple_registers
// KIND: normalize
// PURPOSE: Different registers may both contain local index zero.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] data;
qubit[1] anc;
h data[1];
cry(pi/5) anc[0],data[0];
cz data[1],anc[0];
