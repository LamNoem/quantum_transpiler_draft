// TEST: 00_basics/empty_six_qubits
// KIND: normalize
// PURPOSE: Preserve all six declared idle qubits.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[6] q;
