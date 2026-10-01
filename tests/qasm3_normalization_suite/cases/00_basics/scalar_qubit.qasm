// TEST: 00_basics/scalar_qubit
// KIND: normalize
// PURPOSE: Scalar qubits are not qubit arrays of a presumed name.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit a;
h a;
rz(pi/7) a;
x a;
