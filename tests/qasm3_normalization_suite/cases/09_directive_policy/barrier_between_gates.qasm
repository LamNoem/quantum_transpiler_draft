// TEST: 09_directive_policy/barrier_between_gates
// KIND: feature_probe
// PURPOSE: A barrier is not a unitary gate to decompose. Decide whether to preserve or strip it before Norm.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
ry(pi/7) q[0];
barrier q;
rx(-pi/5) q[1];
