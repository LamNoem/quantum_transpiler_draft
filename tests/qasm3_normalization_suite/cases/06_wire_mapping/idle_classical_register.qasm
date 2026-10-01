// TEST: 06_wire_mapping/idle_classical_register
// KIND: normalize
// PURPOSE: Unused classical bits should not be mistaken for qubits or lost by a DAG-only pass.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

bit[5] unused;
qubit[3] q;
ry(pi/7) q[2];
