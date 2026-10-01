// TEST: 03_symbolic/parameter_only_phase
// KIND: feature_probe
// PURPOSE: Parameter tracking includes circuit global_phase, not just gate parameters.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
qubit[1] q;
gphase(theta);
h q[0];
