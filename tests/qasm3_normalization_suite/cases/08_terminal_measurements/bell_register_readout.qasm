// TEST: 08_terminal_measurements/bell_register_readout
// KIND: normalize
// PURPOSE: Strip terminal measurements before Norm and restore the original q-to-c mapping afterward.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

bit[2] c;
qubit[2] q;
h q[0];
cx q[0],q[1];
c = measure q;
