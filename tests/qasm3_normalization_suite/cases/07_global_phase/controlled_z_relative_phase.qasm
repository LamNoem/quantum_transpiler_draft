// TEST: 07_global_phase/controlled_z_relative_phase
// KIND: feature_probe
// PURPOSE: Under control, a formerly global phase becomes relative. Replacing controlled-Z by controlled-RZ(pi) is wrong.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
h q[0];
h q[1];
ctrl @ z q[0],q[1];
h q[0];
