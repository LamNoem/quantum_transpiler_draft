// TEST: 08_terminal_measurements/readout_only
// KIND: normalize
// PURPOSE: A measurement-only program has an empty unitary body, not an invalid circuit.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

bit[2] c;
qubit[2] q;
c=measure q;
