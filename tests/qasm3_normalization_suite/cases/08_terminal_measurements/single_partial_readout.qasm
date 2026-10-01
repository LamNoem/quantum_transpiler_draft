// TEST: 08_terminal_measurements/single_partial_readout
// KIND: normalize
// PURPOSE: Not all qubits need to be measured, and the measured qubit is not necessarily q[0].
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[3] q;
ry(pi/7) q[2];
cx q[2],q[0];
c[0] = measure q[2];
