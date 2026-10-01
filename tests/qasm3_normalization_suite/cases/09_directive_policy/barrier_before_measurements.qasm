// TEST: 09_directive_policy/barrier_before_measurements
// KIND: feature_probe
// PURPOSE: Keep barrier policy separate from terminal-measurement validation.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

bit[2] c;
qubit[2] q;
ry(pi/7) q[1];
barrier q;
c=measure q;
